"""Warehouse: silver -> the star schema, as Parquet (SYSTEM_DESIGN.md section 5).

    python processing/batch_warehouse.py

Six of the nine tables are built: dim_event_type, dim_product,
stg_rfm_snapshot, dim_user, fact_event and fact_session_funnel. The other
build_* functions are still stubs that return None, and each of those prints
"not built yet". Each owner replaces the BODY of their own function and keeps
its signature. Nobody writes Parquet directly: every table goes through
write_dim() or write_fact(), so all nine tables land the same way.

The build order is forced (SYSTEM_DESIGN.md 5.6), and main() runs it top to
bottom:

    step  table                          owner    input
    1     dim_date                       Tin      seed/holidays_2019.csv
    1     dim_event_type                 Tin      -
    1     dim_warehouse                  Tin      -
    2     dim_product (SCD2 on price)    Nguyen   silver + data/catalog/products.json
    3     stg_rfm_snapshot               Khang    silver
    4     dim_user (SCD2 on RFM cell)    Khang    stg_rfm_snapshot
    5     fact_event                     Dat      the events, keys already on them
    5     fact_session_funnel            Dat      the events, keys already on them
    5     fact_inventory_daily           W40      data/inventory/ + dim_product
    6     load Postgres                  Tin      the tables written above

Step 3 exists to break a cycle: dim_user is Type 2 on the RFM segment, RFM is
BR4, and BR4's gold reads the star. So RFM is computed here, on natural keys,
before any fact.

NEVER RANGE-JOIN A FACT TO AN SCD2 DIMENSION. The textbook lookup
    ON f.product_id = d.product_id AND f.event_time BETWEEN d.valid_from AND d.valid_to
produced 305,663,175 intermediate rows, 65 times the fact table, a quarter of
them from one product (1005115), and AQE cannot split a single skewed key. So
the surrogate keys travel on the event rows instead:
- build_dim_product() returns (dim_product, events). The events are silver with
  product_sk added in the same window pass that detects the price change.
- build_dim_user() returns (dim_user, events). It adds user_sk the same way.
- build_fact_event() then selects columns and broadcast-joins the five-row
  dim_event_type. It never joins an SCD2 dimension.

Memory: the driver heap is set in conf/spark-defaults.conf and nowhere else.
Setting it on SparkSession.builder works only when that builder starts the JVM;
once a JVM runs it is ignored, silently after a stop(). An executor memory
setting does nothing in local[*], where the driver is the only executor.
check_environment() prints the heap the JVM really got.

Done when the script prints WAREHOUSE OK, with all nine tables built. Until
then it prints WAREHOUSE PARTIAL and says how many are built. Today it prints
(Spark 4.1.3, measured, about 60 s):

    dim_date                 not built yet
    dim_event_type                       5
    dim_warehouse            not built yet
    dim_product                    210,454
    stg_rfm_snapshot             1,291,650   (5 snapshot_date directories)
    dim_user                       319,426
    fact_event                   4,754,015   (31 event_date directories)
    fact_session_funnel            970,797   (31 session_start_date directories)
    fact_inventory_daily     not built yet

    fact_event rows              4,754,015   (expect 4,754,015)
    ...                                      (19 more check lines, each at its expect)
    most events in one day         482,049   (event_sk has room for 9,999,999)
    price != version price         677,255   (14.2%, versions are per day: not an error)

    fact_session_funnel rows       970,797   (expect 970,797)
    null values                          0   (expect 0)
    duplicate session_sk                 0   (expect 0)
    session_start_date wrong             0   (expect 0)
    ck_fsf_stage violated                0   (expect 0)
    ck_fsf_lags violated                 0   (expect 0)
    view_count total             4,474,579   (expect 4,474,579)
    cart_count total               214,286   (expect 214,286)
    purchase_count total            65,150   (expect 65,150)
    cart_value total         62,570,985.31   (expect 62,570,985.31)
    purchase_value total     19,785,531.43   (expect 19,785,531.43)
    user_sk not in force                 0   (expect 0)
    funnel_stage 1 / 2 / 3         838,795 / 77,098 / 54,904
    is_abandoned                    77,098   (a cart, no purchase: funnel_stage 2)
    negative lags                      521 / 448   (view->cart / cart->purchase, kept as measured)

    stg_rfm_snapshot             1,291,650   (expect 1,291,650)
    dim_user versions              319,426   (expect 258,330 to 1,291,650)
    ...                                      (9 more check lines on dim_user, each at its expect)
    postgres                 not loaded yet (step 6: Tin, W40)
    WAREHOUSE PARTIAL: 6 of 9 tables built
"""

import os
import sys
import time
from pathlib import Path

# The same three lines open every Spark script in this repo (see processing/kata.py).
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))  # lets `python processing/batch_warehouse.py` find the repo root
os.environ["SPARK_CONF_DIR"] = str(REPO / "conf")  # driver memory + UTC, before the JVM starts

