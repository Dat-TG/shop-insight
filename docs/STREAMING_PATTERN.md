# Streaming pattern: BR1, block by block

BR1 is the reference streaming job. BR3 (Khang), BR5 (Nguyen) and BR8 (Tin) copy its shape
in W41. This page walks through `processing/streaming_gold.py` block by block, in the order
an event travels through it. At every block it says what stays the same and what you change
for your BR. Keep the file open next to this page.

The same walk-through in Vietnamese is in `docs/SPARK_GUIDE_VI.md`, "Phần 10 — Streaming: đọc
BR1 từng khối". Keep the two in step: change one, change the other in the same PR.

```
replayer.py ──JSON every 5 s──> data/stream_landing/ ──> read_events ──> clean() ──> watermark
                                                                                        │
       Cassandra <── write_batch (foreachBatch) <── groupBy(window, ...) <──────────────┘
                             │
                   data/checkpoints/<job>/
```

## Read this first: the two W41 traps

**1. Spark cannot rank a streaming DataFrame, and in update mode you don't get the whole
window either.** BR3 wants the top 20 products per 15-minute window. On the stream, you can
only aggregate: view and cart counts per `(window, product_id)`. The ranking and the cut to 20
happen inside `write_batch`, where the micro-batch is an ordinary DataFrame and `Window`,
`row_number()` and `orderBy().limit()` all work. That alone is not enough, though. BR1 uses
`outputMode("update")`, which hands `write_batch` **only the rows that changed** in this
micro-batch. A top 20 ranked from those rows silently leaves out every product whose count
did not move. BR3 must use `outputMode("append")`. It hands over each window once, complete,
when the watermark closes it.

**2. The tables clean up stale rows in different ways.** BR1's plain upsert is right for BR5
and BR8. For BR3 it is wrong. And BR5 must never grow a DELETE, however tidy one looks.

| Table | Job | Key | What `write_batch` does | Why |
|---|---|---|---|---|
| `gmv_by_minute` | BR1 | `((event_date, category_l1), window_start)` | plain upsert, no delete | The key of a window never changes, so writing it again overwrites the same row |
| `trending_products` | BR3 | `(window_start, rank)` | `DELETE FROM trending_products WHERE window_start = ?`, then insert the new top 20 | A product at rank 3 in one run and rank 5 in the next would leave two rows. `LIMIT 20` then returns it twice. The partition is one window, so deleting it first is exactly right |
| `abandoned_carts` | BR5 | `((event_date), user_session)` | plain upsert, **never delete** | It accumulates all day. `DELETE ... WHERE event_date = ?` erases every cart found by earlier micro-batches, and the screen empties itself mid-demo. `cart_value` is kept out of the key on purpose, so the same session always lands on its own row |
| `order_velocity_alerts` | BR8 | `((event_date), window_start, user_id)` | plain upsert, no delete | Same reason as BR1: the key never changes for a (window, user) |
| `stockout_risk` | BR6, batch | `((warehouse_id), days_to_stockout, product_id)` | `DELETE ... WHERE warehouse_id = ?`, then insert | Not streaming. It is listed so that all the rules sit in one place (SYSTEM_DESIGN 6.1) |

`.claude/hooks/check_python.py` warns when an insert into `trending_products` has no matching
DELETE, or when anything deletes from or truncates `abandoned_carts`. The one reset is
`--fresh`, which names the table only through `STREAMING_TABLES` and so does not trip it.

## Run it

Two terminals, **in this order**:

```bash
python processing/streaming_gold.py            # terminal 1. Wait for the two READY lines
python ingestion/replayer.py --speed 60        # terminal 2, only after READY
```

A good demo start: `--start "2019-11-17 08:00:00"`. It is UTC, 15:00 in Vietnam, on the day
with the most purchases in the sample: 13,076, against about 2,200 on an average day. That
gives about 2,000 rows per file. The default start, 00:00 UTC on 1 November, is the quietest
hour of the day: about 90 rows per file. **Avoid 15 November**: bronze has 432,575 events that
day and not one purchase, so BR1 shows GMV 0 all day.

What terminal 1 prints (measured, 17 Nov from 08:00 UTC):

