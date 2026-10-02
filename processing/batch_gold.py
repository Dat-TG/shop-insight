import os
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
os.environ["SPARK_CONF_DIR"] = str(REPO / "conf")

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

DIM_USER_DIR = REPO / "data" / "warehouse" / "dim_user"
RFM_SEGMENTS_DIR = REPO / "data" / "gold" / "rfm_segments"
LAST_SNAPSHOT = date(2019, 11, 30)
RFM_GOLD_COLUMNS = ["user_id", "recency_days", "frequency", "monetary", "r_score", "f_score", "m_score", "segment"]
SEGMENTS = ["champion", "loyal", "promising", "needs_attention", "at_risk", "hibernating", "no_purchase"]
MANY_CURRENT_VERSIONS = "SELECT user_id FROM dim_user WHERE is_current GROUP BY user_id HAVING count(*) > 1"


def build_rfm_segments(dim):
    return dim.where("is_current").select(*RFM_GOLD_COLUMNS).withColumn("snapshot_date", F.lit(LAST_SNAPSHOT))


def rfm_segments_stats(gold):
    unscored = F.col("r_score").isNull()
    no_purchase = F.col("segment") == "no_purchase"
    return gold.agg(
        F.count("*").alias("rfm_segments rows"),
        F.countDistinct("user_id").alias("distinct users"),
        F.count_if(~unscored).alias("buyers"),
        F.countDistinct("segment").alias("segments"),
        F.count_if(unscored != no_purchase).alias("score and segment disagree"),
        F.count_if(~F.col("segment").isin(SEGMENTS)).alias("unknown segment"),
        F.countDistinct("snapshot_date").alias("snapshot partitions"),
    ).first().asDict()


def report(stats):
    for name, value in stats.items():
        print(f"{name:<30}{value:>10,}")


def run_rfm_segments(spark):
    dim = spark.read.parquet(str(DIM_USER_DIR))
    dim.createOrReplaceTempView("dim_user")
    many = spark.sql(MANY_CURRENT_VERSIONS).count()
    report({"users with >1 current version": many})
    if many:
        print("RFM_SEGMENTS MISMATCH: nothing was overwritten")
        return False
    build_rfm_segments(dim).write.mode("overwrite").partitionBy("snapshot_date").parquet(str(RFM_SEGMENTS_DIR))
    gold = spark.read.parquet(str(RFM_SEGMENTS_DIR))
    stats = {"current versions": dim.where("is_current").count(), **rfm_segments_stats(gold)}
    report(stats)
    ok = (
        stats["rfm_segments rows"] == stats["current versions"] == stats["distinct users"]
        and stats["score and segment disagree"] == 0
        and stats["unknown segment"] == 0
        and stats["snapshot partitions"] == 1
    )
    print("RFM_SEGMENTS OK" if ok else "RFM_SEGMENTS MISMATCH")
    return ok


def main():
    if not (DIM_USER_DIR / "_SUCCESS").exists():
        sys.exit(f"{DIM_USER_DIR} is missing. Run python processing/batch_warehouse.py first.")
    spark = SparkSession.builder.master("local[*]").appName("batch_gold").getOrCreate()
    ok = run_rfm_segments(spark)
    spark.stop()
    if not ok:
        sys.exit(1)
    print("GOLD OK")


if __name__ == "__main__":
    main()
