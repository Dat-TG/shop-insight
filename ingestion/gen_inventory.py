import os
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
os.environ["SPARK_CONF_DIR"] = str(REPO / "conf")

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

BRONZE_DIR = REPO / "data" / "bronze"
INVENTORY_DIR = REPO / "data" / "inventory"
FIRST_DAY = date(2019, 11, 1)
LAST_DAY = date(2019, 11, 30)
DAYS = (LAST_DAY - FIRST_DAY).days + 1
WAREHOUSES = 5
LOW_STOCK_PERCENT = 10
LOW_STOCK_TOLERANCE = 2
MIN_REORDER_POINT = 10
MAX_REORDER_POINT = 50
NORMAL_STOCK_SPREAD = 2
RESTOCK_EVERY_DAYS = 7
RESTOCK_BATCH = 2
EXPECTED_PRODUCTS = 12_731
EXPECTED_ROWS = EXPECTED_PRODUCTS * WAREHOUSES * DAYS
INVENTORY_COLUMNS = ["product_id", "warehouse_id", "snapshot_date", "stock_on_hand", "reorder_point", "units_received"]


def purchased_products(bronze):
    return bronze.where(F.col("event_type") == "purchase").select("product_id").distinct()


def build_inventory(products):
    spark = products.sparkSession
    warehouses = spark.range(1, WAREHOUSES + 1).select(F.col("id").cast("int").alias("warehouse_id"))
    days = spark.range(1).select(F.explode(F.sequence(F.lit(FIRST_DAY), F.lit(LAST_DAY))).alias("snapshot_date"))
    pair = F.xxhash64("product_id", "warehouse_id")
    day = F.xxhash64("product_id", "warehouse_id", "snapshot_date")
    low_stock = F.pmod(F.xxhash64("product_id", "warehouse_id", F.lit("low")), 100) < LOW_STOCK_PERCENT
    reorder_point = F.col("reorder_point")
    return (
        products.crossJoin(warehouses)
        .crossJoin(days)
        .withColumn(
            "reorder_point",
            (MIN_REORDER_POINT + F.pmod(pair, MAX_REORDER_POINT - MIN_REORDER_POINT + 1)).cast("int"),
        )
        .withColumn(
            "stock_on_hand",
            F.when(low_stock, F.pmod(day, reorder_point))
            .otherwise(reorder_point + F.pmod(day, NORMAL_STOCK_SPREAD * reorder_point))
            .cast("int"),
        )
        .withColumn(
            "units_received",
            F.when(F.pmod(day, RESTOCK_EVERY_DAYS) == 0, RESTOCK_BATCH * reorder_point).otherwise(0).cast("int"),
        )
        .select(*INVENTORY_COLUMNS)
    )


def write_inventory(inventory):
    try:
        inventory.repartition("snapshot_date").write.mode("overwrite").partitionBy("snapshot_date").parquet(
            str(INVENTORY_DIR)
        )
    finally:
        INVENTORY_DIR.mkdir(parents=True, exist_ok=True)
        (INVENTORY_DIR / ".gitkeep").touch()


def main():
    if not list(BRONZE_DIR.glob("event_date=*")):
        sys.exit(f"{BRONZE_DIR} is empty. Run python ingestion/load_bronze.py first.")
    spark = SparkSession.builder.master("local[*]").appName("gen_inventory").getOrCreate()
    products = purchased_products(spark.read.parquet(str(BRONZE_DIR)))
    product_count = products.count()
    if product_count != EXPECTED_PRODUCTS:
        spark.stop()
        sys.exit(
            f"bronze has {product_count:,} purchased products, expected {EXPECTED_PRODUCTS:,}. "
            "Re-run ingestion/load_bronze.py; nothing was overwritten."
        )
    write_inventory(build_inventory(products))
    inventory = spark.read.parquet(str(INVENTORY_DIR))
    last_day = F.col("snapshot_date") == F.lit(LAST_DAY)
    totals = inventory.agg(
        F.countDistinct("product_id").alias("products"),
        F.count("*").alias("rows"),
        F.count_if(
            (F.col("stock_on_hand") < 0) | (F.col("units_received") < 0) | (F.col("reorder_point") <= 0)
        ).alias("negative values"),
        F.count_if(last_day & (F.col("stock_on_hand") < F.col("reorder_point"))).alias("below"),
        F.count_if(last_day).alias("last_day"),
    ).first()
    spark.stop()
    below_reorder = 100 * totals["below"] / totals["last_day"]
    for name in ("products", "rows", "negative values"):
        print(f"{name:<24}{totals[name]:>10,}")
    print(f"{'below reorder ' + LAST_DAY.isoformat():<24}{below_reorder:>9.1f}%")
    ok = (
        totals["products"] == EXPECTED_PRODUCTS
        and totals["rows"] == EXPECTED_ROWS
        and totals["negative values"] == 0
        and abs(below_reorder - LOW_STOCK_PERCENT) <= LOW_STOCK_TOLERANCE
    )
    if not ok:
        print("INVENTORY MISMATCH")
        sys.exit(1)
    print("INVENTORY OK")


if __name__ == "__main__":
    main()