from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F

import processing.dim_product as product_scd2  # Nguyen's step 2, under an alias: see the steps 2-4 comment
import processing.dim_user as user_scd2  # Khang's steps 3-4, likewise
from processing.batch_silver import EXPECTED as SILVER_EXPECTED
from processing.batch_silver import EXPECTED_DATE_DIRS
from processing.kata import check_environment
from processing.schema import EVENT_SCHEMA
from serving.load_star_postgres import DIM_EVENT_TYPE_ROWS  # Tin's five rows: imported, never copied

SILVER_DIR = REPO / "data" / "silver"

# One directory per table. Never write to WAREHOUSE_DIR itself: an overwrite
# there would delete the .gitkeep that git tracks. write_dim() and write_fact()
# refuse any other path.
WAREHOUSE_DIR = REPO / "data" / "warehouse"
DIM_DATE_DIR = WAREHOUSE_DIR / "dim_date"
DIM_EVENT_TYPE_DIR = WAREHOUSE_DIR / "dim_event_type"
DIM_WAREHOUSE_DIR = WAREHOUSE_DIR / "dim_warehouse"
DIM_PRODUCT_DIR = WAREHOUSE_DIR / "dim_product"            # same path as processing/dim_product.py
STG_RFM_SNAPSHOT_DIR = WAREHOUSE_DIR / "stg_rfm_snapshot"  # same path as processing/dim_user.py
DIM_USER_DIR = WAREHOUSE_DIR / "dim_user"                  # same path as processing/dim_user.py
FACT_EVENT_DIR = WAREHOUSE_DIR / "fact_event"
FACT_SESSION_FUNNEL_DIR = WAREHOUSE_DIR / "fact_session_funnel"
FACT_INVENTORY_DAILY_DIR = WAREHOUSE_DIR / "fact_inventory_daily"


def check_silver_types(silver):
    """Stop unless silver's nine event columns have the types in processing/schema.py.

    Silver's own Parquet schema is what Spark reads, so EVENT_SCHEMA is not
    passed to the reader; it is the yardstick. A silver written by an older
    batch_silver.py still loads, but a user_id read as INT breaks
    user_sk = user_id * 10 + version_no, and a price as DOUBLE no longer matches
    the star's numeric(10,2).
    """
    actual = {field.name: field.dataType for field in silver.schema.fields}
    wrong = [
        f"{field.name}: {actual.get(field.name)} (expected {field.dataType})"
        for field in EVENT_SCHEMA.fields
        if actual.get(field.name) != field.dataType
    ]
    if wrong:
        sys.exit(
            "silver does not match processing/schema.py:\n  " + "\n  ".join(wrong)
            + "\nRe-run python processing/batch_silver.py; nothing was overwritten."
        )


def read_silver(spark):
    """All of silver, checked before any table is overwritten.

    Spark adds event_date and event_type back from the directory names.
    """
    silver = spark.read.parquet(str(SILVER_DIR))
    check_silver_types(silver)
    rows = silver.count()
    if rows != SILVER_EXPECTED["rows"]:
        sys.exit(
            f"silver has {rows:,} rows, expected {SILVER_EXPECTED['rows']:,}. "
            "Re-run python processing/batch_silver.py; nothing was overwritten."
        )
    print(f"{'silver':<25}{rows:>13,}   (EVENT_SCHEMA types OK)")
    return silver


# ---------------------------------------------------------------------------
# Step 1: three small dimensions, no dependencies. Owner: Tin.
# Their rows already exist in serving/load_star_postgres.py. Import them there,
# never copy: build_dim_date_rows(), DIM_EVENT_TYPE_ROWS, DIM_WAREHOUSE_ROWS.
# createDataFrame() reads Python ints as bigint and sorts a dict's keys
# alphabetically, so select warehouse/ddl.sql's columns in its order and cast
# to its smallint and integer types, as build_dim_event_type() does.
# ---------------------------------------------------------------------------

def build_dim_date(spark):
    """dim_date: one row per day, 2019-10-01 .. 2019-12-31 (92 rows), is_holiday from seed/.

    Columns and types: warehouse/ddl.sql, dim_date. Stub: returns None.
    """
    return None


def build_dim_event_type(spark):
    """dim_event_type: the five rows, keys 1, 2, 3, 4 and -1 (unknown).

    Columns and types: warehouse/ddl.sql, dim_event_type. build_fact_event()
    takes its event_type_key from this table.
    """
    return spark.createDataFrame(DIM_EVENT_TYPE_ROWS).select(
        F.col("event_type_key").cast("smallint").alias("event_type_key"),
        "event_type_code",
        "event_type_name",
        F.col("stage_rank").cast("smallint").alias("stage_rank"),
        "is_funnel_stage",
        "is_conversion",
        F.col("cart_value_sign").cast("smallint").alias("cart_value_sign"),
    )


