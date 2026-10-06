import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]         # repo root
sys.path.insert(0, str(REPO))                      # lets the script import processing.*
os.environ["SPARK_CONF_DIR"] = str(REPO / "conf")  # must come before the first SparkSession

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

FACT_EVENT = REPO / "data" / "warehouse" / "fact_event"
DIM_PRODUCT = REPO / "data" / "warehouse" / "dim_product"
OUT = REPO / "data" / "gold" / "product_affinity"

PURCHASE_KEY = 3             # dim_event_type: 3 = purchase (is_conversion)
MIN_PRODUCT_SESSIONS = 20    # was 50; the join is cheap on this sample, more products get partners
MIN_CO_COUNT = 3             # was 2; a pair seen twice has a noisy lift


def read_baskets(spark: SparkSession) -> DataFrame:
    """One row per (user_session, product_id) purchased. Distinct, so a repeat buy counts once."""
    purchases = (
        spark.read.parquet(str(FACT_EVENT))
        .where(F.col("event_type_key") == PURCHASE_KEY)
        .select("user_session", "product_sk")
    )
    # product_sk is the SCD2 version key; several versions share one product_id.
    # Plain equality join on product_sk, NOT a range join on valid_from/valid_to.
    products = spark.read.parquet(str(DIM_PRODUCT)).select("product_sk", "product_id")
    return (
        purchases.join(F.broadcast(products), "product_sk")
        .select("user_session", "product_id")
        .distinct()
    )


def build_affinity(baskets: DataFrame) -> tuple[DataFrame, int, int]:
    """Return (affinity, purchase_sessions, popular_products)."""
    n_sessions = baskets.select("user_session").distinct().count()  # N for support/lift

    sessions_per_product = baskets.groupBy("product_id").agg(F.count("*").alias("n"))
    popular = sessions_per_product.where(F.col("n") >= MIN_PRODUCT_SESSIONS).cache()
    n_popular = popular.count()

    kept = baskets.join(F.broadcast(popular.select("product_id")), "product_id")
    a = kept.select("user_session", F.col("product_id").alias("product_a"))
    b = kept.select("user_session", F.col("product_id").alias("product_b"))
    pairs = (
        a.join(b, "user_session")
        .where(F.col("product_a") < F.col("product_b"))  # each pair once, no self-pairs
        .groupBy("product_a", "product_b")
        .agg(F.count("*").alias("co_count"))
        .where(F.col("co_count") >= MIN_CO_COUNT)
    )

    n_a = popular.select(F.col("product_id").alias("product_a"), F.col("n").alias("n_a"))
    n_b = popular.select(F.col("product_id").alias("product_b"), F.col("n").alias("n_b"))
    scored = (
        pairs.join(F.broadcast(n_a), "product_a")
        .join(F.broadcast(n_b), "product_b")
        .select(
            "product_a",
            "product_b",
            "co_count",
            (F.col("co_count") / F.lit(n_sessions)).alias("support"),
            (F.col("co_count") * F.lit(n_sessions) / (F.col("n_a") * F.col("n_b"))).alias("lift"),
        )
        .where(F.col("lift") > 1)   # lift <= 1 means no better than chance: not "bought together"
    )
    mirrored = scored.select(
        F.col("product_b").alias("product_a"),
        F.col("product_a").alias("product_b"),
        "co_count",
        "support",
        "lift",
    )
    return scored.unionByName(mirrored), n_sessions, n_popular


def report(spark: SparkSession, n_sessions: int, n_popular: int, took: float) -> bool:
    """Read the gold table back from disk and print the numbers to compare."""
    gold = spark.read.parquet(str(OUT))
    rows = gold.count()
    anchors = gold.select("product_a").distinct().count()
    with_ten = (
        gold.groupBy("product_a").count().where(F.col("count") >= 10).count()
    )
    stats = gold.agg(
        F.min("lift").alias("lo"), F.max("lift").alias("hi"),
        F.count_if(F.col("lift").isNull()).alias("nulls"),
    ).first()
    print()
    print(f"purchase sessions     {n_sessions:>10,}")
    print(f"products >= {MIN_PRODUCT_SESSIONS} sessions {n_popular:>6,}")
    print(f"affinity rows         {rows:>10,}   (both directions, so even)")
    print(f"anchor products       {anchors:>10,}")
    print(f"anchors with >= 10    {with_ten:>10,}   (the 'XONG khi' needs at least one)")
    print(f"lift min / max        {stats['lo']:.2f} / {stats['hi']:.2f}")
    print(f"null lift             {stats['nulls']:>10,}   (expect 0)")
    print(f"took                  {took:>8.0f} s   (expect under 600)")
    ok = rows > 0 and rows % 2 == 0 and stats["nulls"] == 0 and with_ten > 0 and stats["lo"] > 1
    print("BR7 OK" if ok else "BR7 CHECK FAILED")
    return ok


def main() -> None:
    for path in (FACT_EVENT, DIM_PRODUCT):
        if not path.exists():
            sys.exit(f"{path} not found. Run processing/batch_warehouse.py first.")
    start = time.time()
    spark = SparkSession.builder.master("local[*]").appName("br7_affinity").getOrCreate()
    affinity, n_sessions, n_popular = build_affinity(read_baskets(spark))
    # Writes into a subdirectory, so data/gold/.gitkeep is never touched.
    affinity.write.mode("overwrite").parquet(str(OUT))
    ok = report(spark, n_sessions, n_popular, time.time() - start)
    spark.stop()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()