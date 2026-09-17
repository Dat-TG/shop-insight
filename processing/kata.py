"""Spark install check: the first Spark script every team member runs.

    python processing/kata.py

Reads the first 100,000 rows of data/raw/2019-Nov.csv, counts them by
event_type, and compares the four counts with what every correct install
prints. Needs nothing but the raw CSV: no bronze, no Docker.

Expected ending (docs/SETUP_SPARK.md step 8):

    view                97,489
    cart                 1,089
    remove_from_cart         0
    purchase             1,422
    KATA OK

remove_from_cart is 0 on purpose: 2019-Nov.csv has no such events (see
processing/schema.py). Any other difference means a truncated download or a
broken install. The lines printed first (versions, heap, time zone, time range)
say which.
"""

import os
import platform
import sys
from pathlib import Path

# The same three lines open every Spark script in this repo.
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))  # lets `python processing/kata.py` import processing.schema
# Must run before the first SparkSession starts the JVM. conf/spark-defaults.conf
# holds the driver memory and the UTC time zone; set any later, Spark ignores it.
os.environ["SPARK_CONF_DIR"] = str(REPO / "conf")

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from processing.schema import EVENT_SCHEMA, RAW_TIMESTAMP_FORMAT

RAW_CSV = REPO / "data" / "raw" / "2019-Nov.csv"
ROWS = 100_000

# The first 100,000 data rows of 2019-Nov.csv, counted without Spark:
#   head -100001 data/raw/2019-Nov.csv | tail -n +2 | cut -d, -f2 | sort | uniq -c
EXPECTED = {"view": 97_489, "cart": 1_089, "remove_from_cart": 0, "purchase": 1_422}
# Their first and last event_time, in UTC as written in the file.
EXPECTED_FIRST = "2019-11-01 00:00:00"
EXPECTED_LAST = "2019-11-01 03:52:45"


def check_environment(spark):
    """Print the versions and the two settings conf/spark-defaults.conf controls.

    Returns True when both settings really reached the JVM.
    """
    jvm = spark.sparkContext._jvm  # the running JVM, reached through py4j
    java_version = jvm.java.lang.System.getProperty("java.version")
    # The heap the JVM really got, not the value some config claims.
    heap_gib = jvm.java.lang.Runtime.getRuntime().maxMemory() / 2**30
    time_zone = spark.conf.get("spark.sql.session.timeZone")
    print(f"Python {platform.python_version()} | Spark {spark.version} | Java {java_version}")
    print(f"Driver heap: {heap_gib:.1f} GiB (expect 6.0; about 1.0 means conf/spark-defaults.conf was not read)")
    print(f"Time zone:   {time_zone} (expect UTC)")
    return heap_gib > 5.5 and time_zone == "UTC"


def read_first_rows(spark):
    """The first ROWS data rows of the raw CSV, parsed with the shared schema."""
    return (
        spark.read
        .option("header", True)                            # the first line holds column names
        .option("timestampFormat", RAW_TIMESTAMP_FORMAT)   # "2019-11-01 00:00:00 UTC"
        .option("mode", "FAILFAST")                        # a row that does not parse stops the job, never becomes null
        .schema(EVENT_SCHEMA)                              # never inferSchema: see processing/schema.py
        .csv(str(RAW_CSV))
        .limit(ROWS)
    )


def main():
    if not RAW_CSV.exists():
        sys.exit(f"{RAW_CSV} not found. Download it first: docs/SETUP_SPARK.md step 7.")

    spark = SparkSession.builder.master("local[*]").appName("kata").getOrCreate()
    ok = check_environment(spark)

    # Spark parses only the columns a query uses. Asking for event_time as well
    # makes FAILFAST prove the timestamp format, and shows the UTC setting at
    # work: a machine on UTC+7 without it would print 07:00:00.
    rows = (
        read_first_rows(spark)
        .groupBy("event_type")
        .agg(
            F.count("*").alias("count"),
            # date_format renders in the session time zone and returns text, so
            # Python cannot shift it into the laptop's own time zone.
            F.date_format(F.min("event_time"), "yyyy-MM-dd HH:mm:ss").alias("first"),
            F.date_format(F.max("event_time"), "yyyy-MM-dd HH:mm:ss").alias("last"),
        )
        .collect()
    )
    spark.stop()
    counts = {row["event_type"]: row["count"] for row in rows}
    first = min(row["first"] for row in rows)
    last = max(row["last"] for row in rows)

    print(f"Events from: {first} to {last} (expect {EXPECTED_FIRST} to {EXPECTED_LAST})")
    ok = ok and (first, last) == (EXPECTED_FIRST, EXPECTED_LAST)

    print()
    for event_type, expected in EXPECTED.items():
        actual = counts.pop(event_type, 0)
        note = "" if actual == expected else f"   <-- expected {expected:,}"
        ok = ok and actual == expected
        print(f"{event_type:<18}{actual:>8,}{note}")
    for event_type, actual in counts.items():  # whatever is left was not expected at all
        ok = False
        print(f"{event_type!s:<18}{actual:>8,}   <-- unexpected event type")

    if ok:
        print("KATA OK")
    else:
        print("KATA MISMATCH: check the heap and time zone lines, then the download (docs/SETUP_SPARK.md steps 6-7).")
        sys.exit(1)


if __name__ == "__main__":
    main()