def build_dim_warehouse(spark):
    """dim_warehouse: the five warehouses, warehouse_id 1..5.

    Columns and types: warehouse/ddl.sql, dim_warehouse. Stub: returns None.
    """
    return None


# ---------------------------------------------------------------------------
# Steps 2-4: the two SCD2 dimensions. Each returns (dim, events): the dimension
# to write, and the event rows with its surrogate key added. Wired in with an
# import and a call, never a copy:
#   step 2: processing/dim_product.py   assign_versions, build_dim_product
#   steps 3-4: processing/dim_user.py   build_rfm_snapshot, build_dim_user, with_user_sk
# The MODULE is imported under an alias, at the top of this file:
#   import processing.dim_product as product_scd2
#   import processing.dim_user as user_scd2
# and called as product_scd2.build_dim_product(...), user_scd2.build_dim_user(...).
# Never `from processing.dim_user import build_dim_user`: the function below has
# the same name, its def runs after the import and replaces it, and it then
# calls itself. Not `from processing import dim_user` either: main() has a
# local variable called dim_user.
# ---------------------------------------------------------------------------

def build_dim_product(silver):
    """Step 2, owner Nguyen. Returns (dim_product, events).

    events: every silver column plus product_sk, assigned in the same window
    pass that detects the price change (all columns: fact_event needs user_id,
    user_session and event_type too). dim_product: warehouse/ddl.sql, one row per
    product version, valid_to exclusive, 9999-12-31 when current. A version is a
    run of days with the same end-of-day price, so an event earlier on a day the
    price changed saw another price than its version holds.
    """
    # Full silver. Never product_scd2.read_silver_events(): it keeps nine
    # columns and drops user_id, user_session and event_type.
    events = product_scd2.assign_versions(silver)
    dim_product = product_scd2.build_dim_product(events, product_scd2.read_catalog(silver.sparkSession))
    # build_dim_product() has used the product's version_no; dim_user has a
    # version_no of its own, so a later join of events to dim_user would find two.
    return dim_product, events.drop("version_no")


def build_stg_rfm_snapshot(silver):
    """Step 3, owner Khang. R, F and M per user per snapshot date, on natural keys.

    Written through write_fact() partitioned by snapshot_date, the layout
    processing/dim_user.py uses.
    """
    return user_scd2.build_rfm_snapshot(silver)


def build_dim_user(stg_rfm_snapshot, events):
    """Step 4, owner Khang. Returns (dim_user, events).

    stg_rfm_snapshot is the copy read back from disk, as in processing/dim_user.py.
    events gains user_sk, the version in force on each event's date: an
    equi-join on (user_id, snapshot_date), never a range join.
    """
    return user_scd2.build_dim_user(stg_rfm_snapshot), user_scd2.with_user_sk(events, stg_rfm_snapshot)


# ---------------------------------------------------------------------------
# Step 5: the three facts, one per Kimball type (SYSTEM_DESIGN.md 5.2 and 5.5).
# ---------------------------------------------------------------------------

# event_sk = date_key * EVENT_SK_SLOTS + the event's position in its day, so
# event_sk div EVENT_SK_SLOTS is its date_key. The busiest day, 2019-11-17, has
# 482,049 events, far below this.
EVENT_SK_SLOTS = 10_000_000


def build_fact_event(events, dim_event_type):
    """Transaction fact, owner Dat. One row per silver event, 1:1 with silver.

    Selects the surrogate keys already on the event rows, adds event_sk,
    date_key and event_type_key. Columns: warehouse/ddl.sql, fact_event, in its
    order (read back, event_date comes last: it is the directory name, and Spark
    appends partition columns). No dropDuplicates: silver keeps 7,312 rows that repeat another row in
    every column, and each one is an event of its own.
    """
    # The position in the day orders by these four columns. Rows that tie on
    # all four are identical in every column (measured: 4,169 groups, none that
    # differ), so whichever gets which position, the fact holds the same rows
    # on all four machines; check_fact_event() counts ties that differ. Not a
    # content hash: two identical rows would get the same key. Not
    # monotonically_increasing_id(): it follows how the files were split.
    in_day = Window.partitionBy("event_date").orderBy("event_time", "user_session", "product_id", "event_type")
    # Five rows, so broadcast: every task gets its own copy, nothing is shuffled.
    event_types = F.broadcast(dim_event_type.select(F.col("event_type_code").alias("event_type"), "event_type_key"))
    return (
        events.join(event_types, "event_type", "left")
        .withColumn("date_key", F.date_format("event_date", "yyyyMMdd").cast("int"))  # dim_date's key, e.g. 20191129
        # bigint BEFORE the multiply: 20191101 * 10,000,000 does not fit an int,
        # and Spark's ANSI mode stops the job instead of wrapping around.
        .withColumn("event_sk", F.col("date_key").cast("bigint") * EVENT_SK_SLOTS + F.row_number().over(in_day))
        .select(
            "event_sk",
            F.col("product_sk").cast("bigint").alias("product_sk"),  # processing/dim_product.py makes it an int
            F.col("user_sk").cast("bigint").alias("user_sk"),
            "event_time",  # silver already shifted it to Vietnam time: no second shift
            "user_session",
            "price",
            "date_key",
            "event_date",
            F.coalesce("event_type_key", F.lit(-1)).cast("smallint").alias("event_type_key"),  # -1: unknown
        )
    )


