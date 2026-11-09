# ShopInsight — CO5173 Data Engineering

Course project for Data Engineering (CO5173, HCMUT, Semester 1 2026-2027).
Group 15 — Dat, Khang, Nguyen, Tin. Domain: eCommerce. Final deadline: ISO week 46
(9-15 Nov 2026). Every submitted file is named after Group 15.

## What this system is

Input: `2019-Nov.csv`, 67,501,979 user behaviour events (view / cart / purchase,
9.0 GB; the dataset also documents `remove_from_cart`, but this file has none), sampled
by a deterministic 7% user hash to 4,767,012 rows. Hard rule 5 caps that working set,
not the file.
Output: a web dashboard with 8 screens, each answering one business question in
under 2 seconds.

The value of the project sits in between: turn raw logs into a dimensional
warehouse and then into pre-aggregated tables, and lay out the keys so every query
reads only the slice it needs. That gap must be **measured and proven**, not asserted.

The pipeline is bronze -> silver -> **star schema** -> gold. The star schema (five
conformed dimensions, three facts, one per Kimball fact type) is materialised twice:
Parquet as primary, PostgreSQL as a second physical realisation of the same logical
model. Gold is derived from the star, not from silver. The exception is the streaming
path: BR1, BR3, BR5 and BR8 still read silver-shaped events, because a micro-batch
cannot range-join a Type 2 dimension rebuilt nightly. All batch BRs (BR2, BR4, BR6,
BR7) read the star; of the five Cassandra tables, only BR6's `stockout_risk` is
star-derived. `SYSTEM_DESIGN.md` section 1 says why.

Full design: `SYSTEM_DESIGN.md`. Schedule and gates: `PLAN.md` (Vietnamese,
internal only — you rarely need it).

## Stack — locked, do not change

| Layer | Technology |
|---|---|
| Processing | PySpark local mode (`local[*]`), Structured Streaming + Spark SQL |
| Hot storage | Cassandra, single node, Docker |
| Analytical storage | Parquet on local filesystem |
| Ingestion | File source (JSON directory). Kafka only at W44, behind a gate |
| Comparison baselines | PostgreSQL (Docker) + DuckDB |
| API | FastAPI |
| Web | React + TypeScript |

## Hard rules

1. **Do not add technologies.** No Airflow, no dbt, no Flink, no Iceberg or Delta,
   no Redis, no Docker for Spark. The team has 2-4 hours per person per week and
   nobody has used Spark before. Every new technology costs a week we do not have.
2. **Do not use the Spark-Cassandra connector.** Write to Cassandra through
   `foreachBatch` plus the plain Python `cassandra-driver`. This sidesteps Scala
   and Spark jar version matching entirely.
3. **Do not optimise before there are numbers.** Benchmarks run in W41. Any tuning
   before that is guesswork.
4. **Do not build abstractions.** No factories, no base classes, no plugin
   registries. Four students must be able to read any file and understand it in ten
   minutes. Plain functions and runnable scripts are enough.
5. **Dataset caps at 5 million rows.** More only makes every experiment loop ten
   times slower without changing a single conclusion.
6. **Work in vertical slices.** One BR means one Spark query plus one API endpoint
   plus one React screen, finished, before starting the next BR. Never work
   horizontally (all queries first, then all endpoints).
7. **Priority when trading off:** 8 working BRs > clean code > performance. Grading
   counts successfully demonstrated BRs, roughly one point each within an 8/10
   criterion.

## Code conventions

- Python 3.14.x, `pyspark==4.1.3`, OpenJDK 21 — pinned exactly, not minimums. PySpark
  3.5.x **segfaults** on 3.14 and 3.11-3.13 are not in the Ubuntu 26.04 repos.
  `SYSTEM_DESIGN.md` section 11.1 says why each pin is load-bearing
- virtualenv at `.venv/`, dependencies pinned in `requirements.txt`
- Every script runs standalone: `python processing/batch_gold.py`
- The event schema is declared in exactly one place: `processing/schema.py`
- The source reader is isolated in `processing/source.py` — swapping File source for
  Kafka touches only this file
- snake_case English for tables, columns and directories
- Comments, docstrings and commit messages in English
- No notebooks for production code: hard to review, hard to rerun

## Eight business requirements

The course requires at least 2n requirements where n is the team size, so 8. Each
one must be demonstrable.

