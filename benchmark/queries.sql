-- benchmark/queries.sql - every query that benchmark/run_benchmark.py times (T12).
--
-- Format, read by parse_queries() in run_benchmark.py:
--   -- name: <system>.<query>.<variant>   starts a block; system is postgres, duckdb or cassandra
--   -- expect: <text>                     the plan (Cassandra: the query trace) must contain this text
--   -- expect not: <text>                 the plan must NOT contain this text
--   any other line starting with --       a comment, ignored
--   the rest                              SQL statements, each ending in ;
-- The LAST statement of a block is the timed query. The statements before it
-- are the variant's session setup (SET enable_* and the like): they run once,
-- before the warm-up runs, on the same connection. After every Postgres
-- variant the runner sends RESET ALL and DROP INDEX IF EXISTS
-- bench_fe_time_btree, so no setting or benchmark index leaks into the next one.
-- No ; inside a string literal: the parser splits on it.
--
-- {warehouse} in a DuckDB block is replaced by <--data-dir>/warehouse.
-- The Postgres star is warehouse/ddl.sql; the Parquet star is data/warehouse/
-- from processing/batch_warehouse.py; the Cassandra tables are
-- serving/cassandra_schema.cql.
--
-- The day is 2019-11-29 (Black Friday, Vietnam time) throughout, as in
-- docs/evidence/explain_fact_event_partition.sql and duckdb_zonemap.txt.
-- event_type_key 3 is 'purchase' in dim_event_type (is_conversion = true).


-- =====================================================================
-- PostgreSQL 16 - the star in Postgres
-- =====================================================================

-- a) One day of fact_event. pruning_on reads only fact_event_20191129;
--    pruning_off makes the planner open every partition (32 with DEFAULT).

-- name: postgres.count_one_day.pruning_on
-- expect: fact_event_20191129
-- expect not: fact_event_20191128
SELECT count(*) FROM fact_event WHERE event_date = '2019-11-29';

-- name: postgres.count_one_day.pruning_off
-- expect: fact_event_20191128
-- expect: fact_event_default
SET enable_partition_pruning = off;
SELECT count(*) FROM fact_event WHERE event_date = '2019-11-29';

-- b) One hour by event_time. There is no event_date filter, so every
--    partition is visited; what changes is how each one is read.
--    seq_scan: no index may be used.
--    brin: the default plan, using ix_fact_event_time_brin (each partition's
--          copy is named fact_event_<yyyymmdd>_event_time_idx). It must run
--          before the btree variant, while no B-tree on event_time exists.
--    btree: a benchmark-only B-tree, created here and dropped by the runner
--          right after this variant (and at the start of every Postgres run,
--          in case a crashed run left it behind). warehouse/ddl.sql does not
--          have it. Bitmap scans are off so the B-tree is read with a plain
--          Index Scan and the BRIN, which can only be read through a bitmap,
--          cannot be picked.
--    In brin and btree the empty DEFAULT partition may still show a Seq Scan
--    (nothing to index); the expect lines only forbid one on a day partition.

-- name: postgres.event_time_one_hour.seq_scan
-- expect: Seq Scan on fact_event_20191129
-- expect not: Index
SET enable_bitmapscan = off;
SET enable_indexscan = off;
SET enable_indexonlyscan = off;
SELECT count(*), sum(price) FROM fact_event
WHERE event_time >= '2019-11-29 12:00' AND event_time < '2019-11-29 13:00';

-- name: postgres.event_time_one_hour.brin
-- expect: Bitmap Index Scan on fact_event_20191129_event_time_idx
-- expect not: Seq Scan on fact_event_2019
SELECT count(*), sum(price) FROM fact_event
WHERE event_time >= '2019-11-29 12:00' AND event_time < '2019-11-29 13:00';

-- name: postgres.event_time_one_hour.btree
-- expect: Index Scan using fact_event_20191129_event_time_idx1
-- expect not: Bitmap
-- expect not: Seq Scan on fact_event_2019
DROP INDEX IF EXISTS bench_fe_time_btree;
CREATE INDEX bench_fe_time_btree ON fact_event (event_time);
ANALYZE fact_event;
SET enable_bitmapscan = off;
SELECT count(*), sum(price) FROM fact_event
WHERE event_time >= '2019-11-29 12:00' AND event_time < '2019-11-29 13:00';

