"""Spot-check fact_event on five pinned events: the right price at event time.

    python checks/fact_event_spot.py

Run after processing/batch_warehouse.py. Reads what it wrote to data/warehouse/
(fact_event, dim_product, dim_event_type), and data/silver.

"The right price at event time" means three things, all true for every pinned
event (columns a, b and c):
  a  fact_event.price is the price on the event's own silver row, the price the
     shopper saw, and equals the pinned event price below;
  b  product_sk points at a version of the same product_id whose
     [valid_from, valid_to) contains event_date;
  c  that version's price is the product's end-of-day price in silver (the
     price at its last event_time that day, which must be one price), and
     equals the pinned version price below.
a and c together allow fact price != version price, and that is right: a
version lasts whole days and holds the end-of-day price, so an event earlier on
a day the price changed saw another price (677,255 events, 14.2%). The first
three pinned events are such cases; the last two come from product-days with
one price, where the two agree.

fact_event has no product_id. So an event is found in silver by
(product_id, event_time), then in fact_event by its (event_time, user_session,
event_type), which must match exactly one row in each: b is tested, not
assumed. Times are compared and printed as date_format text: collecting a raw
timestamp would shift it into the laptop's time zone (+7 here).
"""

import os
import sys
from decimal import Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
os.environ["SPARK_CONF_DIR"] = str(REPO / "conf")

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from processing.kata import check_environment

SILVER_DIR = REPO / "data" / "silver"
FACT_EVENT_DIR = REPO / "data" / "warehouse" / "fact_event"
DIM_PRODUCT_DIR = REPO / "data" / "warehouse" / "dim_product"
DIM_EVENT_TYPE_DIR = REPO / "data" / "warehouse" / "dim_event_type"
TIME = "yyyy-MM-dd HH:mm:ss"
DAY = "yyyy-MM-dd"

# product_id, event_time (Vietnam time, as in silver), the price on the event's
# own row, the price of the version in force. Measured on silver, not on
# fact_event, so the check does not grade the build with its own output.
PINNED = [
    (1005115, "2019-11-01 07:03:11", "949.47", "942.68"),    # 4 prices that day
    (1004237, "2019-11-01 07:00:27", "1091.33", "1080.72"),  # 4 prices that day
    (15100178, "2019-11-14 13:40:36", "1125.13", "82.63"),   # 2 prices; the next version holds 1125.13
    (1005115, "2019-11-29 00:00:05", "916.37", "916.37"),    # 1 price; the version spans 11-26 .. 11-30
    (1004856, "2019-12-01 00:00:08", "124.11", "124.11"),    # 1 price; the current version
]


def spot(silver, fact_event, versions, product_id, at, event_price, version_price):
    """One pinned event: its silver row, its fact row and its version, as printable values."""
    day = F.lit(at[:10]).cast("date")
    # Filter on event_date first, so Spark opens one date directory, not 31.
    silver_day = silver.where(F.col("event_date") == day)
    at_time = F.date_format("event_time", TIME) == at
    rows = (
        silver_day.where(at_time & (F.col("product_id") == product_id))
        .select("user_session", "event_type", "price")
        .collect()
    )
    if len(rows) != 1:
        sys.exit(f"{product_id} at {at}: {len(rows)} silver rows, expected 1. Pin another event.")
    session, event_type, silver_price = rows[0]

    same_event = at_time & (F.col("user_session") == session) & (F.col("event_type") == event_type)
    in_silver = silver_day.where(same_event).count()
    in_force = (F.col("event_date") >= F.col("valid_from")) & (F.col("event_date") < F.col("valid_to"))
    facts = (
        fact_event.where((F.col("event_date") == day) & same_event)
        .join(versions, "product_sk", "left")  # equi-join on the surrogate key
        .select(
            "price",
            "version_product_id",
            "version_price",
            F.concat_ws(" .. ", F.date_format("valid_from", DAY), F.date_format("valid_to", DAY)).alias("dates"),
            F.coalesce(in_force, F.lit(False)).alias("in_force"),
        )
        .collect()
    )
    if in_silver != 1:
        sys.exit(
            f"{product_id} at {at}: its (event_time, user_session, event_type) matches {in_silver} silver rows, "
            "expected 1. Pin another event."
        )
    if len(facts) != 1:
        # The pin is fine, so this is a fact_event defect: never re-pin around it.
        print(f"{product_id} at {at}: fact_event has {len(facts)} rows for this one silver event, expected 1.")
        print("FACT_EVENT SPOT FAILED")
        sys.exit(1)
    fact = facts[0]

    product_day = silver_day.where(F.col("product_id") == product_id)
    last = product_day.agg(F.max("event_time").alias("event_time"))
    day_end = [row["price"] for row in product_day.join(last, "event_time").select("price").distinct().collect()]
    if len(day_end) != 1:
        sys.exit(f"{product_id} on {at[:10]}: {len(day_end)} prices at the day's last event_time. Pin another event.")
    return {
        "product_id": product_id,
        "event_time": at,
        "event_type": event_type,
        "prices": product_day.select("price").distinct().count(),
        "silver": silver_price,
        "fact": fact["price"],
        "version": fact["version_price"],
        "day end": day_end[0],
        "dates": fact["dates"] or "no version",
        "a": fact["price"] == silver_price == Decimal(event_price),
        "b": fact["version_product_id"] == product_id and fact["in_force"],
        "c": fact["version_price"] == day_end[0] == Decimal(version_price),
    }


def report(results):
    print(f"{'product_id':>10}  {'event_time':<19}  {'type':<9}{'prices':>6}{'silver':>10}{'fact':>10}"
          f"{'version':>10}{'day end':>10}  {'version dates':<24}  a  b  c")
    for r in results:
        marks = "  ".join("Y" if r[must] else "N" for must in "abc")
        print(f"{r['product_id']:>10}  {r['event_time']:<19}  {r['event_type']:<9}{r['prices']:>6}"
              f"{r['silver']!s:>10}{r['fact']!s:>10}{r['version']!s:>10}{r['day end']!s:>10}  {r['dates']:<24}  {marks}")


def main():
    if not list(FACT_EVENT_DIR.glob("event_date=*")) or not DIM_PRODUCT_DIR.exists() or not DIM_EVENT_TYPE_DIR.exists():
        sys.exit("fact_event, dim_product or dim_event_type is missing under data/warehouse/. "
                 "Run python processing/batch_warehouse.py first.")
    spark = SparkSession.builder.master("local[*]").appName("fact_event_spot").getOrCreate()
    try:
        # to_date(), date_format() and the date literals read the session time zone.
        if not check_environment(spark):
            sys.exit("conf/spark-defaults.conf was not read: see the heap and time zone lines above.")
        silver = spark.read.parquet(str(SILVER_DIR))
        event_types = spark.read.parquet(str(DIM_EVENT_TYPE_DIR)).select(
            "event_type_key", F.col("event_type_code").alias("event_type")
        )
        fact_event = spark.read.parquet(str(FACT_EVENT_DIR)).join(event_types, "event_type_key")
        versions = spark.read.parquet(str(DIM_PRODUCT_DIR)).select(
            "product_sk",
            F.col("product_id").alias("version_product_id"),
            F.col("price").alias("version_price"),
            "valid_from",
            "valid_to",
        )
        results = [spot(silver, fact_event, versions, *pinned) for pinned in PINNED]
    finally:
        spark.stop()
    print()
    report(results)
    if not all(r["a"] and r["b"] and r["c"] for r in results):
        print("FACT_EVENT SPOT FAILED")
        sys.exit(1)
    print("FACT_EVENT SPOT OK")


if __name__ == "__main__":
    main()
