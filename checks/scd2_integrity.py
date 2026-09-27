import os
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
os.environ["SPARK_CONF_DIR"] = str(REPO / "conf")

from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F

OPEN_END = date(9999, 12, 31)


def scd2_violations(dim, key):
    by_key = Window.partitionBy(key).orderBy("valid_from", "valid_to")
    current = F.coalesce(F.col("is_current"), F.lit(False))
    open_ended = F.coalesce(F.col("valid_to") == F.lit(OPEN_END), F.lit(False))
    counts = (
        dim.withColumn("next_from", F.lead("valid_from").over(by_key))
        .agg(
            F.count_if(F.col("valid_to") > F.col("next_from")).alias("overlaps"),
            F.count_if(F.col("valid_to") < F.col("next_from")).alias("gaps"),
            F.count_if(F.col("valid_from") >= F.col("valid_to")).alias("empty_ranges"),
            F.count_if(current != open_ended).alias("current_flag_wrong"),
            F.count_if(
                F.col("valid_from").isNull() | F.col("valid_to").isNull() | F.col("is_current").isNull()
            ).alias("null_fields"),
        )
        .first()
    )
    not_one_current = (
        dim.groupBy(key).agg(F.count_if(current).alias("current")).where(F.col("current") != 1).count()
    )
    return {
        "overlaps": counts["overlaps"],
        "not_one_current": not_one_current,
        "gaps": counts["gaps"],
        "empty_ranges": counts["empty_ranges"],
        "current_flag_wrong": counts["current_flag_wrong"],
        "null_fields": counts["null_fields"],
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