```
READY: 1 of 4 jobs running (br1_gmv_by_minute), watching .../data/stream_landing
READY: now start python ingestion/replayer.py --speed 60
[br1_gmv_by_minute] batch 1: upserted 58 rows into gmv_by_minute (12 partitions) in 511 ms
[br1_gmv_by_minute] batch 1: 2,007 events after cleaning, watermark 2019-11-17 14:54:59, 1,150 ms
[br1_gmv_by_minute] batch 6: no window changed (watermark moved on)
```

Each micro-batch prints two lines. The first comes from `write_batch`: what went into
Cassandra. The second comes from Spark's progress report: how many events survived
`clean()`'s row rules, where the watermark stands, and how long the batch took. A batch with
"no window changed" runs because the watermark moved and Spark dropped the state of windows it
had closed. The partitions are the categories with an event in the batch's 5 minutes, plus
`all` (Block 4).

| Situation | Command |
|---|---|
| First run, a demo that replays a period again, or after pulling a change to a query's code | `python processing/streaming_gold.py --fresh` |
| The job stopped (Ctrl-C, crash) and should carry on | `python processing/streaming_gold.py`, **without** `--fresh` |

`--fresh` deletes `data/checkpoints/*/` and `data/stream_landing/*.json`, empties the four
tables the job writes (`gmv_by_minute`, `trending_products`, `abandoned_carts`,
`order_velocity_alerts`), and does nothing else. It never touches `stockout_risk`, which BR6's
batch job writes. Without `--fresh`, the checkpoint remembers the watermark. A replay of an
earlier period then arrives "late" and is dropped without a word: the screen just freezes.

Why empty the tables too: the screens show the newest rows of a partition. Replay 17 Nov up
to 20:54, then replay it again from 15:00 without emptying, and each category's newest rows
are still the old run's 19:55–20:54. Its chart stands still until the new replay passes them.
Measured on 30 Sep, before `--fresh` emptied the tables: `electronics` ended at 20:54 while the
replay was at 20:09. Everything in these tables comes back from the replay, and emptying one
before any query starts is a reset. It is not the mid-run delete that BR5 forbids.

A restart without `--fresh` resumes: the files it already read are not read again, and
windows that were still open keep their totals. Measured on the live Cassandra: after a
restart, batch 8 picked up where batch 7 stopped. All 3,772 rows then in `gmv_by_minute`
(17 Nov, 15:00–20:54 Vietnam time) equal the same minutes computed from silver: GMV
1,794,180.25 and 5,618 orders.

**Ctrl-C stops between two micro-batches.** The job prints
`Ctrl-C: stopping after the running micro-batch`, lets that batch finish its Cassandra write
(1–2 s with BR1 alone, at most 10), stops, and prints `stopped; the checkpoints keep the progress`. Two
`WARN ... Failed to cancel job group ... Cannot find active jobs` lines are expected: nothing
was left running to cancel. A second Ctrl-C quits at once, and the batch it cut short runs again
on restart.

This needed one line in `main()`. Starting Spark replaces Python's Ctrl-C handler with
pyspark's, which cancels every running Spark job first (`pyspark/core/context.py`). A batch
caught halfway then died inside its own write and printed a Java `StackOverflowError`.
Measured on 30 Sep, with Ctrl-C sent while a batch was running: before the fix, 1 error in 7
tries (4 of the 7 logged other errors); after it, 0 in 8, and each running batch committed
before the stop.

## The pipeline, block by block

### Block 0: the first lines of the file

```python
os.environ["SPARK_CONF_DIR"] = str(REPO / "conf")  # driver memory + UTC, before the JVM starts
os.environ["TZ"] = "UTC"
time.tzset()
```

The first three lines are the same in every Spark script. The `TZ` line is new, and it
protects all four jobs in the file. PySpark turns a Spark timestamp into a Python `datetime`
in the **laptop's** time zone, not Spark's UTC session (`TimestampType.fromInternal` calls
`datetime.fromtimestamp`). Measured on a UTC+7 laptop without the line, a timestamp Spark shows
as `2019-11-17 15:00:00` comes out of `collect()` as `22:00:00`. cassandra-driver then stores
that naive 22:00 as 22:00 UTC. The value is seven hours off, no error is raised, and it
differs between machines.

**For your BR:** nothing to change. You are in the same file.

### Block 1: read the stream (`processing/source.py`)

