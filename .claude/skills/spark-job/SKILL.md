---
name: spark-job
description: House rules for writing or changing a batch PySpark script in ShopInsight — load_bronze, batch_silver, batch_warehouse, batch_gold, gen_catalog, gen_inventory, kata. Covers the standalone-script shape, the pinned toolchain and driver-memory trap, partitioning, the seven silver cleaning rules, the star build order and the two SCD2 traps.
when_to_use: Triggers on "write batch_silver.py", "change the warehouse build", "add a gold aggregate", "why is my Spark job slow/OOM", "how do I read silver", "SCD2 in Spark". Do NOT use for Structured Streaming — readStream, foreachBatch, watermarks and the replayer belong to streaming-job.
---

# Batch PySpark in this repo

`load_bronze.py`, `batch_silver.py`, `dim_user.py`, `gen_inventory.py` and the
`batch_warehouse.py` skeleton follow these rules; copy their shape.

## 1. Shape of a script

- [ ] Runs standalone: `python processing/batch_gold.py`. No CLI framework; no `--rows`
      flag on `load_bronze.py` — the sample is whatever the hash rule yields (4,767,012 rows).
- [ ] Plain top-level functions plus a `main()`. **No factories, base classes, registries
      or `abstractmethod`** (hard rule 4) — four students, 2-4 h/week, nobody has used
      Spark before, so any file must be readable in ten minutes.
- [ ] English comments, docstrings, identifiers. snake_case tables/columns/dirs. No
      notebooks for production code.
- [ ] Print the output row count at the end — that is what the owner posts to the group
      chat and what the correctness gate compares.
- [ ] Open with the same three lines as `processing/kata.py`, **before** any SparkSession:
      ```python
      REPO = Path(__file__).resolve().parents[1]
      sys.path.insert(0, str(REPO))                      # import processing.schema from any folder
      os.environ["SPARK_CONF_DIR"] = str(REPO / "conf")  # driver memory + UTC time zone
      ```
      Without the third line Spark silently runs with a 1 GB heap and the laptop's own
      time zone. Import the schema as `from processing.schema import EVENT_SCHEMA`.

## 2. The two files nothing may duplicate

| File | Holds | Rule |
|---|---|---|
| `processing/schema.py` | `EVENT_SCHEMA` | Declared in exactly **one** place. Import it; never re-declare a StructType inline. |
| `processing/source.py` | the source reader | Isolated so swapping the JSON File source for Kafka touches this file and nothing else. |

## 3. Toolchain and memory — everyone hits this

- [ ] Python 3.14.x, OpenJDK 21, `pyspark==4.1.3`. PySpark 3.5.x **segfaults** on Python
      3.14: its cloudpickle 2.x calls a `pickle._getattribute` that changed in 3.14, and
      cloudpickle serialises every UDF and RDD lambda Spark ships to a worker. (Not
      `foreachBatch` in classic `local[*]`: a py4j callback on the driver.) Never pin
      `pyspark==3.*`.
- [ ] `spark.driver.memory 6g` lives in the committed `conf/spark-defaults.conf`, read
      because `SPARK_CONF_DIR` is set **before** the SparkSession is built. On
      `SparkSession.builder.config(...)` it works only if that builder starts the JVM; with
      a JVM already running (pyspark shell, notebook, a session stopped earlier) it is
      ignored — after a `stop()` **silently**, with `getConf()` reporting `6g` over a 1 GB
      heap. No error, just an OOM later. Check the real heap, as `kata.py` does.
- [ ] `spark.executor.memory` does nothing at all in `local[*]`: the driver *is* the
      executor. Do not set it, do not tune it.
- [ ] Master is `local[*]`; no Docker for Spark, no cluster. No optimisation before the
      W41 benchmarks — tuning without numbers is guesswork.

## 4. Where data lives and how it is partitioned

| Path | Written by | Partitioned by |
|---|---|---|
| `data/bronze/` | `load_bronze.py` (the only reader of the raw CSV) | `event_date` |
| `data/silver/` | `batch_silver.py` — **exactly one writer** | `event_date`, then `event_type` |
| `data/warehouse/` | `batch_warehouse.py` | `event_date` (`fact_event`), `session_start_date` (`fact_session_funnel`), `snapshot_date` (`fact_inventory_daily`; only the Postgres copy is LIST-partitioned by `warehouse_id`) |
| `data/gold/` | `batch_gold.py` | `event_date` / `snapshot_date` per table |

Silver is partitioned by `event_type` on purpose: most queries want one event type, so
Spark skips whole directories without opening a file. That is partition pruning, one of
the presentation's worked illustrations — filter on the partition column so it shows.

`.write.mode("overwrite")` deletes the whole output directory first, including the
tracked `.gitkeep`. Every tier writer wraps the write in `try:` and restores it in
`finally:` (`mkdir(parents=True, exist_ok=True)` then `(TIER_DIR / ".gitkeep").touch()`),
as `load_bronze.py` does, or `git status` shows the skeleton deleted, even after a
failed write.

