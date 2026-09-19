"""Silver: bronze cleaned and moved to Vietnam time, as Parquet.

SILVER HAS EXACTLY ONE WRITER: THIS FILE. The W40 streaming job
(streaming_gold.py) must never write to data/silver/, not even "just the new
events". A second writer breaks silver in one of two ways:
- A Parquet file sink creates data/silver/_spark_metadata/. From then on Spark
  reads only the files listed in it, so everything this script wrote is
  invisible to Spark while DuckDB still globs the whole directory. The two
  engines then disagree about the same path.
- A foreachBatch write duplicates rows. The replayer replays bronze, and this
  script has already turned bronze into silver, so from the second demo run on
  BR2, BR4 and BR7 count everything twice.
The stream imports clean() from this file to apply the same rules, and writes
only to Cassandra. SYSTEM_DESIGN.md section 8 has the full argument.

    python processing/batch_silver.py

Reads data/bronze/ (written by load_bronze.py), applies the seven rules in
clean(), and writes data/silver/: one directory per event_date, and inside it
one per event_type:

    data/silver/event_date=2019-11-29/event_type=purchase/part-....parquet

Most queries want one event type on a few days. With this layout Spark skips
the other directories without opening a file (partition pruning).

The seven rules (SYSTEM_DESIGN.md section 4):

1. Drop price <= 0 (12,996 rows of bronze).
2. Drop a null user_id (none in bronze, but the stream reads the same shape).
3. Split category_code, e.g. "electronics.smartphone", into category_l1/l2/l3.
4. Fill a missing category_l1/l2/l3 with 'unknown'. This is not cosmetic.
   category_code is empty in 32.4% of the raw file (21,898,171 of 67,501,979
   rows). category_l1 is half the partition key of BR1's gmv_by_minute, and
   Cassandra rejects a null partition-key part. Without the fill, one BR1
   insert in three fails and GMV comes out a third short.
5. Fill a missing brand with 'unknown'.
6. Shift event_time from UTC to Vietnam time (UTC+7), AND recompute event_date
   from the shifted time. Bronze's event_date is the UTC date. Keeping it files
   every event between 17:00 and 24:00 UTC under the wrong day, which skews
   BR1, BR2 and BR6.
7. Drop a null user_session (one cart event in bronze). fact_event needs it NOT
   NULL, and it is the clustering key of BR5's abandoned_carts in Cassandra.

Why 31 date directories and not 30: the file ends at 30 Nov 23:59 UTC, which is
1 Dec 06:59 in Vietnam. The 25,859 events of 30 Nov 17:00-24:00 UTC belong to
1 Dec, a partial day, just as 1 Nov starts at 07:00. In bronze, 31 directories
means a wrong time zone. In silver, 31 is correct, and 30 means rule 6 is
missing.

Done when the script prints SILVER OK. Every machine must print exactly these
numbers (Spark 4.1.3, measured):

    rows                         4,754,015   (bronze 4,767,012, 12,997 dropped)
    users                          258,330
    products                       128,972
    category_l1 'unknown'        1,534,249
    category_l2 'unknown'        1,534,249
    category_l3 'unknown'        3,428,388
    brand 'unknown'                634,202
    null values                          0   (expect 0; only category_code may be null)
    price <= 0                           0   (expect 0)
    event_date wrong                     0   (expect 0: the Vietnam date of event_time)
    event_date range     2019-11-01 .. 2019-12-01   (expect 2019-11-01 .. 2019-12-01)
    rows on 2019-12-01              25,859   (30 Nov 17:00-24:00 UTC)
    event_time range     2019-11-01 07:00:02 .. 2019-12-01 06:59:49   (expect the same)
    directories          31 dates, 93 date/type   (expect 31 and 93)

If they differ, check first that load_bronze.py printed BRONZE OK on this
machine, then look for local edits with git status and git diff on processing/
and conf/.
"""

import os
import sys
import time
from pathlib import Path

# The same three lines open every Spark script in this repo (see processing/kata.py).
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))  # lets `python processing/batch_silver.py` find the repo root
os.environ["SPARK_CONF_DIR"] = str(REPO / "conf")  # driver memory + UTC, before the JVM starts

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

BRONZE_DIR = REPO / "data" / "bronze"
SILVER_DIR = REPO / "data" / "silver"

VIETNAM = "Asia/Ho_Chi_Minh"  # UTC+7 all year: Vietnam has no daylight saving time
UNKNOWN = "unknown"

# Silver's columns, in this order. event_date and event_type end up as directory
# names, not columns inside the files; Spark adds them back when it reads silver.
# category_code stays as it came, null included: dim_product keeps it, and it is
# the only place the fourth level of "electronics.audio.music_tools.piano" survives.
SILVER_COLUMNS = [
    "event_time", "event_type", "product_id", "category_id", "category_code",
    "category_l1", "category_l2", "category_l3", "brand", "price",
    "user_id", "user_session", "event_date",
]

