"""Warehouse: silver -> the star schema, as Parquet (SYSTEM_DESIGN.md section 5).

    python processing/batch_warehouse.py

THIS IS THE SKELETON. Every build_* function below is a stub that returns None,
so the script runs end to end, writes nothing, and prints "not built yet" for
each table. Each owner replaces the BODY of their own function and keeps its
signature. Nobody writes Parquet directly: every table goes through write_dim()
or write_fact(), so all nine tables land the same way.

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
    5     fact_session_funnel            W40      the events
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
- build_fact_event() then only selects columns. The join never happens.

Memory: the driver heap is set in conf/spark-defaults.conf and nowhere else.
Setting it on SparkSession.builder works only when that builder starts the JVM;
once a JVM runs it is ignored, silently after a stop(). An executor memory
setting does nothing in local[*], where the driver is the only executor.
check_environment() prints the heap the JVM really got.

Done when the script prints WAREHOUSE OK, with all nine tables built. Until
then it prints WAREHOUSE PARTIAL and says how many are built; the skeleton
prints:

    dim_date                 not built yet
    ...                                          (nine lines)
    postgres                 not loaded yet (step 6: Tin, W40)
    WAREHOUSE PARTIAL: 0 of 9 tables built
"""

import os
import sys
import time
from pathlib import Path

# The same three lines open every Spark script in this repo (see processing/kata.py).
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))  # lets `python processing/batch_warehouse.py` find the repo root
os.environ["SPARK_CONF_DIR"] = str(REPO / "conf")  # driver memory + UTC, before the JVM starts

from pyspark.sql import SparkSession

from processing.batch_silver import EXPECTED as SILVER_EXPECTED
from processing.kata import check_environment
from processing.schema import EVENT_SCHEMA

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
# createDataFrame() reads Python ints as bigint, so cast to warehouse/ddl.sql's
# smallint and integer columns.
# ---------------------------------------------------------------------------

def build_dim_date(spark):
    """dim_date: one row per day, 2019-10-01 .. 2019-12-31 (92 rows), is_holiday from seed/.

    Columns and types: warehouse/ddl.sql, dim_date. Stub: returns None.
    """
    return None


def build_dim_event_type(spark):
    """dim_event_type: the five rows, keys 1, 2, 3, 4 and -1 (unknown).

    Columns and types: warehouse/ddl.sql, dim_event_type. build_fact_event()
    takes its event_type_key from this table. Stub: returns None.
    """
    return None


def build_dim_warehouse(spark):
    """dim_warehouse: the five warehouses, warehouse_id 1..5.

    Columns and types: warehouse/ddl.sql, dim_warehouse. Stub: returns None.
    """
    return None


# ---------------------------------------------------------------------------
# Steps 2-4: the two SCD2 dimensions. Each returns (dim, events): the dimension
# to write, and the event rows with its surrogate key added. Owners wire their
# own functions in with an import and a call, never a copy:
#   step 2: processing/dim_product.py   assign_versions, build_dim_product
#   steps 3-4: processing/dim_user.py   build_rfm_snapshot, build_dim_user, with_user_sk
# Import the MODULE under an alias, at the top of this file:
#   import processing.dim_product as product_scd2
#   import processing.dim_user as user_scd2
# and call product_scd2.build_dim_product(...), user_scd2.build_dim_user(...).
# Never `from processing.dim_user import build_dim_user`: the stub below has the
# same name, its def runs after the import and replaces it, and the stub then
# calls itself. Not `from processing import dim_user` either: main() has a
# local variable called dim_user.
# ---------------------------------------------------------------------------

def build_dim_product(silver):
    """Step 2, owner Nguyen. Returns (dim_product, events).

    events: every silver column plus product_sk, assigned in the same window
    pass that detects the price change (all columns: fact_event needs user_id,
    user_session and event_type too). dim_product: warehouse/ddl.sql, one row per
    product version, valid_to exclusive, 9999-12-31 when current.
    Stub: returns (None, silver), so the events pass through untouched.
    """
    return None, silver


def build_stg_rfm_snapshot(silver):
    """Step 3, owner Khang. R, F and M per user per snapshot date, on natural keys.

    Written through write_fact() partitioned by snapshot_date, the layout
    processing/dim_user.py uses. Stub: returns None.
    """
    return None


def build_dim_user(stg_rfm_snapshot, events):
    """Step 4, owner Khang. Returns (dim_user, events).

    stg_rfm_snapshot is the copy read back from disk. events gains user_sk, the
    version in force on each event's date. Stub: returns (None, events).
    """
    return None, events


# ---------------------------------------------------------------------------
# Step 5: the three facts, one per Kimball type (SYSTEM_DESIGN.md 5.2 and 5.5).
# ---------------------------------------------------------------------------

def build_fact_event(events, dim_event_type):
    """Transaction fact, owner Dat. One row per silver event, 1:1 with silver.

    Selects the surrogate keys already on the event rows, adds event_sk,
    date_key and event_type_key. Columns: warehouse/ddl.sql, fact_event.
    Stub: returns None.
    """
    return None


def build_fact_session_funnel(events):
    """Accumulating snapshot, W40. One row per session, user_sk as of session start.

    Columns: warehouse/ddl.sql, fact_session_funnel. Stub: returns None.
    """
    return None


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

        # Each owner's checks go here and fold into checks_ok, e.g.
        # checks_ok = checks_ok and check_fact_event(...). None yet.
        checks_ok = True

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