```python
spark.readStream.format("json").schema(EVENT_SCHEMA).option("mode", "FAILFAST").load(LANDING_DIR)
```

- `.schema(EVENT_SCHEMA)` is compulsory, because Structured Streaming cannot infer a schema.
  The schema is declared once, in `processing/schema.py`.
- No `timestampFormat`. The replayer lets Spark write the JSON, so `event_time` arrives as
  `"2019-11-01T00:00:02.000Z"` and the default parser reads it back. Measured: all 4,767,012
  bronze rows went through the JSON hop, and `exceptAll` found no difference in either
  direction.
- `FAILFAST` means a line that does not parse stops the query. The default would turn it into
  nulls, and `clean()` does not drop a null `event_time`.
- The Kafka swap (a W44 option, behind a gate) changes only this function.

**For your BR:** nothing to change. `main()` builds the stream once and passes it to your
`start_brN(events, cassandra)`.

### Block 2: clean, including the shift to UTC+7

```python
events = clean(read_events(spark)).withWatermark("event_time", WATERMARK)
```

`clean()` is **imported** from `processing/batch_silver.py`, never copied. The stream then
applies exactly silver's seven rules:

- `price > 0`
- `user_id` present
- `category_l1/l2/l3` split, with a missing level filled as `'unknown'`. Half of
  `gmv_by_minute`'s partition key is `category_l1`, and Cassandra rejects a null in the key,
  so without the fill one BR1 insert in three would fail.
- `brand` filled as `'unknown'`
- **`event_time` shifted to UTC+7 and `event_date` recomputed from the shifted time**
- `user_session` present. It is BR5's key.

Forget the shift and `gmv_by_minute` files a 17:00–24:00 UTC event under its UTC date, while
`funnel_daily` (built in batch, from `fact_session_funnel`) files it under the next day, so two screens
disagree about which day it belongs to.

Importing `clean()` does not make this job a silver writer. See trap A below.

**For your BR:** nothing to change. `events` has silver's columns: `event_time` (Vietnam time),
`event_type`, `product_id`, `category_id`, `category_code`, `category_l1/l2/l3`, `brand`,
`price`, `user_id`, `user_session`, `event_date`.

### Block 3: the watermark

```python
WATERMARK = "10 minutes"
```

The watermark tells Spark when a window can no longer change, so its state can be dropped.
Without one, the state of every window since the start stays in memory until the JVM dies.
It is set on the **shifted** `event_time`, so it is Vietnam time too: the log prints it as
wall-clock time. The replayer sends events in time order, so no event is ever 10 minutes
late. The watermark matters for memory and for append mode, not for late data.

**For your BR:** nothing to change. It is shared.

### Block 4: the windowed aggregation

```python
.groupBy(F.window("event_time", "1 minute"), "event_date", "category_l1")
.agg(
    F.sum(F.when(is_purchase, F.col("price")).otherwise(0)).alias("gmv"),
    F.count_if(is_purchase).alias("order_count"),
)
```

- BR1 keeps views and carts on purpose. The 7% sample has only about 1.5 purchases a minute
  across all categories, so if it filtered to purchases first, most minutes would be missing
  from the chart. Keeping every event gives each minute with any activity a row, with `gmv 0`
  if nothing sold (API_CONTRACT §3 allows this).
- `event_date` is in the `groupBy` only to carry the partition key through. A 1-minute window
  never crosses midnight.
- Before the `groupBy`, every event is doubled: once under its own `category_l1`, once under
  `'all'`:

  ```python
  .withColumn("category_l1", F.explode(F.array("category_l1", F.lit(ALL_CATEGORIES))))
  ```

  The screen's default filter, "All categories", then reads one partition instead of 14. The
  `all` row comes out of the same aggregation, so it is never partial. Adding the category
  rows up inside `write_batch` would be wrong without any error: update mode hands over only
  the categories that changed in this micro-batch. Measured on 150 closed minutes of 17 Nov,
  `all` equals both the sum of the 14 category rows and silver, to the cent.

**For your BR:** do **not** copy the explode. It is BR1's alone; in BR5 or BR8 it would
double every count, and in BR3 it would list every product twice.