def build_fact_session_funnel(events):
    """Accumulating snapshot, owner Dat. One row per session, 1:1 with silver's user_session.

    Kimball's accumulating snapshot: one row per run of a process, one timestamp
    per milestone, NULL until the milestone is reached. Here the process is a
    session's funnel and the milestones are first_view_at, first_cart_at and
    purchase_at (the first purchase). Plain Parquet cannot update a row in
    place, so every run recomputes the whole table from all events and
    overwrites it; it is never updated incrementally (SYSTEM_DESIGN.md section 8).

    The groupBy on user_session is this function's only shuffle, and it joins
    nothing; events is a plan, so writing the table re-runs steps 2-4 under it.
    user_sk, user_id and the start date come from the session's first event,
    where step 4 already put user_sk, so user_sk is the version in force on
    session_start_date. Never range-join dim_user for it (see the module docstring).
    is_abandoned: a cart and no purchase anywhere in the session. BR5's
    streaming rule (no purchase in the 30 minutes after the cart) disagrees on
    498 sessions, 0.6% of the 77,098 abandoned ones, mostly purchases that came
    later than 30 minutes. cart_value ignores remove_from_cart
    (cart_value_sign -1): the source has none. A lag is negative when the later
    milestone came first, and is kept that way. Columns: warehouse/ddl.sql,
    fact_session_funnel, in its order (read back, session_start_date comes last).
    """
    is_view = F.col("event_type") == "view"
    is_cart = F.col("event_type") == "cart"
    is_purchase = F.col("event_type") == "purchase"
    sessions = events.groupBy("user_session").agg(
        # min() of a struct compares field by field: the earliest event, and on a
        # tie the lowest user_sk, so all four machines pick the same row.
        F.min(F.struct("event_time", "user_sk", "user_id", "event_date")).alias("first_event"),
        F.min(F.when(is_view, F.col("event_time"))).alias("first_view_at"),
        F.min(F.when(is_cart, F.col("event_time"))).alias("first_cart_at"),
        F.min(F.when(is_purchase, F.col("event_time"))).alias("purchase_at"),
        F.max("event_time").alias("last_event_at"),
        F.count_if(is_view).alias("view_count"),
        F.count_if(is_cart).alias("cart_count"),
        F.count_if(is_purchase).alias("purchase_count"),
        F.sum(F.when(is_cart, F.col("price"))).alias("cart_value"),
        F.sum(F.when(is_purchase, F.col("price"))).alias("purchase_value"),
    )

    def seconds(start, end):
        # NULL when either end is NULL, which is what ck_fsf_lags demands.
        return (F.unix_seconds(end) - F.unix_seconds(start)).cast("int")

    return sessions.select(
        F.xxhash64("user_session").alias("session_sk"),
        "user_session",
        F.col("first_event.user_sk").cast("bigint").alias("user_sk"),
        F.col("first_event.user_id").alias("user_id"),
        F.col("first_event.event_date").alias("session_start_date"),  # silver's Vietnam date
        F.col("first_event.event_time").alias("session_start_at"),
        "first_view_at",
        "first_cart_at",
        "purchase_at",
        "last_event_at",
        seconds("first_view_at", "first_cart_at").alias("view_to_cart_sec"),
        seconds("first_cart_at", "purchase_at").alias("cart_to_purchase_sec"),
        F.col("view_count").cast("int").alias("view_count"),
        F.col("cart_count").cast("int").alias("cart_count"),
        F.col("purchase_count").cast("int").alias("purchase_count"),
        F.coalesce("cart_value", F.lit(0)).cast("decimal(12,2)").alias("cart_value"),  # NOT NULL in ddl.sql
        F.coalesce("purchase_value", F.lit(0)).cast("decimal(12,2)").alias("purchase_value"),
        # The furthest milestone, from the counts. check_fact_session_funnel() tests
        # it against ddl.sql's CASE on the timestamps.
        F.when(F.col("purchase_count") > 0, 3)
        .when(F.col("cart_count") > 0, 2)
        .when(F.col("view_count") > 0, 1)
        .otherwise(0)
        .cast("smallint")
        .alias("funnel_stage"),
        (F.col("first_cart_at").isNotNull() & F.col("purchase_at").isNull()).alias("is_abandoned"),
    )


