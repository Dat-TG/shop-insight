-- docs/evidence/explain_fact_event_partition.sql
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- EXPLAIN evidence for the W39 Postgres star schema (warehouse/ddl.sql).
-- What it proves: partition pruning (a date or warehouse filter reads only its
-- own partition) and index choice (the GIN index answers @> on attributes).
--
-- In W39 the three facts and dim_product are empty, so these are planner
-- estimates, not speed: plain EXPLAIN, no ANALYZE. Once the facts are loaded,
-- rerun it with EXPLAIN ANALYZE to measure.
--
-- Run it after serving/load_star_postgres.py. The output file is generated raw
-- by this one command and is never hand-edited:
--   docker exec -i shopinsight-postgres psql -X -a -v ON_ERROR_STOP=1 -U shopinsight -d <db> < docs/evidence/explain_fact_event_partition.sql > docs/evidence/explain_output_w39.txt
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SELECT version();

-- 1. Partition pruning on fact_event for a single day (Black Friday).
--    Expected: only fact_event_20191129 appears in the plan.
EXPLAIN
SELECT count(*) FROM fact_event WHERE event_date = '2019-11-29';

-- 1b. The same for 2019-12-01, the partial last day.
--    Expected: only fact_event_20191201, not the DEFAULT partition.
EXPLAIN
SELECT count(*) FROM fact_event WHERE event_date = '2019-12-01';

-- 2. GIN index containment search on dim_product.attributes.
--    Expected: a Bitmap Index Scan using ix_dim_product_attrs. A GIN index can only
--    be read through a Bitmap Index Scan, never a plain Index Scan. seqscan is
--    turned off because the table is empty and a sequential scan of nothing
--    would win. color is an attribute key (SYSTEM_DESIGN.md 3.3); brand is a
--    column, not an attribute, so it is not the key to test.
SET enable_seqscan = off;
EXPLAIN
SELECT product_id, brand, category_l1
FROM   dim_product
WHERE  attributes @> '{"color": "space_grey"}';
RESET enable_seqscan;

SELECT indexdef FROM pg_indexes WHERE indexname = 'ix_dim_product_attrs';

-- 3. fact_session_funnel date-range scan (BR2's source table), one ISO week.
--    Expected: only fact_session_funnel_20191111 .. _20191117, no _default.
EXPLAIN
SELECT funnel_stage, count(*)
FROM   fact_session_funnel
WHERE  session_start_date BETWEEN '2019-11-11' AND '2019-11-17'
GROUP BY funnel_stage;

-- 4. fact_inventory_daily LIST-partition pruning for a single warehouse (BR6).
--    Expected: only fact_inventory_daily_wh1 in the plan.
EXPLAIN
SELECT product_id, stock_on_hand, days_to_stockout
FROM   fact_inventory_daily
WHERE  snapshot_date = '2019-11-30'
  AND  warehouse_id = 1
ORDER BY days_to_stockout;