| BR | Group by | Aggregate |
|---|---|---|
| BR3 | `F.window("event_time", "15 minutes", "1 minute")`, `product_id`. Not `brand`: 612 products have more than one brand value in silver (573 a real brand and `'unknown'`, 42 two real brands, 3 both), so they would split into two rows | `count_if` view, `count_if` cart; `brand` is the real one when any event has it (of two real ones, the alphabetically last), `category_l1` through `max()` |
| BR5 | per `user_session`. `F.session_window("event_time", "30 minutes")` is one way to say "30 minutes with nothing after the cart" | whether it had a cart, whether it had a purchase, cart value, item count, last event time |
| BR8 | `F.window("event_time", "5 minutes")`, `user_id` | purchases, their total value |

The window sizes come from SYSTEM_DESIGN §8 step 8.

### Block 5: `foreachBatch` and the Cassandra write

```python
insert = cassandra.prepare("INSERT INTO gmv_by_minute (...) VALUES (?, ?, ?, ?, ?)")

def write_batch(batch, batch_id):
    rows = batch.select(..., F.col("window.start").alias("window_start"), ...).collect()
    # one UNLOGGED BatchStatement per partition key
```

- `write_batch` runs **on the driver**, once per micro-batch. `batch` is an ordinary static
  DataFrame, so everything you know from batch Spark works here, including ranking (trap 1).
- The write uses the plain Python `cassandra-driver`. The Spark-Cassandra connector is banned
  (CLAUDE.md hard rule 2).
- There is one prepared statement, parsed once. Rows are grouped by partition key into
  UNLOGGED batches: every statement in a batch goes to the same partition, which is the only
  case where a Cassandra batch is cheap.
- `collect()` is safe because a micro-batch is small: about 50–70 rows for BR1. For BR3, cut
  to the top 20 **before** you collect.
- **Timestamps:** Cassandra stores the Vietnam wall clock, the same convention as silver.
  `cqlsh` shows `2019-11-17 15:00:00+0000` for 15:00 in Vietnam, and the API appends `+07:00`
  when it renders the value. Block 0 keeps this correct.

**For your BR:** the INSERT, your table's delete rule (trap 2), and the columns you select.

### Block 6: `writeStream`, the checkpoint and the trigger

```python
gmv_by_minute.writeStream
    .queryName("br1_gmv_by_minute")
    .outputMode("update")
    .foreachBatch(write_batch)
    .option("checkpointLocation", str(CHECKPOINT_DIR / "br1_gmv_by_minute"))
    .trigger(processingTime=TRIGGER)          # "5 seconds"
    .start()
```

- **One checkpoint directory per query**, named `br<N>_<table>`. If two queries share one,
  both break.
- `update` suits BR1 and BR8: each micro-batch re-emits the windows it changed, with the
  running total, so the screen sees the current minute grow. BR3 needs `append` (trap 1). For
  BR5, `append` fits the question: a session is abandoned only once 30 minutes have passed
  with no purchase, and only the watermark can say that.
- The trigger checks for new files every 5 seconds. That is the replayer's cadence, so there
  is about one file per micro-batch.

**For your BR:** `queryName`, the checkpoint name, and `outputMode`.

### Block 7: `main()`

