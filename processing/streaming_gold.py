"""Streaming gold: the four real-time jobs (BR1, BR3, BR5, BR8) in one process.

    python processing/streaming_gold.py             # terminal 1, FIRST. Wait for READY
    python ingestion/replayer.py --speed 60         # terminal 2, only after READY

    python processing/streaming_gold.py --fresh     # before a demo: start from nothing

Every job reads the replayer's JSON files through processing/source.py, cleans
them with the SAME seven rules as silver (clean() is imported from
batch_silver.py, never copied), and writes one Cassandra table from foreachBatch
with the plain cassandra-driver. docs/STREAMING_PATTERN.md walks through BR1
block by block and says what to change for BR3, BR5 and BR8; SPARK_GUIDE_VI.md
has the same walk-through in Vietnamese.

    BR1  Dat     1-minute windows              gmv_by_minute            done (W40)
    BR3  Khang   15-minute window, 1-min slide trending_products        done (W41)
    BR5  Nguyen  cart, no purchase in 30 min   abandoned_carts          stub (W41)
    BR8  Tin     5-minute windows per user     order_velocity_alerts    stub (W41)

THIS JOB NEVER WRITES data/silver/. Silver has exactly one writer,
batch_silver.py. A Parquet file sink would create data/silver/_spark_metadata/,
after which Spark reads only the files listed there and every file the batch
wrote goes invisible to Spark (DuckDB still sees them). A foreachBatch write
would duplicate rows, because the replayer replays bronze that silver already
holds. The only outputs here are the Cassandra tables.

Start order matters: this job first, the replayer after READY. Files already
sitting in data/stream_landing/ when a query starts with no checkpoint are all
read by its first micro-batch, one giant batch that looks nothing like real
time. Restarting WITHOUT --fresh resumes from data/checkpoints/<job>/: the
files read before are not read again and open windows keep their totals.

When to use --fresh: before replaying a period again, and after pulling a
change to a query's code (a checkpoint of the old query resumes without a
word). The checkpoint remembers the watermark, so events older than it count
as late and are dropped without a word - the screen would just freeze.
--fresh deletes data/checkpoints/*/ and data/stream_landing/*.json and empties
the four tables this job writes (STREAMING_TABLES), and nothing else. Emptying
them matters as much as the checkpoints: rows an earlier, longer replay wrote
would otherwise stay the newest in their partition, and a chart of "the last
60 minutes" would stand still on them. Everything in those tables comes back
from the replay.

Ctrl-C waits up to 10 s for the running micro-batch to finish, then stops
(see main()). A second Ctrl-C quits at once.

Done when the log prints READY, then two lines per micro-batch once the
replayer runs - the rows upserted into Cassandra, then the events read and the
watermark:

    [br1_gmv_by_minute] batch 4: upserted 59 rows into gmv_by_minute (12 partitions) in 569 ms
    [br1_gmv_by_minute] batch 4: 2,087 events after cleaning, watermark 2019-11-17 15:09:59, 1,304 ms

(12 partitions: the categories with an event in those 5 minutes, plus 'all'.)
"""

import argparse
import itertools
import os
import shutil
import signal
import sys
import time
from pathlib import Path

# The same three lines open every Spark script in this repo (see processing/kata.py).
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))  # lets `python processing/streaming_gold.py` find the repo root
os.environ["SPARK_CONF_DIR"] = str(REPO / "conf")  # driver memory + UTC, before the JVM starts
# A fourth line, for the scripts that collect() timestamps and send them on. PySpark
# turns a Spark timestamp into a Python datetime in the LAPTOP's time zone
# (TimestampType.fromInternal calls datetime.fromtimestamp), ignoring Spark's UTC
# session. On a UTC+7 laptop a window that starts at 14:01 comes back as 21:01, and
# cassandra-driver stores that naive 21:01 as 21:01 UTC: seven hours off, with no
# error, and different on every machine. Pinning this process to UTC makes the
# Python side agree with Spark's.
os.environ["TZ"] = "UTC"
time.tzset()

from cassandra.cluster import EXEC_PROFILE_DEFAULT, Cluster, ExecutionProfile, NoHostAvailable
from cassandra.policies import DCAwareRoundRobinPolicy
from cassandra.query import BatchStatement, BatchType
from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F