# What every machine must get, exactly (measured on bronze with Spark 4.1.3).
BRONZE_ROWS = 4_767_012
EXPECTED = {
    "rows": 4_754_015,
    "users": 258_330,
    "products": 128_972,
    "category_l1 'unknown'": 1_534_249,
    "category_l2 'unknown'": 1_534_249,
    "category_l3 'unknown'": 3_428_388,
    "brand 'unknown'": 634_202,
}
EXPECTED_FIRST_DATE = "2019-11-01"
EXPECTED_LAST_DATE = "2019-12-01"   # the last Vietnam date: see "Why 31" above
EXPECTED_LAST_DAY_ROWS = 25_859
EXPECTED_TIMES = ("2019-11-01 07:00:02", "2019-12-01 06:59:49")  # first and last event, Vietnam time
EXPECTED_DATE_DIRS = 31
EXPECTED_TYPE_DIRS = 93             # 31 dates x view, cart, purchase


def read_bronze(spark):
    """All of bronze. Parquet carries its own schema, so none is passed here.

    Spark adds bronze's event_date back from the directory names. It is the UTC
    date, and clean() replaces it.
    """
    return spark.read.parquet(str(BRONZE_DIR))


def clean(events):
    """Apply the seven silver rules. Takes and returns a DataFrame; no I/O.

    Every step works row by row, so this also runs on a streaming DataFrame:
    the W40 streaming job imports this function instead of copying the rules,
    and so cannot forget one (SYSTEM_DESIGN.md section 8, step 7). Importing it
    does not make the stream a silver writer.
    """
    # Rule 6 is right only in a UTC session: to_date() reads a time in the
    # session time zone. A script that skipped the SPARK_CONF_DIR line runs in
    # the laptop's zone (UTC+7 here), where to_date() adds another 7 hours and
    # files every event of 10:00-17:00 UTC under the next day, without any
    # error. Stop it here instead.
    time_zone = events.sparkSession.conf.get("spark.sql.session.timeZone")
    if time_zone != "UTC":
        raise RuntimeError(f"clean() needs a UTC Spark session, got {time_zone}: set "
                           "SPARK_CONF_DIR to conf/ before the SparkSession starts")
    # 3. "electronics.smartphone" -> ["electronics", "smartphone"]. split() takes
    # a regular expression, so the dot is escaped. A null category_code gives a
    # null array.
    parts = F.split("category_code", r"\.")
    return (
        events
        # 1. A price of zero or less is not a real sale. `price > 0` also drops
        # a null price (none in bronze).
        .where(F.col("price") > 0)
        # 2. Every event must belong to a user.
        .where(F.col("user_id").isNotNull())
        # 7. Every event must belong to a session (one row in bronze does not).
        .where(F.col("user_session").isNotNull())
        # 3 and 4. get() and never getItem() or parts[2]: Spark 4 runs in ANSI
        # mode, where getItem(2) on a two-level code stops the whole job with
        # INVALID_ARRAY_INDEX. get() returns null instead, and coalesce turns
        # that null into 'unknown'.
        .withColumn("category_l1", F.coalesce(F.get(parts, 0), F.lit(UNKNOWN)))
        .withColumn("category_l2", F.coalesce(F.get(parts, 1), F.lit(UNKNOWN)))
        .withColumn("category_l3", F.coalesce(F.get(parts, 2), F.lit(UNKNOWN)))
        # 5.
        .withColumn("brand", F.coalesce(F.col("brand"), F.lit(UNKNOWN)))
        # 6. First shift the time, then take the date of the SHIFTED time. The
        # session time zone is UTC (conf/spark-defaults.conf), so to_date() of
        # the shifted value is the Vietnam date. 30 Nov 20:00 UTC becomes
        # 1 Dec 03:00 and is filed under 2019-12-01.
        .withColumn("event_time", F.from_utc_timestamp("event_time", VIETNAM))
        .withColumn("event_date", F.to_date("event_time"))
        .select(*SILVER_COLUMNS)
    )


def write_silver(events):
    """Write Parquet: data/silver/event_date=.../event_type=.../part-....parquet"""
    try:
        (
            events
            # One file per directory, 93 in all, on every machine. Without this,
            # each of bronze's 97 files writes its own small file into every
            # directory it touches (about 580 files), and the "partitions read"
            # each screen shows would depend on how bronze happened to be split.
            .repartition("event_date", "event_type")
            .write
            .mode("overwrite")          # a re-run replaces silver, never appends a second copy
            .partitionBy("event_date", "event_type")
            .parquet(str(SILVER_DIR))
        )
    finally:
        # "overwrite" deletes the whole directory first, including the .gitkeep
        # that git tracks so a fresh clone has data/silver/. Put it back, even
        # when the write fails halfway.
        SILVER_DIR.mkdir(parents=True, exist_ok=True)
        (SILVER_DIR / ".gitkeep").touch()