`main()` connects to Cassandra first (a missing container fails in one second, not after the
JVM's ten). It builds `events` once, calls the four `start_brN` functions, and starts every
query that is not `None`. It then waits until each query has read whatever was already there,
prints READY, and prints one progress line per micro-batch until Ctrl-C. On Ctrl-C,
`stop_between_batches()` lets each query finish its running batch before stopping it.

**For your BR:** replace the stub's body and return the `StreamingQuery`. `main()` picks it up
with no other edit.

## Traps you will not see coming

**A. The stream never writes `data/silver/`.** Silver has one writer, `batch_silver.py`. A
Parquet file sink would create `data/silver/_spark_metadata/`, after which Spark reads only the
files listed there, so everything the batch wrote goes invisible to Spark (DuckDB still sees
it). A `foreachBatch` write would duplicate rows, because the replayer replays bronze that
silver already holds. BR2, BR4 and BR7 would then count everything twice. The only outputs are
Cassandra tables.

**B. Shuffle partitions are fixed in the checkpoint.** `spark.sql.shuffle.partitions` is 4 in
this job, not Spark's 200. Measured, with BR1 alone on 20 cores: at 200, every micro-batch ran
200 state-store tasks and took 3.5–6.7 s for about 50 events, longer than the 5-second
trigger. At 4, it takes 1.0–1.7 s for about 2,000 events. Each query writes the value into its
checkpoint on its first run and ignores later changes, so after changing it, start once with
`--fresh`.

**C. The start order matters.** Files that pile up in `data/stream_landing/` before a query
first starts are all read by its first micro-batch, one giant batch. The job prints a WARNING
when it sees that. Stop, run it with `--fresh`, then start the replayer.

**D. The replayer's rules, for anyone who touches it:**

- It reads `data/bronze/` (258,390 users), never the raw CSV (3,696,117). A 14x larger
  population would put the >= 99% correctness gate out of reach.
- Every file is written under a hidden name (`.tmp-...`) and renamed. Spark skips dot-files,
  and a rename is atomic, so a micro-batch never reads half a file.
- File names are unique per run: `<run start>-<sequence>.json`. The checkpoint remembers every
  path it has read, and a repeated name would be skipped silently.

**E. "events after cleaning" is not "rows in the file".** Spark pushes `clean()`'s row filters
into the JSON scan, so the progress line counts the events that survive them. A replayer file
of 1,804 rows shows up as 1,791. Measured on six files, every one matched exactly.

**F. The toolchain pin, and its reason stated correctly.** `pyspark==4.1.3` on Python 3.14 with
OpenJDK 21 is pinned exactly. PySpark 3.5.x does not work on Python 3.14: its vendored
cloudpickle 2.x calls `pickle._getattribute`, which changed in 3.14. cloudpickle serialises
**every Python function Spark ships to a worker**: UDFs, RDD lambdas, and the `foreachBatch`
function under Spark Connect. In the classic `local[*]` mode used here, `foreachBatch` is
*not* pickled. `ForeachBatchFunction` (`pyspark/sql/utils.py`) is a py4j callback that runs in
the driver's own Python process. The pin stands. The earlier wording, "cloudpickle serialises
every foreachBatch closure", was wrong about the mechanism.

## Gate 1a checklist (BR1, end of W40)

- [ ] `docker compose up -d --wait`, `python serving/check_infra.py` prints INFRA OK, and
      `python serving/apply_schema.py` prints APPLY_SCHEMA OK.
- [ ] `python processing/streaming_gold.py --fresh` prints READY; *then*
      `python ingestion/replayer.py --speed 60 --start "2019-11-17 08:00:00"`.
- [ ] Screenshot 1: terminal 1 with at least five micro-batches, both lines each.
- [ ] Screenshot 2: `docker compose exec cassandra cqlsh -e "SELECT * FROM
      shopinsight.gmv_by_minute WHERE event_date = '2019-11-17' AND category_l1 = 'electronics'
      LIMIT 10"`. Rows come newest first (`window_start DESC`). Their times must match the
      "Vietnam" times in the replayer's log. Seven hours later means Block 0 is missing.
      Run it again with `category_l1 = 'all'`: the total row for each minute.
- [ ] Screenshot 3: the BR1 screen (`/br1`) with the API and the replayer running. The line
      extends at every 10-second refresh; the footer reads `Cassandra · 1 partition`.
- [ ] Ctrl-C the job: it prints `stopping after the running micro-batch`, then `stopped`, with
      no Java error. Start it again without `--fresh`, and check it resumes with no giant
      batch.
- [ ] The three screenshots go in `docs/evidence/` and the group chat.

## What each BR changes, in one table

| | BR1 (done) | BR3 | BR5 | BR8 |
|---|---|---|---|---|
| Function | `start_br1` | `start_br3` | `start_br5` | `start_br8` |
| Window | 1 min tumbling | 15 min sliding every 1 min | 30 min after the cart | 5 min tumbling |
| Group by | window, event_date, category_l1 | window, product_id | user_session | window, user_id |
| Output mode | update | **append** | append | update |
| Rank in `write_batch` | no | **yes**, top 20 | no | no |
| Delete before insert | no | **yes**, `WHERE window_start = ?` | **never** | no |
| Extra `all` row (explode) | yes | **no** | **no** | **no** |
| Checkpoint | `br1_gmv_by_minute` | `br3_trending_products` | `br5_abandoned_carts` | `br8_order_velocity_alerts` |