from processing.batch_silver import clean
from processing.source import LANDING_DIR, read_events
from serving.check_infra import read_env

CHECKPOINT_DIR = REPO / "data" / "checkpoints"   # one subdirectory per query: never shared
DATA_CENTER = "datacenter1"                       # the node's own name (check_infra.py prints it)

# How late an event may arrive and still count. The replayer sends events in
# time order, so nothing is ever this late here; the watermark is what lets
# Spark DROP the state of windows that can no longer change. Without one, the
# state of every window since the start stays in memory until the JVM dies.
WATERMARK = "10 minutes"

# How often each query looks for new files. The replayer writes one every 5
# seconds, so this gives about one file per micro-batch. The default trigger
# (as fast as possible) would list the landing directory about 100 times a
# second per query, even when nothing has arrived.
TRIGGER = "5 seconds"

# Partitions of every shuffle, and so of every query's state store. See main().
STATE_PARTITIONS = "4"

# The Cassandra tables this job writes, and the only ones --fresh empties. Not
# stockout_risk: BR6's batch job writes that one. Emptying all four here, before
# any query starts, is a reset. It is not the write_batch delete that the BR5
# stub forbids, which would erase carts found earlier in the same run.
STREAMING_TABLES = ("gmv_by_minute", "trending_products", "abandoned_carts", "order_velocity_alerts")

# How long Ctrl-C waits for a running micro-batch to finish before stopping
# anyway, shared by all queries. Measured with BR1 alone, a batch takes 1-2 s.
# Once BR3, BR5 and BR8 share the JVM a batch may outlast the 5 s trigger;
# batches then run back to back and the wait can run out, which cuts a batch
# (it re-runs on restart, so nothing is lost). Re-measure in W41.
STOP_WAIT_SECONDS = 10

# BR1 only: the category_l1 of the extra row each window gets, summed over every
# category. The screen's default filter, "All categories", then reads this one
# partition instead of reading 14 and adding them up in the API. Silver's
# category_l1 has 13 categories plus 'unknown' (measured 2026-09-30), so 'all'
# names no real one.
ALL_CATEGORIES = "all"

# BR3 only: how many products each window keeps (API_CONTRACT section 5).
TRENDING_TOP = 20


# ---------------------------------------------------------------------------
# BR1 (Dat) - GMV and order count per minute, per category -> gmv_by_minute
# The reference implementation. BR3, BR5 and BR8 copy this shape.
# ---------------------------------------------------------------------------

