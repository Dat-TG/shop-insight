import os
import sys
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
os.environ["SPARK_CONF_DIR"] = str(REPO / "conf")

from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F

SILVER_DIR = REPO / "data" / "silver"
INVENTORY_DIR = REPO / "data" / "inventory"
FIRST_DAY = date(2019, 11, 1)
LAST_DAY = date(2019, 11, 30)
DAYS = (LAST_DAY - FIRST_DAY).days + 1
WAREHOUSES = 5
LOW_STOCK_PERCENT = 10
LOW_STOCK_TOLERANCE = 2
MAX_SAFETY_STOCK = 2
RESTOCK_COVER_DAYS = 7
AT_RISK_DAYS = 3
EXPECTED_PRODUCTS = 12_731
EXPECTED_ROWS = EXPECTED_PRODUCTS * WAREHOUSES * DAYS
INVENTORY_COLUMNS = ["product_id", "warehouse_id", "snapshot_date", "stock_on_hand", "reorder_point", "units_received"]
STOCK_DAYS_TYPE = "array<struct<snapshot_date:date,units_received:int,stock_on_hand:int>>"


def purchases_by_warehouse(silver):
    return silver.where(F.col("event_type") == "purchase").withColumn(
        "warehouse_id", (1 + F.pmod(F.xxhash64("user_id"), F.lit(WAREHOUSES))).cast("int")
    )


def daily_sales(purchases):
    return purchases.groupBy("product_id", "warehouse_id", F.col("event_date").alias("snapshot_date")).agg(
        F.count("*").cast("int").alias("units_sold")
    )


def run_stock(days, opening, reorder_point, batch, waiting_for_supplier):
    stock = opening
    result = []
    for day in days:
        received = batch if stock < reorder_point and not waiting_for_supplier else 0
        received += max(0, day.units_sold - stock - received)
        stock += received - day.units_sold
        result.append((day.snapshot_date, received, stock))
    return result


def build_inventory(purchases):
    spark = purchases.sparkSession
    warehouses = spark.range(1, WAREHOUSES + 1).select(F.col("id").cast("int").alias("warehouse_id"))
    days = spark.range(1).select(F.explode(F.sequence(F.lit(FIRST_DAY), F.lit(LAST_DAY))).alias("snapshot_date"))
    pairs = (
        purchases.select("product_id")
        .distinct()
        .crossJoin(warehouses)
        .crossJoin(days)
        .join(daily_sales(purchases), ["product_id", "warehouse_id", "snapshot_date"], "left")
        .fillna(0, ["units_sold"])
        .groupBy("product_id", "warehouse_id")
        .agg(
            F.sort_array(F.collect_list(F.struct("snapshot_date", "units_sold"))).alias("days"),
            F.sum("units_sold").alias("month_sold"),
        )
    )
    daily_average = F.col("month_sold") / DAYS
    safety_stock = F.pmod(F.xxhash64("product_id", "warehouse_id"), F.lit(MAX_SAFETY_STOCK + 1))
    waiting = F.pmod(F.xxhash64("product_id", "warehouse_id", F.lit("low")), F.lit(100)) < LOW_STOCK_PERCENT
    spread = F.xxhash64("product_id", "warehouse_id", F.lit("open"))
    stock_days = F.udf(run_stock, STOCK_DAYS_TYPE)
    return (
        pairs.withColumn("reorder_point", (F.ceil(daily_average) + 1 + safety_stock).cast("int"))
        .withColumn("batch", (F.col("reorder_point") + F.ceil(daily_average * RESTOCK_COVER_DAYS)).cast("int"))
        .withColumn(
            "opening",
            F.when(waiting, F.pmod(spread, F.col("reorder_point")))
            .otherwise(F.col("reorder_point") + F.pmod(spread, F.col("batch")))
            .cast("int"),
        )
        .select(
            "product_id",
            "warehouse_id",
            "reorder_point",
            F.explode(stock_days("days", "opening", "reorder_point", "batch", waiting)).alias("day"),
        )
        .select("product_id", "warehouse_id", "reorder_point", "day.*")
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
    if not list(SILVER_DIR.glob("event_date=*")):
        sys.exit(f"{SILVER_DIR} is empty. Run python processing/batch_silver.py first.")
    spark = SparkSession.builder.master("local[*]").appName("gen_inventory").getOrCreate()
    purchases = purchases_by_warehouse(spark.read.parquet(str(SILVER_DIR)))
    product_count = purchases.select("product_id").distinct().count()
    if product_count != EXPECTED_PRODUCTS:
        spark.stop()
        sys.exit(
            f"silver has {product_count:,} purchased products, expected {EXPECTED_PRODUCTS:,}. "
            "Re-run processing/batch_silver.py; nothing was overwritten."
        )
    write_inventory(build_inventory(purchases))
    by_pair = Window.partitionBy("product_id", "warehouse_id")
    last_day = F.col("snapshot_date") == F.lit(LAST_DAY)
    last_week = F.col("snapshot_date") > F.lit(LAST_DAY - timedelta(days=7))
    checked = (
        spark.read.parquet(str(INVENTORY_DIR))
        .join(daily_sales(purchases), ["product_id", "warehouse_id", "snapshot_date"], "left")
        .fillna(0, ["units_sold"])
        .withColumn("yesterday", F.lag("stock_on_hand").over(by_pair.orderBy("snapshot_date")))
        .withColumn("velocity_7d", F.sum(F.when(last_week, F.col("units_sold"))).over(by_pair) / 7)
    )
    totals = checked.agg(
        F.countDistinct("product_id").alias("products"),
        F.count("*").alias("rows"),
        F.count_if(
            (F.col("stock_on_hand") < 0) | (F.col("units_received") < 0) | (F.col("reorder_point") <= 0)
        ).alias("negative values"),
        F.count_if(
            F.col("stock_on_hand") != F.col("yesterday") + F.col("units_received") - F.col("units_sold")
        ).alias("broken balance"),
        F.count_if(last_day & (F.col("stock_on_hand") < F.col("reorder_point"))).alias("below"),
        F.count_if(last_day).alias("last_day"),
    ).first()
    at_risk = dict(
        checked.where(last_day & (F.col("stock_on_hand") < AT_RISK_DAYS * F.col("velocity_7d")))
        .groupBy("warehouse_id")
        .count()
        .collect()
    )
    spark.stop()
    below_reorder = 100 * totals["below"] / totals["last_day"]
    at_risk_counts = [at_risk.get(w, 0) for w in range(1, WAREHOUSES + 1)]
    for name in ("products", "rows", "negative values", "broken balance"):
        print(f"{name:<30}{totals[name]:>10,}")
    print(f"{'below reorder ' + LAST_DAY.isoformat():<30}{below_reorder:>9.1f}%")
    print(f"{f'under {AT_RISK_DAYS} days per warehouse':<30}{' / '.join(map(str, at_risk_counts))}")
    ok = (
        totals["products"] == EXPECTED_PRODUCTS
        and totals["rows"] == EXPECTED_ROWS
        and totals["negative values"] == 0
        and totals["broken balance"] == 0
        and abs(below_reorder - LOW_STOCK_PERCENT) <= LOW_STOCK_TOLERANCE
        and min(at_risk_counts) > 0
    )
    if not ok:
        print("INVENTORY MISMATCH")
        sys.exit(1)
    print("INVENTORY OK")


if __name__ == "__main__":
    main()
