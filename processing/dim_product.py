import os
import sys
import time
from pathlib import Path
 
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
os.environ["SPARK_CONF_DIR"] = str(REPO / "conf")
 
from pyspark.sql import SparkSession, Window  # noqa: E402
from pyspark.sql import functions as F  # noqa: E402
 
SILVER_DIR = REPO / "data" / "silver"
CATALOG_FILE = REPO / "data" / "catalog" / "products.json"
DIM_PRODUCT_DIR = REPO / "data" / "warehouse" / "dim_product"
 
OPEN_DATE = "9999-12-31"  # valid_to sentinel for the current version
 
 
def read_silver_events(spark):
    if not (SILVER_DIR / "_SUCCESS").exists():
        print(f"{SILVER_DIR} has no data yet (no _SUCCESS marker). Run processing/batch_silver.py first.")
        sys.exit(1)
    return spark.read.parquet(str(SILVER_DIR)).select(
        "product_id", "event_time", "price", "brand",
        "category_id", "category_code",
        "category_l1", "category_l2", "category_l3",
    )
 
 
def read_catalog(spark):
    if not CATALOG_FILE.exists():
        print(f"{CATALOG_FILE} is missing. Run ingestion/gen_catalog.py first.")
        sys.exit(1)
    return spark.read.json(str(CATALOG_FILE)).select("product_id", "attributes")
 
 
def assign_versions(events):
    events_with_day = events.withColumn("local_date", F.to_date("event_time"))
 
    daily = (
        events_with_day
        .groupBy("product_id", "local_date")
        .agg(
            F.max_by("price", "event_time").alias("price"),
            F.max_by("brand", "event_time").alias("brand"),
            F.max_by("category_id", "event_time").alias("category_id"),
            F.max_by("category_code", "event_time").alias("category_code"),
            F.max_by("category_l1", "event_time").alias("category_l1"),
            F.max_by("category_l2", "event_time").alias("category_l2"),
            F.max_by("category_l3", "event_time").alias("category_l3"),
        )
    )
 
    day_w = Window.partitionBy("product_id").orderBy("local_date")
    running_w = day_w.rowsBetween(Window.unboundedPreceding, Window.currentRow)
    prev_price = F.lag("price").over(day_w)
    changed = (~F.col("price").eqNullSafe(prev_price)).cast("int")
    daily = (
        daily
        .withColumn("changed", changed)
        .withColumn("version_no", F.sum("changed").over(running_w))
        .drop("changed")
    )
 
    sk_w = Window.orderBy("product_id", "version_no")
    product_sk = (
        daily.select("product_id", "version_no").distinct()
        .withColumn("product_sk", F.row_number().over(sk_w))
    )
    daily = daily.join(product_sk, ["product_id", "version_no"], "left")
 
    return (
        events_with_day
        .join(
            daily.select("product_id", "local_date", "version_no", "product_sk"),
            ["product_id", "local_date"],
            "left",
        )
        .drop("local_date")
    )
 
 
def build_dim_product(versioned_events, catalog):
    versions = (
        versioned_events.groupBy("product_id", "version_no")
        .agg(
            F.min("event_time").alias("valid_from_ts"),
            F.max_by("price", "event_time").alias("price"),
            F.max_by("brand", "event_time").alias("brand"),
            F.max_by("category_id", "event_time").alias("category_id"),
            F.max_by("category_code", "event_time").alias("category_code"),
            F.max_by("category_l1", "event_time").alias("category_l1"),
            F.max_by("category_l2", "event_time").alias("category_l2"),
            F.max_by("category_l3", "event_time").alias("category_l3"),
            F.first("product_sk").alias("product_sk"),
        )
        .withColumn("valid_from", F.to_date("valid_from_ts"))
        .drop("valid_from_ts")
    )
 
    next_w = Window.partitionBy("product_id").orderBy("version_no")
    open_date = F.lit(OPEN_DATE).cast("date")
    versions = (
        versions
        .withColumn("next_valid_from", F.lead("valid_from").over(next_w))
        .withColumn("valid_to", F.coalesce("next_valid_from", open_date))
        .withColumn("is_current", F.col("valid_to") == open_date)
        .drop("next_valid_from")
    )
 
    dim_product = versions.join(catalog, "product_id", "left")
 
    
    missing = dim_product.filter(F.col("attributes").isNull()).count()
    if missing:
        raise RuntimeError(
            f"{missing} dim_product rows have no catalog attributes. "
            "Re-run ingestion/gen_catalog.py against the current data/silver/."
        )
 
    return dim_product.select(
        F.col("product_sk").cast("long").alias("product_sk"),
        "product_id",
        F.col("version_no").cast("int").alias("version_no"),
        "price", "brand", "category_id", "category_code",
        "category_l1", "category_l2", "category_l3",
        "attributes", "valid_from", "valid_to", "is_current",
    )
 
 
def write_dim_product(dim_product) -> None:
    (
        dim_product
        .sortWithinPartitions("product_id", "version_no")
        .coalesce(1)
        .write.mode("overwrite")
        .parquet(str(DIM_PRODUCT_DIR))
    )
 
 
def report(spark) -> bool:
    """Check the SCD2 invariants for dim_product."""
    df = spark.read.parquet(str(DIM_PRODUCT_DIR))
 
    n_versions = df.count()
    n_products = df.select("product_id").distinct().count()
 
    bad_current = (
        df.groupBy("product_id")
        .agg(F.sum(F.col("is_current").cast("int")).alias("n_current"))
        .filter("n_current != 1")
        .count()
    )
 
    w = Window.partitionBy("product_id").orderBy("valid_from")
    overlaps = (
        df.withColumn("next_valid_from", F.lead("valid_from").over(w))
        .filter(
            F.col("next_valid_from").isNotNull()
            & (F.col("next_valid_from") != F.col("valid_to"))
        )
        .count()
    )
 
    bad_range = df.filter(F.col("valid_from") >= F.col("valid_to")).count()
    null_l1 = df.filter(F.col("category_l1").isNull()).count()
    null_attrs = df.filter(F.col("attributes").isNull()).count()
 
    print(f"products                {n_products:>10,}")
    print(f"product versions        {n_versions:>10,}")
    print(f"products with != 1 is_current row   {bad_current:>6,}   (expect 0)")
    print(f"overlapping/gapped SCD2 intervals    {overlaps:>6,}   (expect 0)")
    print(f"valid_from >= valid_to               {bad_range:>6,}   (expect 0)")
    print(f"null category_l1                     {null_l1:>6,}   (expect 0)")
    print(f"null attributes                       {null_attrs:>6,}   (expect 0)")
 
    return bad_current == 0 and overlaps == 0 and bad_range == 0 and null_l1 == 0 and null_attrs == 0
 
 
def main():
    start = time.time()
    spark = (
        SparkSession.builder
        .appName("dim_product")
        .master("local[*]")
        .getOrCreate()
    )
    try:
        events = read_silver_events(spark)
        catalog = read_catalog(spark)
        versioned_events = assign_versions(events)
        dim_product = build_dim_product(versioned_events, catalog)
        write_dim_product(dim_product)
        ok = report(spark)
    finally:
        spark.stop()
 
    took = time.time() - start
    print(f"took                    {took:>9.0f} s")
    if not ok:
        print("DIM_PRODUCT CHECK FAILED")
        sys.exit(1)
    print("DIM_PRODUCT OK")
 
 
if __name__ == "__main__":
    main()