def start_br1(events, cassandra):
    """GMV and purchase count per 1-minute window and top-level category.

    Each window also gets a row with category_l1 = 'all', the total over every
    category, for the screen's default filter.

    events: the cleaned, watermarked stream built in main(). Returns the
    running StreamingQuery.
    """
    # One prepared statement, parsed by Cassandra once and reused for every row.
    # gmv_by_minute's key is ((event_date, category_l1), window_start). None of
    # those values changes when a window is emitted again, so a second write of
    # the same window lands on the same row: an upsert, no DELETE needed. Compare
    # trending_products and abandoned_carts in docs/STREAMING_PATTERN.md.
    insert = cassandra.prepare(
        "INSERT INTO gmv_by_minute (event_date, category_l1, window_start, gmv, order_count) "
        "VALUES (?, ?, ?, ?, ?)"
    )

    def write_batch(batch, batch_id):
        """Runs once per micro-batch, on the driver. batch is a plain static DataFrame."""
        started = time.monotonic()
        # Update mode hands over only the windows this micro-batch changed: about
        # 5 minutes x 15 keys (14 categories plus 'all') at --speed 60, so
        # collect() is safe.
        rows = batch.select(
            "event_date", "category_l1", F.col("window.start").alias("window_start"),
            "gmv", "order_count",
        ).collect()
        # One UNLOGGED batch per partition key: every statement in it goes to the
        # same partition, which is the one case where a Cassandra batch is cheap.
        rows.sort(key=lambda row: (row.event_date, row.category_l1))
        partitions = 0
        for _, same_partition in itertools.groupby(rows, key=lambda row: (row.event_date, row.category_l1)):
            statement = BatchStatement(batch_type=BatchType.UNLOGGED)
            for row in same_partition:
                statement.add(insert, (row.event_date, row.category_l1, row.window_start,
                                       row.gmv, row.order_count))
            cassandra.execute(statement)
            partitions += 1
        if rows:
            print(f"[br1_gmv_by_minute] batch {batch_id}: upserted {len(rows)} rows into gmv_by_minute "
                  f"({partitions} partitions) in {(time.monotonic() - started) * 1000:.0f} ms", flush=True)
        else:
            # A batch with no new events runs when the watermark moves: Spark drops
            # the state of the windows it closed. Nothing changed, nothing to write.
            print(f"[br1_gmv_by_minute] batch {batch_id}: no window changed (watermark moved on)", flush=True)

    is_purchase = F.col("event_type") == "purchase"
    gmv_by_minute = (
        events
        # Each event counts twice: once under its own category and once under
        # 'all'. So the 'all' row is summed by the same aggregation, from the same
        # state, and is never partial. Summing the category rows inside
        # write_batch instead would be wrong without any error: update mode
        # hands over only the categories that changed in this micro-batch, so
        # 'all' would drop every category that did not. BR1 only: an explode in
        # BR5 or BR8 would double their counts, and in BR3 list every product twice.
        .withColumn("category_l1", F.explode(F.array("category_l1", F.lit(ALL_CATEGORIES))))
        # event_date is constant inside a 1-minute window (midnight is a minute
        # boundary), so grouping by it splits nothing; it just carries the
        # partition key through. Views and carts are kept on purpose: a minute
        # with views but no purchase gives a row with gmv 0 instead of a hole in
        # the chart - the 7% sample has only about 1.5 purchases a minute.
        .groupBy(F.window("event_time", "1 minute"), "event_date", "category_l1")
        .agg(
            F.sum(F.when(is_purchase, F.col("price")).otherwise(0)).alias("gmv"),
            F.count_if(is_purchase).alias("order_count"),
        )
    )
    return (
        gmv_by_minute.writeStream
        .queryName("br1_gmv_by_minute")
        # update: each micro-batch emits every window whose totals changed, with
        # the running total so far. The screen sees the current minute grow.
        # (append would wait until the watermark closes a window: 10 minutes late.)
        .outputMode("update")
        .foreachBatch(write_batch)
        .option("checkpointLocation", str(CHECKPOINT_DIR / "br1_gmv_by_minute"))
        .trigger(processingTime=TRIGGER)
        .start()
    )


# ---------------------------------------------------------------------------
# BR3 (Khang) - top 20 products per 15-minute window sliding every minute
# -> trending_products
# ---------------------------------------------------------------------------