Determinism is mandatory: `data/` is gitignored and each person regenerates locally.
Sampling and synthetic generation use `pmod(hash(user_id), 100) < 7` or a fixed hash of
`product_id` — **never** `random`, `np.random`, a seed or `.sample()`.

## 5. The seven silver cleaning rules

All seven live in `clean()` in `processing/batch_silver.py`, a pure DataFrame -> DataFrame
function the streaming job imports instead of copying.

1. Drop `price <= 0`
2. Drop null `user_id`
3. Split `category_code` into `category_l1` / `category_l2` / `category_l3`
4. **Fill missing `category_l1/l2/l3` with `'unknown'`**
5. Fill missing `brand` with `'unknown'`
6. **Shift `event_time` to UTC+7 AND recompute `event_date` from the shifted time**
7. Drop null `user_session` (1 row; `fact_event` needs it NOT NULL, BR5 clusters on it)

Split with `F.get(parts, i)`, **never** `getItem(i)` or `parts[i]`: Spark 4 runs in ANSI
mode, where `getItem(2)` on a two-level code like `electronics.smartphone` stops the whole
job with `INVALID_ARRAY_INDEX`. `get()` returns NULL, which rule 4 fills.

Silver has **31** date directories (2019-11-01 .. 2019-12-01), not 30: the last seven UTC
hours of 30 Nov are 1 Dec in Vietnam. 31 in bronze means a time-zone bug; 30 in silver
means rule 6 is missing.

Rules 4 and 6 are the two that corrupt results silently:

- Rule 4: `category_l1` is half the partition key of `gmv_by_minute` and Cassandra rejects
  a null partition-key component. 32.4% of source rows have an empty `category_code`, so
  without the fill one BR1 insert in three fails and GMV understates by about a third.
- Rule 6: keeping the pre-shift `event_date` misfiles every event between 17:00 and 24:00
  UTC and skews BR1, BR2, BR6. `from_utc_timestamp` implies a matching `to_date(...)`.

`batch_silver.py` runs before any other batch job, including in W39 before the streaming
job exists — batch never waits for the stream.

## 6. Star schema build order (SYSTEM_DESIGN 5.6, forced)

1. `dim_date` (from `seed/holidays_2019.csv`, outside `data/` so git keeps it),
   `dim_event_type`, `dim_warehouse` — no dependencies
2. `dim_product` — SCD2 on `price`, from silver + `data/catalog/products.json`
3. `stg_rfm_snapshot` — R/F/M per user per snapshot date, straight from silver
4. `dim_user` — SCD2 over `stg_rfm_snapshot`
5. `fact_event`, `fact_session_funnel`, `fact_inventory_daily`
6. Write Parquet, then load Postgres from the **same DataFrames**

Step 3 breaks the cycle dim_user -> RFM -> gold -> star: RFM is a derived attribute of
the user dimension, computed on natural keys before any fact is built, so BR4's gold
reads `dim_user` and recomputes nothing.

## 7. SCD2 — two traps that have already bitten this design

- [ ] Change detection uses `IS DISTINCT FROM` (`eqNullSafe`), never `<>` or `!=`.
      `dim_product.price` is NOT NULL so the naive predicate happens to work;
      `dim_user.rfm_cell` is NULL for 88% of users at the first snapshot and
      `NULL <> NULL` is NULL, so it emits a new version every snapshot for every non-buyer.
- [ ] **Never range-join a fact to an SCD2 dimension** on
      `product_id = ... AND event_time BETWEEN valid_from AND valid_to`: measured at
      305,663,175 intermediate rows, 65x the fact table, with product `1005115` (46,499
      events x 1,642 price versions) 25% of it alone — AQE cannot split one join key.
      Assign `product_sk` in the **same window pass over silver that detects the price
      change**, so the surrogate key is already on the event row and no join happens.
- [ ] `fact_session_funnel` is recomputed and overwritten in full every run — plain
      Parquet has no UPDATE and Iceberg/Delta are out of scope. Cheap (970,797 sessions,
      one shuffle, seconds), and saying so beats pretending the rows mutate.

## 8. Reading rules for gold

- [ ] `batch_gold.py` reads the **star**, not silver: `funnel_daily` aggregates
      `fact_session_funnel`, `rfm_segments` projects `dim_user WHERE is_current`,
      `product_affinity` self-joins `fact_event` purchases by `user_session`.
- [ ] Only `load_bronze.py` turns the raw CSV into data. `kata.py` reads its first 100,000
      rows to check an install and writes nothing. Nothing else opens it.
- [ ] No banned imports (airflow, dbt, pyflink, redis, pyiceberg, delta). BR6's Cassandra
      write uses the plain `cassandra-driver`, never the banned Spark-Cassandra connector.