def report(spark):
    """Read silver back from disk, print what is really there, return True if it passes."""
    silver = spark.read.parquet(str(SILVER_DIR))
    # category_code is the one column allowed to stay null: rule 4 fills the
    # three levels split from it, not the original.
    any_null = F.lit(False)
    for column in silver.columns:
        if column != "category_code":
            any_null = any_null | F.col(column).isNull()
    stats = silver.agg(
        F.count("*").alias("rows"),
        F.countDistinct("user_id").alias("users"),
        F.countDistinct("product_id").alias("products"),
        F.count_if(F.col("category_l1") == UNKNOWN).alias("category_l1 'unknown'"),
        F.count_if(F.col("category_l2") == UNKNOWN).alias("category_l2 'unknown'"),
        F.count_if(F.col("category_l3") == UNKNOWN).alias("category_l3 'unknown'"),
        F.count_if(F.col("brand") == UNKNOWN).alias("brand 'unknown'"),
        F.count_if(any_null).alias("null"),
        F.count_if(F.col("price") <= 0).alias("price_le_0"),
        F.count_if(F.col("event_date") != F.to_date("event_time")).alias("wrong_date"),
        F.min("event_date").cast("string").alias("first_date"),
        F.max("event_date").cast("string").alias("last_date"),
        F.count_if(F.col("event_date") == F.lit(EXPECTED_LAST_DATE).cast("date")).alias("last_day_rows"),
        # date_format renders in the session time zone (UTC) and returns text,
        # so this is the shifted Vietnam wall-clock time, exactly as stored.
        F.date_format(F.min("event_time"), "yyyy-MM-dd HH:mm:ss").alias("first_time"),
        F.date_format(F.max("event_time"), "yyyy-MM-dd HH:mm:ss").alias("last_time"),
    ).first()
    date_dirs = len(list(SILVER_DIR.glob("event_date=*")))
    type_dirs = len(list(SILVER_DIR.glob("event_date=*/event_type=*")))

    print()
    ok = True
    for name, expected in EXPECTED.items():
        note = "" if stats[name] == expected else f"   <-- expected {expected:,}"
        ok = ok and stats[name] == expected
        extra = f"   (bronze {BRONZE_ROWS:,}, {BRONZE_ROWS - stats[name]:,} dropped)" if name == "rows" else ""
        print(f"{name:<22}{stats[name]:>13,}{note}{extra}")
    print(f"{'null values':<22}{stats['null']:>13,}   (expect 0; only category_code may be null)")
    print(f"{'price <= 0':<22}{stats['price_le_0']:>13,}   (expect 0)")
    print(f"{'event_date wrong':<22}{stats['wrong_date']:>13,}   (expect 0: the Vietnam date of event_time)")
    print(f"{'event_date range':<22}{stats['first_date']} .. {stats['last_date']}"
          f"   (expect {EXPECTED_FIRST_DATE} .. {EXPECTED_LAST_DATE})")
    print(f"{'rows on ' + EXPECTED_LAST_DATE:<22}{stats['last_day_rows']:>13,}"
          f"   (expect {EXPECTED_LAST_DAY_ROWS:,}: 30 Nov 17:00-24:00 UTC)")
    print(f"{'event_time range':<22}{stats['first_time']} .. {stats['last_time']}"
          f"   (expect {EXPECTED_TIMES[0]} .. {EXPECTED_TIMES[1]})")
    print(f"{'directories':<22}{date_dirs} dates, {type_dirs} date/type"
          f"   (expect {EXPECTED_DATE_DIRS} and {EXPECTED_TYPE_DIRS})")

    return (
        ok
        and stats["null"] == 0
        and stats["price_le_0"] == 0
        and stats["wrong_date"] == 0
        and (stats["first_date"], stats["last_date"]) == (EXPECTED_FIRST_DATE, EXPECTED_LAST_DATE)
        and stats["last_day_rows"] == EXPECTED_LAST_DAY_ROWS
        and (stats["first_time"], stats["last_time"]) == EXPECTED_TIMES
        and (date_dirs, type_dirs) == (EXPECTED_DATE_DIRS, EXPECTED_TYPE_DIRS)
    )


def main():
    # Check before the write deletes the old silver.
    if not list(BRONZE_DIR.glob("event_date=*")):
        sys.exit(f"{BRONZE_DIR} is empty. Run python ingestion/load_bronze.py first.")

    started = time.monotonic()
    spark = SparkSession.builder.master("local[*]").appName("batch_silver").getOrCreate()

    write_silver(clean(read_bronze(spark)))
    ok = report(spark)
    spark.stop()

    print(f"{'took':<22}{time.monotonic() - started:>13.0f} s")
    if ok:
        print("SILVER OK")
    else:
        print("SILVER CHECK FAILED: see the lines above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