def start_br3(events, cassandra):
    """Top 20 products by view count in each 15-minute window, sliding every minute.

    Views and carts are counted per (window, product) on the stream, then ranked
    and cut to 20 inside write_batch: a streaming DataFrame cannot be ranked.

    events: the cleaned, watermarked stream built in main(). Returns the
    running StreamingQuery.
    """
    # trending_products' key is (window_start, rank). A product at rank 3 in one
    # write of a window and rank 5 in the next would leave two rows, and the
    # screen would list it twice. One partition is one window, so each window is
    # deleted first, then its top 20 inserted. Append mode writes a window once,
    # but Spark runs a micro-batch again after a crash, and the delete makes
    # that harmless.
    delete = cassandra.prepare("DELETE FROM trending_products WHERE window_start = ?")
    insert = cassandra.prepare(
        "INSERT INTO trending_products "
        "(window_start, rank, product_id, brand, category_l1, view_count, cart_count) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)"
    )
    # Ties at the cut are common: on 17 Nov 15:00-21:00 (Vietnam time), #20 and
    # #21 had the same view_count in 212 of 360 windows, and the same cart_count
    # as well in 64. product_id settles the rest, so a re-run ranks the same way.
    by_window = Window.partitionBy("window_start").orderBy(
        F.desc("view_count"), F.desc("cart_count"), F.asc("product_id"))

    def write_batch(batch, batch_id):
        """Runs once per micro-batch, on the driver. batch is a plain static DataFrame."""
        started = time.monotonic()
        # Rank and cut in Spark, then collect() at most 20 rows per window: a
        # closed window holds about 850 products (the month's median), up to 3,767.
        rows = (
            batch.withColumn("window_start", F.col("window.start"))
            .withColumn("rank", F.row_number().over(by_window))
            .where(F.col("rank") <= TRENDING_TOP)
            .select("window_start", "rank", "product_id", "brand", "category_l1", "view_count", "cart_count")
            .collect()
        )
        rows.sort(key=lambda row: (row.window_start, row.rank))
        windows = 0
        for window_start, same_window in itertools.groupby(rows, key=lambda row: row.window_start):
            # The delete runs on its own, never inside the insert batch: every
            # statement in a batch gets the same write timestamp, and at equal
            # timestamps Cassandra lets the delete win, so the window would come
            # out empty. Run separately, the insert gets the later timestamp.
            cassandra.execute(delete, (window_start,))
            statement = BatchStatement(batch_type=BatchType.UNLOGGED)
            for row in same_window:
                statement.add(insert, (row.window_start, row.rank, row.product_id, row.brand,
                                       row.category_l1, row.view_count, row.cart_count))
            cassandra.execute(statement)
            windows += 1
        if rows:
            print(f"[br3_trending_products] batch {batch_id}: replaced {windows} windows in trending_products "
                  f"({len(rows)} rows, windows from {rows[0].window_start:%H:%M} to {rows[-1].window_start:%H:%M}) "
                  f"in {(time.monotonic() - started) * 1000:.0f} ms", flush=True)
        else:
            # Append mode writes only the windows the watermark has closed. A
            # batch that closed none has nothing to write.
            print(f"[br3_trending_products] batch {batch_id}: no window closed yet", flush=True)

    is_view = F.col("event_type") == "view"
    is_cart = F.col("event_type") == "cart"
    trending = (
        events
        # Purchases count in neither column; dropping them keeps them out of the state.
        .where(is_view | is_cart)
        # No explode: that is BR1's alone, and here it would list every product
        # twice. Grouped by product only, not by brand: in silver 612 products have
        # more than one brand value, 573 a real brand on some events and 'unknown'
        # (clean()'s fill for a null) on others, 42 two real brands, 3 both. Grouping
        # by brand would split such a product into two rows. The brand kept is the
        # real one when any event has it, and of two real ones the alphabetically
        # last. category_l1 never differs within a product (measured on silver), so
        # max() carries it through.
        .groupBy(F.window("event_time", "15 minutes", "1 minute"), "product_id")
        .agg(
            F.count_if(is_view).alias("view_count"),
            F.count_if(is_cart).alias("cart_count"),
            F.coalesce(F.max(F.when(F.col("brand") != "unknown", F.col("brand"))), F.lit("unknown")).alias("brand"),
            F.max("category_l1").alias("category_l1"),
        )
    )
    return (
        trending.writeStream
        .queryName("br3_trending_products")
        # append, not BR1's update: update hands write_batch only the products
        # whose counts changed in this micro-batch, and a top 20 ranked from those
        # silently misses every product that did not. append hands over each
        # window once, complete, when the watermark closes it: 10 minutes of
        # event time after the window ends.
        .outputMode("append")
        .foreachBatch(write_batch)
        .option("checkpointLocation", str(CHECKPOINT_DIR / "br3_trending_products"))
        .trigger(processingTime=TRIGGER)
        .start()
    )


# ---------------------------------------------------------------------------
# W41 stubs. Replace the body, keep the signature, return the StreamingQuery.
# Copy start_br1, except its explode: same events, own checkpoint directory,
# own queryName.
# ---------------------------------------------------------------------------


def start_br5(events, cassandra):
    """BR5 (Nguyen, W41): sessions with a cart and no purchase 30 minutes later.

    Sink: abandoned_carts, key ((event_date), user_session).
    Trap: NEVER delete from this table inside write_batch. (The only exception
    is --fresh emptying it before any query starts.) It accumulates all day;
    deleting the event_date partition erases every cart found by earlier
    micro-batches and the screen empties itself mid-demo. The key has no
    cart_value in it, so a plain INSERT of the same session overwrites its own
    row: already idempotent.
    Checkpoint: data/checkpoints/br5_abandoned_carts/.
    """
    return None


