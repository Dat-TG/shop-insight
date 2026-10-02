"""Bronze: a 7% user sample of the raw event log, as Parquet.

    python ingestion/load_bronze.py

Reads data/raw/2019-Nov.csv (67,501,979 rows, 3,696,117 users) and keeps every
event of the users for which

    pmod(hash(user_id), 100) < 7

is true: about 7% of the users, each with their whole month of history. Writes
them to data/bronze/ as Parquet, one directory per event_date. Nothing is
cleaned or changed; bronze is the untouched reference copy, and
batch_silver.py does the cleaning.

This is the only script that turns the raw CSV into data (kata.py only reads
100,000 rows of it to check an install). From W40, replayer.py reads
data/bronze/, never the raw file: the raw file holds 14x more users, so the
stream would stop matching the batch side.

Why sample users instead of taking the first 5 million rows: the file is in
time order, so its first 5 million rows cover about three days of November
(row 5,000,000 is 4 Nov 07:09:03 UTC).
BR4's recency would mean nothing, and BR6's velocity_7d would not have seven
days to average over.

Why all four machines get the same rows:
- hash() is Spark's Murmur3 with a fixed seed. No random numbers, no seed, no
  .sample(). data/ is not in git; each person rebuilds bronze locally.
- user_id is read as BIGINT (processing/schema.py). hash() of an INT gives
  other values, so reading it as INT would pick a different set of users.
- event_date is the UTC date, because conf/spark-defaults.conf pins the
  session time zone to UTC. On a UTC+7 laptop without that, the last seven
  hours of 30 Nov would land in a 31st directory, 2019-12-01.

Done when the script prints BRONZE OK. Post the numbers it prints in the group
chat. Every machine must print exactly these (Spark 4.1.3, measured), which is
inside the W38 target of 4.4-5.0 million rows:

    rows               4,767,012
    users                258,390
    products             129,899
    date directories          30

The script refuses to start if the raw file is not the complete
9,006,762,395 bytes. If the size is right but the numbers differ, someone
changed the sampling rule, processing/schema.py or conf/: check with git
status and git diff. Measured at 25 s on 20 cores; expect a few minutes on a
4-core laptop.
"""

import os
import sys
import time
from pathlib import Path

# The same three lines open every Spark script in this repo (see processing/kata.py).
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))  # lets `python ingestion/load_bronze.py` import processing.schema
os.environ["SPARK_CONF_DIR"] = str(REPO / "conf")  # driver memory + UTC, before the JVM starts

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from processing.schema import EVENT_SCHEMA, RAW_TIMESTAMP_FORMAT

RAW_CSV = REPO / "data" / "raw" / "2019-Nov.csv"
RAW_BYTES = 9_006_762_395  # size of the complete download (wc -c)
BRONZE_DIR = REPO / "data" / "bronze"

# The sampling rule, written exactly as in the design documents.
SAMPLE_RULE = "pmod(hash(user_id), 100) < 7"

# What every machine must get, exactly. A range would not do: a wrong sample
# (user_id read as INT: 4,713,498 rows) looks just as plausible.
EXPECTED = {"rows": 4_767_012, "users": 258_390, "products": 129_899}
EXPECTED_DAYS = 30  # 1-30 November 2019


def read_raw(spark):
    """All rows of the raw CSV, parsed with the shared schema (same options as kata.py)."""
    return (
        spark.read
        .option("header", True)
        .option("timestampFormat", RAW_TIMESTAMP_FORMAT)   # "2019-11-01 00:00:00 UTC"
        .option("mode", "FAILFAST")                        # a row that does not parse stops the job, never becomes null
        .schema(EVENT_SCHEMA)                              # never inferSchema: see processing/schema.py
        .csv(str(RAW_CSV))
    )


def sample_users(events):
    """Keep every event of the users in the 7% hash bucket."""
    return events.where(F.expr(SAMPLE_RULE))


def add_event_date(events):
    """Add the partition column: the UTC calendar date of event_time.

    to_date() uses the session time zone, which conf/spark-defaults.conf pins
    to UTC. batch_silver.py shifts event_time to UTC+7 and recomputes
    event_date there; bronze keeps the file's own UTC.
    """
    return events.withColumn("event_date", F.to_date("event_time"))


def write_bronze(events):
    """Write Parquet, one directory per day: data/bronze/event_date=2019-11-01/..."""
    try:
        (
            events.write
            .mode("overwrite")          # a re-run replaces bronze, never appends a second copy
            .partitionBy("event_date")
            .parquet(str(BRONZE_DIR))
        )
    finally:
        # "overwrite" deletes the whole directory first, including the .gitkeep
        # that git tracks so a fresh clone has data/bronze/. Put it back, even
        # when the write fails halfway.
        BRONZE_DIR.mkdir(parents=True, exist_ok=True)
        (BRONZE_DIR / ".gitkeep").touch()


def report(spark):
    """Read bronze back from disk, print what is really there, return True if it passes."""
    bronze = spark.read.parquet(str(BRONZE_DIR))
    stats = bronze.agg(
        F.count("*").alias("rows"),
        F.countDistinct("user_id").alias("users"),
        F.countDistinct("product_id").alias("products"),
        F.count_if(F.col("event_time").isNull()).alias("null_event_time"),
    ).first()
    days = sorted(path.name for path in BRONZE_DIR.glob("event_date=*"))

    print()
    ok = True
    for name, expected in EXPECTED.items():
        note = "" if stats[name] == expected else f"   <-- expected {expected:,}"
        ok = ok and stats[name] == expected
        print(f"{name:<18}{stats[name]:>10,}{note}")
    print(f"date directories  {len(days):>10}   (expect {EXPECTED_DAYS}: {days[0] if days else '-'} .. {days[-1] if days else '-'})")
    print(f"null event_time   {stats['null_event_time']:>10,}   (expect 0)")

    return ok and len(days) == EXPECTED_DAYS and stats["null_event_time"] == 0


def main():
    if not RAW_CSV.exists():
        sys.exit(f"{RAW_CSV} not found. Download it first: docs/SETUP_SPARK.md step 7.")
    # Check before the write deletes the old bronze: a cut-off download silently
    # drops the users whose events all sit at the end of the month.
    if RAW_CSV.stat().st_size != RAW_BYTES:
        sys.exit(f"{RAW_CSV} is {RAW_CSV.stat().st_size:,} bytes, not {RAW_BYTES:,}: "
                 "a partial download. Download it again: docs/SETUP_SPARK.md step 7.")

    started = time.monotonic()
    spark = SparkSession.builder.master("local[*]").appName("load_bronze").getOrCreate()

    events = add_event_date(sample_users(read_raw(spark)))
    write_bronze(events)
    ok = report(spark)
    spark.stop()

    print(f"took              {time.monotonic() - started:>10.0f} s")
    if ok:
        print("BRONZE OK")
    else:
        print("BRONZE CHECK FAILED: see the lines above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