| BR | What it answers | Layer | Sink |
|---|---|---|---|
| BR1 | GMV and order count per minute, split by category | streaming | Cassandra |
| BR2 | Conversion funnel view -> cart -> purchase, per session | batch | Parquet |
| BR3 | Top-N trending products, 15-minute sliding window | streaming | Cassandra |
| BR4 | RFM customer segmentation | batch | Parquet |
| BR5 | Abandoned cart detection | streaming | Cassandra |
| BR6 | Stock-out risk per SKU and warehouse | batch | Cassandra |
| BR7 | Frequently bought together, from a co-occurrence matrix | batch | Parquet |
| BR8 | Order velocity anomaly detection | streaming | Cassandra |
| BR9 | (bonus, **cut** in `PLAN.md`) Ad-hoc product lookup with combined filters | batch | Parquet |

BR6 is batch only, even though it sinks to Cassandra.

Each BR has one owner who writes all three layers of it — Spark query, API endpoint,
React screen. Dat owns BR2 and BR1; Khang BR4 and BR3; Nguyen BR7 and BR5; Tin BR6
and BR8. BR9 was cut to pay for the warehouse layer. Which week each BR lands in
lives only in `PLAN.md`, the schedule of record — it moved once already.
Everyone writes Spark; that is deliberate.

The three streaming BRs that are not Dat's all sit in W41 — one week after Dat builds
the streaming foundation in W40 — so nobody waits on anybody inside a week.

## Details that are easy to get wrong

- Structured Streaming **cannot infer schema**. Pass `EVENT_SCHEMA` explicitly to
  `readStream`.
- Without `checkpointLocation` all state is lost on restart.
- The streaming job must start **before** the replayer. Start it after and the
  files already sitting in the landing directory collapse into one huge
  micro-batch, which looks nothing like real time during a demo.
- Cassandra cannot filter arbitrarily. Every query goes through the partition key,
  so design keys backwards from the question the screen will ask.
- Structured Streaming cannot rank a streaming DataFrame. BR3's top-N is computed
  inside `foreachBatch`, not with a window function on the stream.
- Three Cassandra tables leave stale rows, and the fix differs for each. Getting this
  wrong shows up on screen as duplicates, or as a list that empties itself mid-demo.
  `stockout_risk` is batch and rewrites every warehouse in full, so delete the
  partition (`WHERE warehouse_id = ?`) then insert. `trending_products` re-emits each
  window, so delete `WHERE window_start = ?` then insert the new top-N. But
  `abandoned_carts` is streaming and accumulates through the day: deleting its
  partition would erase every cart found in earlier micro-batches. Its key is
  therefore `((event_date), user_session)` with `cart_value` as a plain column, which
  makes the upsert idempotent and needs no delete at all.
- Silver has exactly one writer: `processing/batch_silver.py`, from bronze. The
  streaming job does **not** write silver — its only outputs are the Cassandra gold
  tables. A Parquet file sink there would create `data/silver/_spark_metadata/` and make
  Spark blind to the files `batch_silver.py` wrote while DuckDB still globs the whole
  directory; a `foreachBatch` write would duplicate rows, because the replayer replays
  bronze that silver already contains. `SYSTEM_DESIGN.md` section 8 has both arguments.
- `data/` is gitignored, so no data ever moves between machines. Each person downloads
  the raw CSV themselves and runs `load_bronze.py` + `batch_silver.py` locally. The
  sampling rule must be deterministic — `pmod(hash(user_id), 100) < 7`, never a
  random seed — so all four machines produce byte-identical datasets.
- `batch_silver.py` shifts `event_time` to UTC+7, so it must also RECOMPUTE
  `event_date` from the shifted time. Keeping the old date misfiles every event
  between 17:00 and 24:00 UTC and skews BR1, BR2 and BR6.
- Every screen displays its query time and how many partitions were read. This is
  live evidence for the evaluation section of the report.

## Current status