def start_br8(events, cassandra):
    """BR8 (Tin, W41): purchases per user in 5-minute windows, with a severity label.

    Sink: order_velocity_alerts, key ((event_date), window_start, user_id). The
    key never changes for a (window, user), so an upsert is enough, as in BR1.
    Checkpoint: data/checkpoints/br8_order_velocity_alerts/.
    """
    return None


# ---------------------------------------------------------------------------
# Plumbing shared by the four jobs.
# ---------------------------------------------------------------------------

def connect_cassandra():
    """A session on the shopinsight keyspace, or exit with the command that fixes it."""
    env = read_env()
    host, port, keyspace = env["CASSANDRA_HOST"], int(env["CASSANDRA_PORT"]), env["CASSANDRA_KEYSPACE"]
    # The policy goes in an execution profile: passed straight to Cluster() it
    # still works, but prints a DeprecationWarning into the micro-batch log.
    profile = ExecutionProfile(load_balancing_policy=DCAwareRoundRobinPolicy(local_dc=DATA_CENTER))
    cluster = Cluster([host], port=port, execution_profiles={EXEC_PROFILE_DEFAULT: profile})
    try:
        session = cluster.connect()
    except NoHostAvailable:
        sys.exit(f"Cassandra is not answering at {host}:{port}. "
                 "Run docker compose up -d --wait, then python serving/check_infra.py.")
    # Connect first, then look the keyspace up: connect(keyspace) reports a
    # missing keyspace as NoHostAvailable too, which would send you to Docker.
    if keyspace not in cluster.metadata.keyspaces:
        cluster.shutdown()
        sys.exit(f"Keyspace {keyspace} does not exist. Run python serving/apply_schema.py.")
    session.set_keyspace(keyspace)
    return cluster, session


def forget_earlier_runs(cassandra):
    """--fresh: remove every checkpoint and replayed file, and empty STREAMING_TABLES. Nothing else."""
    checkpoints = [path for path in CHECKPOINT_DIR.iterdir() if path.is_dir()]
    for path in checkpoints:
        shutil.rmtree(path)
    landed = list(LANDING_DIR.glob("*.json"))
    for path in landed:
        path.unlink()
    for table in STREAMING_TABLES:
        # TRUNCATE snapshots the table first (auto_snapshot), which can outlast the
        # driver's default 10 s timeout on a slow laptop; the server allows 60 s.
        cassandra.execute(f"TRUNCATE {table}", timeout=60)
    print(f"--fresh: removed {len(checkpoints)} checkpoint directories and {len(landed):,} landed files, "
          f"emptied {', '.join(STREAMING_TABLES)}")


def wait_until_ready(queries):
    """Block until every query has read what is already there and is idle."""
    while True:
        for query in queries:
            if not query.isActive:
                raise query.exception() or RuntimeError(f"{query.name} stopped")
        if all(query.lastProgress is not None and not query.status["isTriggerActive"]
               for query in queries):
            return
        time.sleep(0.5)


def stop_between_batches(queries):
    """Stop each query once the micro-batch it is running has finished.

    Stopping in the middle of a batch interrupts it on the way to Cassandra.
    Nothing is lost - the batch has offsets but no commit, so the restart runs
    it again - but the log fills with Java errors, a StackOverflowError among
    them, right where the Gate 1a screenshot of a restart is taken.
    """
    deadline = time.monotonic() + STOP_WAIT_SECONDS
    for query in queries:
        while query.isActive and query.status["isTriggerActive"] and time.monotonic() < deadline:
            time.sleep(0.1)
        query.stop()


def print_progress(queries):
    """One line per finished micro-batch, per query, until Ctrl-C or a query fails."""
    printed = {}
    while True:
        for query in queries:
            if not query.isActive:
                raise query.exception() or RuntimeError(f"{query.name} stopped")
            progress = query.lastProgress
            # An idle query reports every 10 s with 0 rows and the id of the batch
            # it has not run yet; keying on the timestamp and skipping empty
            # reports keeps one line per micro-batch that read something.
            if progress is None or progress["numInputRows"] == 0 or printed.get(query.name) == progress["timestamp"]:
                continue
            printed[query.name] = progress["timestamp"]
            # numInputRows counts the events that pass clean()'s row rules (price > 0,
            # user and session present): Spark pushes those filters into the JSON
            # scan, so a replayer file of 1,804 rows can show up here as 1,791.
            # The watermark is Vietnam wall-clock time, because clean() shifted
            # event_time; before the first batch it is 1970, i.e. none yet.
            watermark = progress["eventTime"].get("watermark", "1970")[:19].replace("T", " ")
            if watermark.startswith("1970"):
                watermark = "none yet"
            print(f"[{query.name}] batch {progress['batchId']}: {progress['numInputRows']:,} events "
                  f"after cleaning, watermark {watermark}, "
                  f"{progress['durationMs'].get('triggerExecution', 0):,} ms", flush=True)
        time.sleep(1)


