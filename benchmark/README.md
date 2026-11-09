# benchmark/ - the query benchmark (T12)

`queries.sql` holds every query that is timed, one named block per
(system, query, variant). `run_benchmark.py` parses it, times every block on
PostgreSQL, DuckDB and Cassandra, and writes four files. Nothing else in the repo
reads these two files.

## How to run

Prerequisites: the Parquet star in `data/warehouse/` (`processing/batch_warehouse.py`),
the star loaded into Postgres, the Cassandra gold tables filled (`gmv_by_minute` by
the stream, `stockout_risk` by `processing/batch_gold.py`), and
`docker compose up -d --wait`. Connection settings come from
`serving/check_infra.read_env()` (`.env.example`, overridden by `.env`).

```bash
# the official run: 3 warm-up + 20 timed runs per variant, all three systems
.venv/bin/python benchmark/run_benchmark.py

# one or two systems, fewer runs, results somewhere else
.venv/bin/python benchmark/run_benchmark.py --only postgres --only duckdb --runs 5 --warmup 1 \
    --out-dir /path/to/scratch
```

| Option | Default | Meaning |
|---|---|---|
| `--runs` | 20 | timed runs per variant |
| `--warmup` | 3 | untimed runs before them |
| `--only` | all three | `postgres`, `duckdb` or `cassandra`; repeat for several |
| `--data-dir` | `REPO/data` | the directory that holds `warehouse/` |
| `--out-dir` | `REPO/benchmark/results` | where the four files go |

Run the official numbers with nothing else on the CPU: no Spark job, no stream, no
web build. Each variant, in file order: its setup statements once, the warm-up runs,
the timed runs, then one plan. A timed run is client-side wall time,
`time.perf_counter()` around execute plus fetching every row, on one connection per
system that all runs share (a fresh in-memory DuckDB connection per run of the script).

The script only reads, with one exception: `postgres.event_time_one_hour.btree`
creates the benchmark-only index `bench_fe_time_btree` (and runs `ANALYZE fact_event`).
The script drops it right after that variant, in a `finally`, and also at the start
of every Postgres run in case a crashed run left it behind. `warehouse/ddl.sql` does
not have it. After every Postgres variant the script also sends `RESET ALL`.

It ends with `BENCHMARK OK`. If a plan does not contain a block's `-- expect:` text
(or does contain an `-- expect not:` text), the forced plan did not take effect,
that variant's numbers measure something else, and the script ends with
`BENCHMARK FAILED` and exit code 1, after writing all four files.

## What each variant shows

The day is 2019-11-29 (Black Friday, Vietnam time) throughout.

| Block | What changes | What the plan must show |
|---|---|---|
| `postgres.count_one_day.pruning_on` / `pruning_off` | `SET enable_partition_pruning = off` | only `fact_event_20191129`, or every partition including `fact_event_default` |
| `postgres.event_time_one_hour.seq_scan` | bitmap, index and index-only scans off | `Seq Scan` on every day partition, no index |
| `postgres.event_time_one_hour.brin` | nothing: the default plan | `Bitmap Index Scan` on the BRIN `ix_fact_event_time_brin` (per partition: `fact_event_<day>_event_time_idx`) |
| `postgres.event_time_one_hour.btree` | benchmark B-tree on `event_time`, bitmap scans off | `Index Scan using fact_event_<day>_event_time_idx1`, no bitmap |
| `postgres.attributes_containment.gin` / `no_gin` | bitmap and index scans off | `Bitmap Index Scan on ix_dim_product_attrs`, or `Seq Scan on dim_product` |
| `postgres.revenue_by_category.days_1` / `days_7` / `days_31` | the date range: 1, 7 or all 31 days | only the partitions in the range |
| `duckdb.count_one_day.hive_pruning` / `no_pruning` | filter on `event_date` (the hive directory) or on `date_key` (a plain column) | `Scanning Files: 1/31`, or `Total Files Read: 31` |
| `duckdb.event_time_one_hour.zonemap` | nothing to choose: row-group min/max only | `Total Files Read: 31` |
| `duckdb.attributes_containment.scan` | `attributes` is a STRUCT in Parquet, so `attributes.color = ...`; no index exists | a `READ_PARQUET` scan of `dim_product` |
| `duckdb.revenue_by_category.days_1` / `days_7` / `days_31` | as in Postgres | `Scanning Files: 1/31`, `7/31`, or all 31 files |
| `cassandra.gmv_by_minute.right_key` / `wrong_key` | the whole partition key `(event_date, category_l1)`, or only `category_l1` with `ALLOW FILTERING` | trace: `Executing single-partition query`, or `Executing seq scan` |
| `cassandra.stockout_risk.right_key` / `wrong_key` | `warehouse_id = 1 LIMIT 100`, or `product_id = <id> ALLOW FILTERING` | the same two trace lines |

Notes:

- The event_time variants have no `event_date` filter, so Postgres visits every
  partition in all three; only the access path inside each partition changes. In
  `brin` and `btree` the empty `fact_event_default` may still show a Seq Scan, so the
  expect lines only forbid one on a day partition.
- `stockout_risk.warehouse_id` is an `int` (1..5) in `serving/cassandra_schema.cql`,
  so the right-key query says `warehouse_id = 1`, not `'wh1'`.
- The Cassandra wrong-key queries do not answer the same question as the right-key
  ones: `gmv_by_minute.wrong_key` returns the `'all'` rows of every day in the table,
  and `stockout_risk.wrong_key` the product in every warehouse. The `rows` column
  says how many rows came back, and the trace's `Read N live rows` how many were read.
- An empty Cassandra table is not an error: its variants record `rows = 0` and the
  script prints a WARNING.

## Output files

All four are written to `--out-dir` with the same timestamp `ts` (local time,
`YYYYMMDD_HHMMSS`).

| File | Content |
|---|---|
| `raw_<ts>.csv` | `system,query,variant,run,ms,rows` - one line per timed run (`run` is 1..`--runs`) |
| `summary_<ts>.csv` | `system,query,variant,runs,p50_ms,p95_ms,min_ms,max_ms,mean_ms,rows` - one line per variant |
| `env_<ts>.txt` | date, host, CPU count, RAM, OS and kernel, Python, duckdb, psycopg2 and cassandra-driver versions, Postgres and Cassandra server versions and Postgres settings, git commit and dirty flag (tracked files only), the exact command line, and the row counts of the tables used, taken before any timing |
| `plans_<ts>.txt` | per variant: the setup statements, the query, the plan check, and one `EXPLAIN (ANALYZE, BUFFERS)` (Postgres), `EXPLAIN ANALYZE` (DuckDB) or query trace (Cassandra) |

**p50 and p95 use the nearest-rank method**: sort the n timed values and take the one
at 1-based rank `ceil(p / 100 * n)`. There is no interpolation, so every reported
value was actually measured. With n = 20, p50 is the 10th value and p95 the 19th.
`rows` in the summary is the row count of the last timed run.

The files of a test run are not committed. Commit the official run only, on purpose,
as evidence.

## Changing a query

Edit `queries.sql`, never the script. A block is

```sql
-- name: <system>.<query>.<variant>
-- expect: <text the plan must contain>
-- expect not: <text it must not contain>
SET some_setting = off;
SELECT ...;
```

Every statement but the last is setup, run once before the warm-up runs; the last
one is the timed query. Other lines starting with `--` are comments. Statements are split on `;`, so a string literal must
not contain one. In DuckDB blocks `{warehouse}` stands for `<--data-dir>/warehouse`.