-- c) JSONB containment on dim_product.attributes. space_grey is a real
--    color (21,489 rows of dim_product when T12 was written). A GIN index
--    can only be read through a Bitmap Index Scan, so turning bitmap scans
--    off is enough to force the Seq Scan; index scans go off too for clarity.

-- name: postgres.attributes_containment.gin
-- expect: Bitmap Index Scan on ix_dim_product_attrs
SELECT count(*) FROM dim_product WHERE attributes @> '{"color": "space_grey"}';

-- name: postgres.attributes_containment.no_gin
-- expect: Seq Scan on dim_product
-- expect not: ix_dim_product_attrs
SET enable_bitmapscan = off;
SET enable_indexscan = off;
SELECT count(*) FROM dim_product WHERE attributes @> '{"color": "space_grey"}';

-- d) The data-growth query: revenue per category, fact_event x dim_product
--    on product_sk, purchases only, over 1, 7 and 31 days (all of them).

-- name: postgres.revenue_by_category.days_1
-- expect: fact_event_20191129
-- expect not: fact_event_20191128
SELECT p.category_l1, sum(f.price) AS revenue, count(*) AS orders
FROM   fact_event f
JOIN   dim_product p ON p.product_sk = f.product_sk
WHERE  f.event_type_key = 3
  AND  f.event_date = '2019-11-29'
GROUP  BY p.category_l1
ORDER  BY revenue DESC;

-- name: postgres.revenue_by_category.days_7
-- expect: fact_event_20191123
-- expect not: fact_event_20191122
SELECT p.category_l1, sum(f.price) AS revenue, count(*) AS orders
FROM   fact_event f
JOIN   dim_product p ON p.product_sk = f.product_sk
WHERE  f.event_type_key = 3
  AND  f.event_date BETWEEN '2019-11-23' AND '2019-11-29'
GROUP  BY p.category_l1
ORDER  BY revenue DESC;

-- name: postgres.revenue_by_category.days_31
-- expect: fact_event_20191101
-- expect: fact_event_20191201
SELECT p.category_l1, sum(f.price) AS revenue, count(*) AS orders
FROM   fact_event f
JOIN   dim_product p ON p.product_sk = f.product_sk
WHERE  f.event_type_key = 3
GROUP  BY p.category_l1
ORDER  BY revenue DESC;


-- =====================================================================
-- DuckDB 1.5.5, in process, on the Parquet star (data/warehouse/)
-- fact_event is hive-partitioned: one event_date=<day>/ directory per day.
-- =====================================================================

-- a) One day. hive_pruning filters on the partition column, so DuckDB opens
--    one directory. no_pruning asks the same question through date_key,
--    a plain column: every file is opened and only min/max statistics help.

-- name: duckdb.count_one_day.hive_pruning
-- expect: Scanning Files: 1/31
-- expect: Total Files Read: 1
SELECT count(*)
FROM read_parquet('{warehouse}/fact_event/event_date=*/*.parquet', hive_partitioning = true)
WHERE event_date = DATE '2019-11-29';

-- name: duckdb.count_one_day.no_pruning
-- expect: Total Files Read: 31
-- expect not: Scanning Files
SELECT count(*)
FROM read_parquet('{warehouse}/fact_event/event_date=*/*.parquet', hive_partitioning = true)
WHERE date_key = 20191129;

-- b) One hour by event_time, the same filter as Postgres. No partition
--    column in the filter, so all files are opened and row groups are
--    skipped by their event_time min/max (docs/evidence/duckdb_zonemap.txt).

-- name: duckdb.event_time_one_hour.zonemap
-- expect: Total Files Read: 31
SELECT count(*), sum(price)
FROM read_parquet('{warehouse}/fact_event/event_date=*/*.parquet', hive_partitioning = true)
WHERE event_time >= TIMESTAMP '2019-11-29 12:00:00'
  AND event_time <  TIMESTAMP '2019-11-29 13:00:00';

