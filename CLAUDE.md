# ShopInsight — CO5173 Data Engineering

Course project for Data Engineering (CO5173, HCMUT, Semester 1 2026-2027).
Group 15 — Dat, Khang, Nguyen, Tin. Domain: eCommerce. Final deadline: ISO week 46
(9-15 Nov 2026). Every submitted file is named after Group 15.

## What this system is

Input: one 5-million-row CSV of user behaviour events (view / cart / purchase).
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
cannot range-join a Type 2 dimension rebuilt nightly. Only BR6 is genuinely
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

- Python 3.11+, virtualenv at `.venv/`, dependencies pinned in `requirements.txt`
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
| BR9 | (bonus) Ad-hoc product lookup with combined filters | batch | Parquet |

BR6 is batch only, even though it sinks to Cassandra.

Each BR has one owner who writes all three layers of it — Spark query, API endpoint,
React screen. Dat owns BR2 (W39) and BR1 (W40); Khang BR4 (W39) and BR3 (W41);
Nguyen BR7 (W39) and BR5 (W41); Tin BR6 (W40), BR8 (W41) and BR9 (W45).
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
- Silver is produced by `processing/batch_silver.py` from bronze. The streaming job
  also appends to it, but batch jobs must not wait for the stream to exist.
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

No code yet. The project runs W38-W46 (14 Sep - 15 Nov). W38 is a combined week:
kickoff and infrastructure together.

The team works asynchronously — everyone has a job and other classes. Only two
moments in the whole project need all four people at once: the 45-minute rehearsal
in W43 and the in-class talk in W44. Everything else is handed over through the
repo. So: write the setup down instead of explaining it, comment the reference
implementation instead of walking someone through it, and make every gate produce
an artefact someone can look at on their own time.

First task: `docs/SETUP_SPARK.md` + `processing/kata.py` so all four can install
Spark unattended, then bronze and silver so the batch BRs have input.