The Spark setup exists: `docs/SETUP_SPARK.md` (English) and `docs/SPARK_GUIDE_VI.md`
(Vietnamese, explains every step and file; keep the two in step), `requirements.txt`,
`conf/spark-defaults.conf`, `processing/schema.py` and `processing/kata.py`. So does
bronze: `ingestion/load_bronze.py` (4,767,012 rows, 30 date directories), and silver:
`processing/batch_silver.py` (4,754,015 rows, 31 Vietnam-time date directories, seven
cleaning rules in `clean()`, which the streaming job imports). So does the
infrastructure: `docker-compose.yml` (cassandra:4.1.12 + postgres:16.15, pinned to the
patch), `.env.example` and `serving/check_infra.py` (prints `INFRA OK`); the Docker
install is `docs/SETUP_SPARK.md` step 9. The warehouse layer: the Postgres star DDL
`warehouse/ddl.sql` and its loader `serving/load_star_postgres.py` (the three small
dimensions when run on its own, every star table when step 6 calls it);
`processing/batch_warehouse.py`, the 5.6 build order, which imports
`processing/dim_product.py` (`dim_product` SCD2 + `product_sk`) and `processing/dim_user.py`
(`stg_rfm_snapshot` + `dim_user` SCD2 + `user_sk`) and builds all nine tables: `dim_date`,
`dim_event_type`, `dim_warehouse`, `dim_product`, `stg_rfm_snapshot`, `dim_user`,
`fact_event` (4,754,015 rows, 31 date directories), `fact_session_funnel` (970,797 rows,
one per silver `user_session`, checked against `ck_fsf_stage` and `ck_fsf_lags`) and
`fact_inventory_daily` (1,909,650 rows: 12,731 purchased SKUs x 5 warehouses x 30 days,
dense). Step 6 then loads them into Postgres when it is up, and the script prints
`WAREHOUSE OK`. Inputs and checks: `ingestion/gen_catalog.py` and
`ingestion/gen_inventory.py` (both run before batch_warehouse), `checks/scd2_integrity.py`,
`checks/fact_event_spot.py`. Cassandra: `serving/cassandra_schema.cql` +
`serving/apply_schema.py`. The streaming foundation: `ingestion/replayer.py` (bronze ->
`data/stream_landing/`, one JSON file every 5 s), `processing/source.py` (the only
source reader) and `processing/streaming_gold.py`, where BR1 writes `gmv_by_minute`
(plus a `category_l1 = 'all'` total row per window), BR3 writes the top 20 of each
15-minute window to `trending_products`, BR5 writes one row per session that carted and
did not buy within a 30-minute `session_window` to `abandoned_carts` (upsert, no delete),
and BR8 writes one row per 5-minute window and user with a purchase to
`order_velocity_alerts`, labelled low / medium / high at 1 / 2-3 / >= 4 orders
(API_CONTRACT section 10; upsert, no delete). `docs/STREAMING_PATTERN.md` walks through it
block by block, and `docs/SPARK_GUIDE_VI.md` Phần 10 is its Vietnamese twin (keep the
two in step). All eight BRs are live end to end: `GET /api/br1/realtime`,
`GET /api/br3/trending`, `GET /api/br5/carts`, `GET /api/br6/stockout` (one query per
warehouse partition, at most 100 rows each) and `GET /api/br8/alerts` read Cassandra
through `serving/api/cassandra.py` (the one session every Cassandra router imports), and
the BR1, BR3, BR5 and BR8 screens refresh every 10 s;
`processing/batch_gold.py` writes BR6's `stockout_risk` from the last day of
`fact_inventory_daily` (delete each warehouse partition, then insert, 9999.0 for a NULL
`days_to_stockout`), projects BR4's `rfm_segments` from `dim_user` and aggregates
BR2's `funnel_daily` (465 rows: session start date x 14 categories + `'all'`) from
`fact_session_funnel`, the category rows through `fact_event` and `dim_product` on
`product_sk`, and `GET /api/br4/segments` and
`GET /api/br2/funnel` read them with DuckDB; `processing/gold_br7.py` builds BR7's
`product_affinity`, which `GET /api/br7/affinity` reads with DuckDB. The
project runs W38-W46 (14 Sep - 15 Nov). W38 is a combined week: kickoff and
infrastructure together.

The team works asynchronously — everyone has a job and other classes. Only two
moments in the whole project need all four people at once: the 45-minute rehearsal
in W43 and the in-class talk in W44. Everything else is handed over through the
repo. So: write the setup down instead of explaining it, comment the reference
implementation instead of walking someone through it, and make every gate produce
an artefact someone can look at on their own time.

Next task: Gate 2b (W42, code freeze): every screen measured under 2 s through its
QueryMeta footer. Gate 2a (all 8 BRs demonstrable) is met in code since #23. Its evidence
is `docs/evidence/gate2a_br2_run.txt` and `docs/evidence/gate2a_br5_run.txt`, and Tin still
owes `gate2a_br6_run.txt` and `gate2a_br8_run.txt`. One team decision is closed: BR8's
screen expands an alert to its 5-minute window totals (`order_velocity_alerts` stores no
orders), recorded in `docs/BR_SCOPE.md`, `docs/REPORT.md` section 2.8 and `SYSTEM_DESIGN.md`
section 9 (sprint task T04, 10 Nov).