def main():
    parser = argparse.ArgumentParser(description="Run the streaming jobs (BR1, BR3, BR5, BR8).")
    parser.add_argument("--fresh", action="store_true",
                        help="delete data/checkpoints/*/ and data/stream_landing/*.json and empty "
                             "the four streaming tables first")
    args = parser.parse_args()

    # Cassandra first: a missing container should fail in one second, not after
    # the JVM has taken ten to start.
    cluster, cassandra = connect_cassandra()
    if args.fresh:
        forget_earlier_runs(cassandra)
    waiting = len(list(LANDING_DIR.glob("*.json")))
    if waiting and not any(path.is_dir() for path in CHECKPOINT_DIR.iterdir()):
        print(f"WARNING: {waiting:,} files already in {LANDING_DIR} and no checkpoint: the first "
              "micro-batch reads them all at once. Stop, run with --fresh, then start the replayer.")

    spark = (
        SparkSession.builder.master("local[*]").appName("streaming_gold")
        # The [Stage 3:====>] bars would be interleaved with the micro-batch log.
        .config("spark.ui.showConsoleProgress", "false")
        # Measured, not guessed (W40 dry run, BR1 alone, 20 cores): with Spark's
        # default of 200, every micro-batch runs 200 state-store tasks and takes
        # 3.5-6.7 s for about 50 events - longer than the 5-second trigger, so the
        # job falls behind the replayer. At 4: 1.0-1.7 s for about 2,000 events.
        # The value is written into each checkpoint on its first run and reused
        # from then on: after changing it, start once with --fresh.
        .config("spark.sql.shuffle.partitions", STATE_PARTITIONS)
        .getOrCreate()
    )
    # Starting Spark replaced Python's Ctrl-C handler with pyspark's, which
    # cancels every running Spark job before raising KeyboardInterrupt
    # (pyspark/core/context.py). A micro-batch caught halfway then dies inside
    # its own write. Measured on 30 Sep, Ctrl-C sent while a batch ran: a Java
    # StackOverflowError in 1 of 7 tries, other errors in 4 of 7; with this line,
    # none in 8. Python's own handler only raises KeyboardInterrupt, and
    # stop_between_batches() below does the rest.
    signal.signal(signal.SIGINT, signal.default_int_handler)

    # The stream every job starts from, in three steps:
    #   read_events  the replayer's JSON, with EVENT_SCHEMA (processing/source.py)
    #   clean        silver's seven rules: UTC+7 shift, event_date recomputed from
    #                the shifted time, category_l1 'unknown', null session dropped
    #   watermark    on the SHIFTED event_time, so it is Vietnam time as well
    # Each writeStream below still gets its own source, state and checkpoint.
    events = clean(read_events(spark)).withWatermark("event_time", WATERMARK)

    try:
        # Inside the try: if a W41 start_brN raises at .start(), BR1 is already
        # running, and the finally below still stops it cleanly.
        started = [start(events, cassandra) for start in (start_br1, start_br3, start_br5, start_br8)]
        queries = [query for query in started if query is not None]
        wait_until_ready(queries)
        names = ", ".join(query.name for query in queries)
        print(f"READY: {len(queries)} of 4 jobs running ({names}), watching {LANDING_DIR}")
        print("READY: now start python ingestion/replayer.py --speed 60", flush=True)
        print_progress(queries)
    except KeyboardInterrupt:
        print("Ctrl-C: stopping after the running micro-batch (Ctrl-C again to quit now)", flush=True)
    finally:
        stop_between_batches(spark.streams.active)
        print("stopped; the checkpoints keep the progress", flush=True)
        spark.stop()
        cluster.shutdown()


if __name__ == "__main__":
    main()