def build_fact_inventory_daily(spark, dim_product, dim_warehouse):
    """Periodic snapshot, W40. One row per SKU x warehouse x day, from data/inventory/.

    product_sk is the version in force on snapshot_date. No event rows carry it
    here, and the range join is banned here too (see the module docstring). So
    expand each dim_product version into one row per day it covers,
    sequence(valid_from, valid_to - 1) clipped to the inventory dates, and
    equi-join on (product_id, snapshot_date). A product has no version before
    its first event day, yet product_sk is NOT NULL: decide that case
    explicitly. Columns: warehouse/ddl.sql, fact_inventory_daily.
    Stub: returns None.
    """
    return None


# ---------------------------------------------------------------------------
# Checks. Each runs on the tables read back from disk, prints one line per
# count and returns True when every count is what it should be; main() folds
# it into checks_ok.
# ---------------------------------------------------------------------------

# fact_event rows per event_type_key: view, cart, purchase, and none unknown
# (-1). The three add up to silver's 4,754,015.
EXPECTED_EVENT_TYPE_ROWS = {1: 4_474_579, 2: 214_286, 3: 65_150, -1: 0}
# The silver columns fact_event keeps, directly or through a dimension's key.
COMPARED_WITH_SILVER = ["event_date", "event_time", "user_session", "product_id", "user_id", "event_type", "price"]


def check_fact_event(fact_event, silver, events, dim_event_type, dim_product, dim_user):
    """fact_event against silver and the two SCD2 dimensions.

    fact_event and the three dimensions are the copies read back from disk,
    so most counts test the files written. Two test the events plan from steps
    2-4 instead, computed again here, which still carries product_id and
    user_id: "events on wrong product" and user_scd2.check_events(). Every
    version check is an equi-join on the unique surrogate key, then a filter on
    the dates. That is not the banned range join: each row meets exactly one
    version row.
    """
    any_null = F.lit(False)
    for column in fact_event.columns:
        any_null = any_null | F.col(column).isNull()
    stats = (
        fact_event.agg(
            F.count("*").alias("fact_event rows"),
            F.count_distinct("event_date").alias("event_date values"),
            F.count_if(any_null).alias("null values"),
            (F.count("*") - F.count_distinct("event_sk")).alias("duplicate event_sk"),
            F.count_if(F.expr(f"event_sk div {EVENT_SK_SLOTS}") != F.col("date_key")).alias("event_sk on another day"),
            F.count_if(F.col("date_key") != F.date_format("event_date", "yyyyMMdd").cast("int"))
            .alias("date_key wrong"),
            F.count_if(F.col("event_date") != F.to_date("event_time")).alias("event_date wrong"),  # ddl ck_fact_date
            F.count_if(F.col("price") <= 0).alias("price <= 0"),  # ddl ck_fact_price
            F.max(F.col("event_sk") % EVENT_SK_SLOTS).alias("most events in one day"),
        )
        .first()
        .asDict()
    )
    by_type = {row["event_type_key"]: row["count"] for row in fact_event.groupBy("event_type_key").count().collect()}
    for key in EXPECTED_EVENT_TYPE_ROWS:
        stats[f"event_type_key {key}"] = by_type.get(key, 0)

    # event_sk is the same on every machine only if rows that tie on its four
    # order columns are identical in the fact. Within one day product_sk stands
    # for product_id, and event_type_key for event_type.
    stats["event_sk ties that differ"] = (
        fact_event.groupBy("event_date", "event_time", "user_session", "product_sk", "event_type_key")
        .agg(F.count_distinct("price", "user_sk").alias("variants"))
        .where(F.col("variants") > 1)
        .count()
    )

    versions = dim_product.select(
        "product_sk",
        F.col("product_id").alias("version_product_id"),
        F.col("price").alias("version_price"),
        "valid_from",
        "valid_to",
    )
    in_force = (F.col("event_date") >= F.col("valid_from")) & (F.col("event_date") < F.col("valid_to"))
    # On the files written: the fact's product_sk is a version in force that day.
    on_versions = (
        fact_event.join(versions, "product_sk", "left")
        .agg(
            F.count_if(~F.coalesce(in_force, F.lit(False))).alias("product_sk not in force"),
            F.count_if(F.col("price") != F.col("version_price")).alias("price != version price"),
        )
        .first()
    )
    stats["product_sk not in force"] = on_versions["product_sk not in force"]
    users = dim_user.select("user_sk", "user_id", "valid_from", "valid_to")
    stats["user_sk not in force"] = (
        fact_event.join(users, "user_sk", "left").where(~F.coalesce(in_force, F.lit(False))).count()
    )
    # On the files written: turn the three keys back into natural keys through
    # the dimensions and compare with silver row for row. The row counts are
    # equal (checked above) and the left joins keep every fact row, so 0 here
    # means the fact holds exactly silver's events, the 7,312 duplicates too.
    event_types = dim_event_type.select("event_type_key", F.col("event_type_code").alias("event_type"))
    as_silver = (
        fact_event.join(versions.withColumnRenamed("version_product_id", "product_id"), "product_sk", "left")
        .join(users.select("user_sk", "user_id"), "user_sk", "left")
        .join(event_types, "event_type_key", "left")
        .select(*COMPARED_WITH_SILVER)
    )
    stats["fact rows not in silver"] = as_silver.exceptAll(silver.select(*COMPARED_WITH_SILVER)).count()
    # On the event rows: that version also belongs to the event's own product.
    right_product = F.coalesce((F.col("version_product_id") == F.col("product_id")) & in_force, F.lit(False))
    stats["events on wrong product"] = events.join(versions, "product_sk", "left").where(~right_product).count()
    stats.update(user_scd2.check_events(events, dim_user))

    # Two lines of information, not checks.
    most_in_a_day = stats.pop("most events in one day")
    other_price = on_versions["price != version price"]

    expected = {
        "fact_event rows": SILVER_EXPECTED["rows"],
        "event_date values": EXPECTED_DATE_DIRS,
        **{f"event_type_key {key}": rows for key, rows in EXPECTED_EVENT_TYPE_ROWS.items()},
        "events": SILVER_EXPECTED["rows"],
    }
    ok = True
    for name, value in stats.items():
        want = expected.get(name, 0)  # every other count must be 0
        ok = ok and value == want
        print(f"{name:<25}{value:>13,}   (expect {want:,})")
    print(f"{'most events in one day':<25}{most_in_a_day:>13,}   (event_sk has room for {EVENT_SK_SLOTS - 1:,})")
    # A version holds the end-of-day price for whole days, so an event earlier
    # on a day the price changed saw another price. Right, and expected.
    share = 100 * other_price / max(stats["fact_event rows"], 1)
    print(f"{'price != version price':<25}{other_price:>13,}   ({share:.1f}%, versions are per day: not an error)")
    return ok


