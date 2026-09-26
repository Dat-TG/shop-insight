import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
os.environ["SPARK_CONF_DIR"] = str(REPO / "conf")

from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F


def scd2_violations(dim, key):
    by_key = Window.partitionBy(key).orderBy("valid_from")
    versions = dim.withColumn("next_from", F.lead("valid_from").over(by_key))
    current_per_key = dim.groupBy(key).agg(F.sum(F.col("is_current").cast("int")).alias("current"))
    return {
        "overlaps": versions.where(F.col("valid_to") > F.col("next_from")).count(),
        "not_one_current": current_per_key.where(F.col("current") != 1).count(),
        "gaps": versions.where(F.col("valid_to") < F.col("next_from")).count(),
        "empty_ranges": dim.where(F.col("valid_from") >= F.col("valid_to")).count(),
    }


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: python checks/scd2_integrity.py <parquet path> <natural key>, "
                 "e.g. data/warehouse/dim_user user_id")
    path, key = sys.argv[1], sys.argv[2]
    if not (REPO / path).exists():
        sys.exit(f"{REPO / path} not found.")
    spark = SparkSession.builder.master("local[*]").appName("scd2_integrity").getOrCreate()
    violations = scd2_violations(spark.read.parquet(str(REPO / path)), key)
    spark.stop()
    for name, count in violations.items():
        print(f"{name:<24}{count:>10,}")
    if any(violations.values()):
        print("SCD2 VIOLATIONS")
        sys.exit(1)
    print("SCD2 OK")


if __name__ == "__main__":
    main()
