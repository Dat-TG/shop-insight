import os
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
os.environ["SPARK_CONF_DIR"] = str(REPO / "conf")

from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F

from checks.scd2_integrity import scd2_violations

SILVER_DIR = REPO / "data" / "silver"
RFM_DIR = REPO / "data" / "warehouse" / "stg_rfm_snapshot"
DIM_USER_DIR = REPO / "data" / "warehouse" / "dim_user"
SNAPSHOTS = [date(2019, 11, 7), date(2019, 11, 14), date(2019, 11, 21), date(2019, 11, 28), date(2019, 11, 30)]
FIRST_DAY = date(2019, 11, 1)
OPEN_END = date(9999, 12, 31)
EXPECTED_USERS = 258_330
VERSION_SLOTS = 10
RFM_COLUMNS = [
    "user_id", "snapshot_date", "recency_days", "frequency", "monetary",
    "r_score", "f_score", "m_score", "rfm_cell", "segment", "version_no", "user_sk",
]
DIM_USER_COLUMNS = [
    "user_sk", "user_id", "version_no", "snapshot_date", "recency_days", "frequency", "monetary",
    "r_score", "f_score", "m_score", "rfm_cell", "segment", "valid_from", "valid_to", "is_current",
]


def score(order):
    buyers = Window.partitionBy("snapshot_date", F.col("frequency") > 0).orderBy(order, "user_id")
    return F.when(F.col("frequency") > 0, F.ntile(5).over(buyers)).cast("smallint")


def segment(r, f):
    return (
        F.when(F.col("rfm_cell").isNull(), "no_purchase")
        .when((r >= 4) & (f >= 4), "champion")
        .when((r >= 3) & (f >= 3), "loyal")
        .when((r >= 4) & (f <= 2), "promising")
        .when((r == 3) & (f <= 2), "needs_attention")
        .when((r <= 2) & (f >= 3), "at_risk")
        .otherwise("hibernating")
    )


def build_rfm_snapshot(silver):
    snapshots = silver.sparkSession.createDataFrame([(day,) for day in SNAPSHOTS], ["snapshot_date"])
    totals = (
        silver.where(F.col("event_type") == "purchase")
        .join(snapshots, F.col("event_date") <= F.col("snapshot_date"))
        .groupBy("user_id", "snapshot_date")
        .agg(F.max("event_date").alias("last_buy"), F.count("*").alias("frequency"), F.sum("price").alias("monetary"))
    )
    by_user = Window.partitionBy("user_id").orderBy("snapshot_date")
    cell_changed = F.lag("snapshot_date").over(by_user).isNull() | ~F.col("rfm_cell").eqNullSafe(
        F.lag("rfm_cell").over(by_user)
    )
    return (
        silver.select("user_id").distinct()
        .crossJoin(snapshots)
        .join(totals, ["user_id", "snapshot_date"], "left")
        .withColumn("recency_days", F.datediff("snapshot_date", "last_buy"))
        .withColumn("frequency", F.coalesce("frequency", F.lit(0)).cast("int"))
        .withColumn("monetary", F.coalesce("monetary", F.lit(0)).cast("decimal(14,2)"))
        .withColumn("r_score", score(F.col("recency_days").desc()))
        .withColumn("f_score", score(F.col("frequency")))
        .withColumn("m_score", score(F.col("monetary")))
        .withColumn("rfm_cell", F.concat(*[F.col(s).cast("string") for s in ("r_score", "f_score", "m_score")]))
        .withColumn("segment", segment(F.col("r_score"), F.col("f_score")))
        .withColumn("version_no", F.sum(cell_changed.cast("int")).over(by_user))
        .withColumn("user_sk", F.col("user_id") * VERSION_SLOTS + F.col("version_no"))
        .select(*RFM_COLUMNS)
    )


def build_dim_user(rfm_snapshot):
    by_version = Window.partitionBy("user_id", "version_no")
    by_user = Window.partitionBy("user_id").orderBy("version_no")
    return (
        rfm_snapshot.withColumn("first_snapshot", F.min("snapshot_date").over(by_version))
        .where(F.col("snapshot_date") == F.col("first_snapshot"))
        .withColumn("valid_from", F.when(F.col("version_no") == 1, F.lit(FIRST_DAY)).otherwise(F.col("snapshot_date")))
        .withColumn("valid_to", F.coalesce(F.date_sub(F.lead("valid_from").over(by_user), 1), F.lit(OPEN_END)))
        .withColumn("is_current", F.col("valid_to") == F.lit(OPEN_END))
        .select(*DIM_USER_COLUMNS)
    )


def snapshot_of(day):
    snapshot = F.lit(SNAPSHOTS[0])
    for cutoff in SNAPSHOTS[1:]:
        snapshot = F.when(day >= F.lit(cutoff), F.lit(cutoff)).otherwise(snapshot)
    return snapshot


def with_user_sk(events, rfm_snapshot):
    keys = rfm_snapshot.select("user_id", "snapshot_date", "user_sk")
    return (
        events.withColumn("snapshot_date", snapshot_of(F.col("event_date")))
        .join(keys, ["user_id", "snapshot_date"], "left")
        .select(*events.columns, "user_sk")
    )


def report(stats):
    for name, value in stats.items():
        print(f"{name:<24}{value:>10,}")


def main():
    if not list(SILVER_DIR.glob("event_date=*")):
        sys.exit(f"{SILVER_DIR} is empty. Run python processing/batch_silver.py first.")
    if len(SNAPSHOTS) >= VERSION_SLOTS:
        sys.exit(f"user_sk holds at most {VERSION_SLOTS - 1} versions per user: raise VERSION_SLOTS.")
    spark = SparkSession.builder.master("local[*]").appName("dim_user").getOrCreate()
    silver = spark.read.parquet(str(SILVER_DIR))
    build_rfm_snapshot(silver).write.mode("overwrite").parquet(str(RFM_DIR))
    rfm = spark.read.parquet(str(RFM_DIR))
    build_dim_user(rfm).write.mode("overwrite").parquet(str(DIM_USER_DIR))
    dim = spark.read.parquet(str(DIM_USER_DIR))
    events = with_user_sk(silver, rfm)
    stats = {
        "stg_rfm_snapshot": rfm.count(),
        "dim_user versions": dim.count(),
        "dim_user current": dim.where("is_current").count(),
        "duplicate user_sk": dim.groupBy("user_sk").count().where("count > 1").count(),
        "events": events.count(),
        "events without user_sk": events.where(F.col("user_sk").isNull()).count(),
        **scd2_violations(dim, "user_id"),
    }
    silver_rows = silver.count()
    spark.stop()
    report(stats)
    ok = (
        stats["stg_rfm_snapshot"] == EXPECTED_USERS * len(SNAPSHOTS)
        and stats["dim_user current"] == EXPECTED_USERS
        and EXPECTED_USERS <= stats["dim_user versions"] <= EXPECTED_USERS * len(SNAPSHOTS)
        and stats["duplicate user_sk"] == 0
        and stats["events"] == silver_rows
        and stats["events without user_sk"] == 0
        and not any(stats[name] for name in ("overlaps", "not_one_current", "gaps"))
    )
    if not ok:
        print("DIM_USER MISMATCH")
        sys.exit(1)
    print("DIM_USER OK")


if __name__ == "__main__":
    main()