def check_fact_session_funnel(fact_session_funnel, silver, dim_user):
    """fact_session_funnel against silver, dim_user and its own two CHECK constraints.

    fact_session_funnel and dim_user are the copies read back from disk. Each
    measure column's total must equal silver's, so every event sits in exactly
    one session and is counted as its own type. The two CHECKs are
    warehouse/ddl.sql's text, copied word for word, so each row counted here is
    a row Postgres would refuse at step 6. Neither can be NULL once "null
    values" is 0, so they need no coalesce. funnel_stage was built from the
    counts and is tested here on the timestamps: two derivations, not one
    expression compared with itself.
    """
    # warehouse/ddl.sql, fact_session_funnel. Change them together.
    ck_fsf_stage = """funnel_stage =
        CASE WHEN purchase_at   IS NOT NULL THEN 3
             WHEN first_cart_at IS NOT NULL THEN 2
             WHEN first_view_at IS NOT NULL THEN 1
             ELSE 0 END"""
    ck_fsf_lags = """(view_to_cart_sec     IS NULL) = (first_view_at IS NULL OR first_cart_at IS NULL)
        AND (cart_to_purchase_sec IS NULL) = (first_cart_at IS NULL OR purchase_at   IS NULL)"""
    nullable = {"first_view_at", "first_cart_at", "purchase_at", "view_to_cart_sec", "cart_to_purchase_sec"}
    any_null = F.lit(False)
    for column in fact_session_funnel.columns:
        if column not in nullable:
            any_null = any_null | F.col(column).isNull()
    stats = (
        fact_session_funnel.agg(
            F.count("*").alias("fact_session_funnel rows"),
            F.count_if(any_null).alias("null values"),
            (F.count("*") - F.count_distinct("session_sk")).alias("duplicate session_sk"),  # ddl pk_fsf
            F.count_if(F.col("session_start_date") != F.to_date("session_start_at")).alias("session_start_date wrong"),
            F.count_if(~F.expr(ck_fsf_stage)).alias("ck_fsf_stage violated"),
            F.count_if(~F.expr(ck_fsf_lags)).alias("ck_fsf_lags violated"),
            F.sum("view_count").alias("view_count total"),
            F.sum("cart_count").alias("cart_count total"),
            F.sum("purchase_count").alias("purchase_count total"),
            F.sum("cart_value").alias("cart_value total"),
            F.sum("purchase_value").alias("purchase_value total"),
            # Information, not checks: popped below and printed after them.
            F.count_if(F.col("funnel_stage") == 1).alias("stage 1"),
            F.count_if(F.col("funnel_stage") == 2).alias("stage 2"),
            F.count_if(F.col("funnel_stage") == 3).alias("stage 3"),
            F.count_if("is_abandoned").alias("is_abandoned"),
            F.count_if(F.col("view_to_cart_sec") < 0).alias("view_to_cart_sec < 0"),
            F.count_if(F.col("cart_to_purchase_sec") < 0).alias("cart_to_purchase_sec < 0"),
        )
        .first()
        .asDict()
    )
    stages = [stats.pop(f"stage {stage}") for stage in (1, 2, 3)]
    abandoned = stats.pop("is_abandoned")
    negative = [stats.pop("view_to_cart_sec < 0"), stats.pop("cart_to_purchase_sec < 0")]

    # On the files written: user_sk is a version of the session's own user, in
    # force on the day the session started. An equi-join on the unique user_sk,
    # then a filter, as in check_fact_event; a user_sk missing from dim_user counts.
    versions = dim_user.select("user_sk", F.col("user_id").alias("version_user_id"), "valid_from", "valid_to")
    in_force = (
        (F.col("version_user_id") == F.col("user_id"))
        & (F.col("session_start_date") >= F.col("valid_from"))
        & (F.col("session_start_date") < F.col("valid_to"))
    )
    stats["user_sk not in force"] = (
        fact_session_funnel.join(versions, "user_sk", "left").where(~F.coalesce(in_force, F.lit(False))).count()
    )

    # Silver's own numbers, in one pass: one row per distinct user_session, and
    # the same events and the same money as the measure columns add up to.
    expected = (
        silver.agg(
            F.count_distinct("user_session").alias("fact_session_funnel rows"),
            F.count_if(F.col("event_type") == "view").alias("view_count total"),
            F.count_if(F.col("event_type") == "cart").alias("cart_count total"),
            F.count_if(F.col("event_type") == "purchase").alias("purchase_count total"),
            F.sum(F.when(F.col("event_type") == "cart", F.col("price"))).alias("cart_value total"),
            F.sum(F.when(F.col("event_type") == "purchase", F.col("price"))).alias("purchase_value total"),
        )
        .first()
        .asDict()
    )
    ok = True
    for name, value in stats.items():
        want = expected.get(name, 0)  # every other count must be 0
        ok = ok and value == want
        print(f"{name:<25}{value:>13,}   (expect {want:,})")
    print(f"{'funnel_stage 1 / 2 / 3':<25}{stages[0]:>13,} / {stages[1]:,} / {stages[2]:,}")
    print(f"{'is_abandoned':<25}{abandoned:>13,}   (a cart, no purchase: funnel_stage 2)")
    print(f"{'negative lags':<25}{negative[0]:>13,} / {negative[1]:,}   (view->cart / cart->purchase, kept as measured)")
    return ok