-- c) In Parquet, attributes is a STRUCT (Spark wrote the JSON as nested
--    columns), so the containment test is a plain field comparison and
--    there is no index: a scan of dim_product.

-- name: duckdb.attributes_containment.scan
-- expect: READ_PARQUET
SELECT count(*)
FROM read_parquet('{warehouse}/dim_product/*.parquet')
WHERE attributes.color = 'space_grey';

-- d) The data-growth query, as in Postgres. "Scanning Files: k/31" is the
--    hive pruning of fact_event; dim_product's scan is one more file.

-- name: duckdb.revenue_by_category.days_1
-- expect: Scanning Files: 1/31
SELECT p.category_l1, sum(f.price) AS revenue, count(*) AS orders
FROM   read_parquet('{warehouse}/fact_event/event_date=*/*.parquet', hive_partitioning = true) f
JOIN   read_parquet('{warehouse}/dim_product/*.parquet') p ON p.product_sk = f.product_sk
WHERE  f.event_type_key = 3
  AND  f.event_date = DATE '2019-11-29'
GROUP  BY p.category_l1
ORDER  BY revenue DESC;

-- name: duckdb.revenue_by_category.days_7
-- expect: Scanning Files: 7/31
-- expect: Total Files Read: 7
SELECT p.category_l1, sum(f.price) AS revenue, count(*) AS orders
FROM   read_parquet('{warehouse}/fact_event/event_date=*/*.parquet', hive_partitioning = true) f
JOIN   read_parquet('{warehouse}/dim_product/*.parquet') p ON p.product_sk = f.product_sk
WHERE  f.event_type_key = 3
  AND  f.event_date BETWEEN DATE '2019-11-23' AND DATE '2019-11-29'
GROUP  BY p.category_l1
ORDER  BY revenue DESC;

-- name: duckdb.revenue_by_category.days_31
-- expect: Total Files Read: 31
SELECT p.category_l1, sum(f.price) AS revenue, count(*) AS orders
FROM   read_parquet('{warehouse}/fact_event/event_date=*/*.parquet', hive_partitioning = true) f
JOIN   read_parquet('{warehouse}/dim_product/*.parquet') p ON p.product_sk = f.product_sk
WHERE  f.event_type_key = 3
GROUP  BY p.category_l1
ORDER  BY revenue DESC;


-- =====================================================================
-- Cassandra 4.1, keyspace shopinsight (serving/cassandra_schema.cql)
-- right_key goes through the whole partition key; wrong_key does not, so
-- Cassandra needs ALLOW FILTERING and reads every partition on the node.
-- No EXPLAIN in CQL: the runner writes one query trace per variant instead,
-- and the expect lines are checked against the trace.
-- =====================================================================

-- a) BR1's table. The partition key is (event_date, category_l1);
--    wrong_key gives only half of it. It returns the 'all' rows of every
--    day in the table, not just 17 Nov: the rows column shows how many.

-- name: cassandra.gmv_by_minute.right_key
-- expect: Executing single-partition query on gmv_by_minute
SELECT window_start, gmv, order_count FROM gmv_by_minute
WHERE event_date = '2019-11-17' AND category_l1 = 'all';

-- name: cassandra.gmv_by_minute.wrong_key
-- expect: Executing seq scan
SELECT window_start, gmv, order_count FROM gmv_by_minute
WHERE category_l1 = 'all' ALLOW FILTERING;

-- b) BR6's table. The partition key is (warehouse_id), an int (1..5), as
--    the screen asks it. wrong_key looks one product up in every warehouse
--    through product_id, a clustering column behind days_to_stockout.
--    1002540 is a product in stockout_risk when T12 was written.

-- name: cassandra.stockout_risk.right_key
-- expect: Executing single-partition query on stockout_risk
SELECT product_id, days_to_stockout, stock_on_hand, velocity_7d FROM stockout_risk
WHERE warehouse_id = 1 LIMIT 100;

-- name: cassandra.stockout_risk.wrong_key
-- expect: Executing seq scan
SELECT product_id, days_to_stockout, stock_on_hand, velocity_7d FROM stockout_risk
WHERE product_id = 1002540 ALLOW FILTERING;