def check_dim_user(stg_rfm_snapshot, dim_user):
    """stg_rfm_snapshot and dim_user, as processing/dim_user.py checks them when run alone.

    Both tables are the copies read back from disk. The counts and what each must
    be come from dim_user.py itself (dim_user_stats, EXPECTED_RANGES), so the two
    scripts cannot disagree about a whole dim_user: one current version per user,
    no user_sk twice, one version for anyone who never bought, and no overlap or
    gap between versions. The events are not counted again here: check_fact_event()
    already runs user_scd2.check_events().
    """
    stats = user_scd2.dim_user_stats(stg_rfm_snapshot, dim_user)
    for name, value in stats.items():
        low, high = user_scd2.expected_range(name)
        want = f"{low:,}" if low == high else f"{low:,} to {high:,}"
        print(f"{name:<25}{value:>13,}   (expect {want})")
    return user_scd2.all_as_expected(stats)


# ---------------------------------------------------------------------------
# The two writers. Both skip None, which is what lets the skeleton run, and
# both return the table read back from disk, so the next step starts from the
# file and not from a plan that recomputes everything before it.
# ---------------------------------------------------------------------------

def write_dim(df, path):
    """Small table: one file, no partitions. Returns it read back, or None."""
    if df is None:
        print(f"{path.name:<25}{'not built yet':>13}")
        return None
    if path.parent != WAREHOUSE_DIR:
        raise ValueError(f"{path} is not a table directory directly under {WAREHOUSE_DIR}")
    df.coalesce(1).write.mode("overwrite").parquet(str(path))  # a re-run replaces the table
    table = df.sparkSession.read.parquet(str(path))
    print(f"{path.name:<25}{table.count():>13,}")
    return table


def write_fact(df, path, partition_col, sort_col):
    """Big table: one directory per partition_col value, one file in each,
    rows sorted by sort_col inside it. Returns it read back, or None.

    Sorting by partition_col first matters: Spark sorts by it anyway before a
    partitioned write, and would drop an order that does not start with it.
    """
    if df is None:
        print(f"{path.name:<25}{'not built yet':>13}")
        return None
    if path.parent != WAREHOUSE_DIR:
        raise ValueError(f"{path} is not a table directory directly under {WAREHOUSE_DIR}")
    (
        df.repartition(partition_col)  # one file per directory, the same on every machine
        .sortWithinPartitions(partition_col, sort_col)
        .write.mode("overwrite")
        .partitionBy(partition_col)
        .parquet(str(path))
    )
    table = df.sparkSession.read.parquet(str(path))
    directories = len(list(path.glob(f"{partition_col}=*")))
    print(f"{path.name:<25}{table.count():>13,}   ({directories} {partition_col} directories)")
    return table


def load_postgres(tables):
    """Step 6, owner Tin (W40). Load the Postgres star from the tables written above.

    The loading functions belong in serving/load_star_postgres.py; this step
    calls them with the DataFrames read back from Parquet, so Parquet and
    Postgres hold the same rows. Until they exist, run
    python serving/load_star_postgres.py on its own: it loads the three small
    dimensions.

    Trap: collecting a timestamp column into Python shifts it into the laptop's
    time zone (+07 here), which moves every event_time by 7 hours and makes
    fact_event's ck_fact_date reject the rows. Cast to timestamp_ntz, or render
    it with date_format, before it leaves Spark.
    """
    print(f"{'postgres':<25}not loaded yet (step 6: Tin, W40)")


def main():
    # Check before any write replaces a table.
    if not list(SILVER_DIR.glob("event_date=*")):
        sys.exit(f"{SILVER_DIR} is empty. Run python processing/batch_silver.py first.")
    # Step 2 needs it, and would stop only after step 1 had overwritten its tables.
    if not product_scd2.CATALOG_FILE.exists():
        sys.exit(f"{product_scd2.CATALOG_FILE} is missing. Run python ingestion/gen_catalog.py first.")

    started = time.monotonic()
    spark = SparkSession.builder.master("local[*]").appName("batch_warehouse").getOrCreate()
    try:
        if not check_environment(spark):
            sys.exit("conf/spark-defaults.conf was not read: see the heap and time zone lines above.")
        silver = read_silver(spark)
        print()
        tables = {}

        # Step 1
        tables["dim_date"] = write_dim(build_dim_date(spark), DIM_DATE_DIR)
        tables["dim_event_type"] = write_dim(build_dim_event_type(spark), DIM_EVENT_TYPE_DIR)
        tables["dim_warehouse"] = write_dim(build_dim_warehouse(spark), DIM_WAREHOUSE_DIR)

        # Step 2: product_sk lands on the event rows here.
        dim_product, events = build_dim_product(silver)
        tables["dim_product"] = write_dim(dim_product, DIM_PRODUCT_DIR)

        # Step 3
        tables["stg_rfm_snapshot"] = write_fact(
            build_stg_rfm_snapshot(silver), STG_RFM_SNAPSHOT_DIR, "snapshot_date", "user_id"
        )

        # Step 4: user_sk lands on the event rows here.
        dim_user, events = build_dim_user(tables["stg_rfm_snapshot"], events)
        tables["dim_user"] = write_dim(dim_user, DIM_USER_DIR)

        # Step 5
        tables["fact_event"] = write_fact(
            build_fact_event(events, tables["dim_event_type"]), FACT_EVENT_DIR, "event_date", "event_time"
        )
        tables["fact_session_funnel"] = write_fact(
            build_fact_session_funnel(events), FACT_SESSION_FUNNEL_DIR, "session_start_date", "session_start_at"
        )
        tables["fact_inventory_daily"] = write_fact(
            build_fact_inventory_daily(spark, tables["dim_product"], tables["dim_warehouse"]),
            FACT_INVENTORY_DAILY_DIR, "snapshot_date", "product_id",
        )

        # Each owner's checks go here, each folded into checks_ok like this one:
        # the call first, so every check runs and prints even after one fails.
        print()
        checks_ok = True
        checks_ok = check_fact_event(
            tables["fact_event"], silver, events, tables["dim_event_type"], tables["dim_product"], tables["dim_user"]
        ) and checks_ok
        print()
        checks_ok = check_fact_session_funnel(tables["fact_session_funnel"], silver, tables["dim_user"]) and checks_ok
        print()
        checks_ok = check_dim_user(tables["stg_rfm_snapshot"], tables["dim_user"]) and checks_ok

        # Step 6
        load_postgres(tables)
    finally:
        spark.stop()

    built = sum(table is not None for table in tables.values())
    print(f"{'took':<25}{time.monotonic() - started:>13.0f} s")
    if not checks_ok:
        print("WAREHOUSE CHECK FAILED: see the lines above.")
        sys.exit(1)
    if built == len(tables):
        print("WAREHOUSE OK")
    else:
        print(f"WAREHOUSE PARTIAL: {built} of {len(tables)} tables built")


if __name__ == "__main__":
    main()
