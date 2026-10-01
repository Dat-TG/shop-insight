"""batch_gold.py — reads the star schema Parquet and writes to Cassandra + gold Parquet.

Owners per BR:
  BR2  funnel_daily (Parquet)       — Dat   (W41)
  BR4  rfm_segments (Parquet)       — Khang (W40)
  BR6  stockout_risk (Cassandra)    — Tin   (W40)
  BR7  product_affinity (Parquet)   — Nguyen (W40/W41)

Run AFTER batch_warehouse.py has populated data/warehouse/:
    python processing/batch_gold.py          # all available BRs
    python processing/batch_gold.py --br6    # BR6 only
    python processing/batch_gold.py --rfm    # BR4 only

BR6 contract (SYSTEM_DESIGN.md section 6.1 and cassandra_schema.cql):
  Table: stockout_risk
    PRIMARY KEY ((warehouse_id), days_to_stockout, product_id)
  Idempotency: DELETE the whole partition (WHERE warehouse_id = ?) then INSERT
  the new rows. This is the only safe way since the clustering key changes when
  velocity changes — an upsert would leave orphan rows with the old
  days_to_stockout value.

  Sentinel: fact_inventory_daily stores NULL when velocity_7d = 0 (Postgres
  CHECK ck_fid_dts). Cassandra clustering columns cannot be NULL, so this
  script substitutes 9999.0 before writing (SYSTEM_DESIGN.md note at 6.1).

Stack:
  Uses PySpark local mode and cassandra-driver directly (CLAUDE.md hard rules 1-2).
  No external dependencies outside requirements.txt (no pandas, no connector).
"""

from __future__ import annotations

import argparse
import itertools
import os
import sys
import time
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
os.environ["SPARK_CONF_DIR"] = str(REPO / "conf")

from cassandra.cluster import Cluster
from cassandra.policies import DCAwareRoundRobinPolicy
from cassandra.query import BatchStatement, BatchType
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from serving.check_infra import read_env

WAREHOUSE_DIR = REPO / "data" / "warehouse"
GOLD_DIR = REPO / "data" / "gold"
FACT_INVENTORY_DIR = WAREHOUSE_DIR / "fact_inventory_daily"
DIM_USER_DIR = WAREHOUSE_DIR / "dim_user"
RFM_SEGMENTS_DIR = GOLD_DIR / "rfm_segments"

# ── Cassandra helper ──────────────────────────────────────────────────────────

def get_cassandra_session():
    """Open a cassandra-driver session on keyspace shopinsight."""
    env = read_env()
    host = env.get("CASSANDRA_HOST", "127.0.0.1")
    port = int(env.get("CASSANDRA_PORT", "9042"))
    keyspace = env.get("CASSANDRA_KEYSPACE", "shopinsight")
    dc = env.get("CASSANDRA_DC", "datacenter1")

    cluster = Cluster(
        [host],
        port=port,
        load_balancing_policy=DCAwareRoundRobinPolicy(local_dc=dc),
        protocol_version=5,
    )
    session = cluster.connect(keyspace)
    return cluster, session


# ── BR6: Stockout Risk → Cassandra:stockout_risk ───────────────────────────────

def run_br6(spark: SparkSession) -> bool:
    """Read fact_inventory_daily Parquet and write stockout_risk to Cassandra.

    Owner: Tin (W40).

    Steps per warehouse (SYSTEM_DESIGN.md 6.1):
    1. Filter fact_inventory_daily to the most recent snapshot_date in that
       partition (semi-additive stock_on_hand: only one date makes sense).
    2. Substitute days_to_stockout NULL -> 9999.0 (Cassandra sentinel).
    3. DELETE FROM stockout_risk WHERE warehouse_id = ? (whole partition).
    4. INSERT rows in UNLOGGED batches using prepared statements.
    """
    if not FACT_INVENTORY_DIR.exists() or not list(FACT_INVENTORY_DIR.glob("**/*.parquet")):
        print(f"{FACT_INVENTORY_DIR} is missing. Run python processing/batch_warehouse.py first.")
        return False

    t0 = time.perf_counter()
    print("reading fact_inventory_daily ...")
    df = spark.read.parquet(str(FACT_INVENTORY_DIR))

    # Keep only the latest snapshot_date per warehouse (semi-additive: SYSTEM_DESIGN 5.5)
    latest_dates = df.groupBy("warehouse_id").agg(F.max("snapshot_date").alias("snapshot_date"))
    latest = df.join(latest_dates, ["warehouse_id", "snapshot_date"], "inner")

    # Apply Cassandra sentinel: NULL -> 9999.0
    latest = latest.withColumn(
        "days_to_stockout",
        F.coalesce(F.col("days_to_stockout"), F.lit(9999.0)).cast("float"),
    ).select(
        F.col("warehouse_id").cast("int"),
        F.col("days_to_stockout"),
        F.col("product_id").cast("bigint"),
        F.col("stock_on_hand").cast("int"),
        F.col("velocity_7d").cast("float"),
    )

    # Collect warehouse IDs
    wh_ids = [row.warehouse_id for row in latest.select("warehouse_id").distinct().orderBy("warehouse_id").collect()]
    if not wh_ids:
        print("  no rows found in fact_inventory_daily")
        return False

    cluster, session = get_cassandra_session()
    try:
        delete_stmt = session.prepare("DELETE FROM stockout_risk WHERE warehouse_id = ?")
        insert_stmt = session.prepare(
            "INSERT INTO stockout_risk "
            "(warehouse_id, days_to_stockout, product_id, stock_on_hand, velocity_7d) "
            "VALUES (?, ?, ?, ?, ?)"
        )

        total_rows = 0
        BATCH_SIZE = 100  # unlogged batch size within the same partition key

        for wh_id in wh_ids:
            wh_rows = latest.filter(F.col("warehouse_id") == wh_id).collect()
            session.execute(delete_stmt, (int(wh_id),))

            for i in range(0, len(wh_rows), BATCH_SIZE):
                chunk = wh_rows[i : i + BATCH_SIZE]
                batch = BatchStatement(batch_type=BatchType.UNLOGGED)
                for r in chunk:
                    batch.add(
                        insert_stmt,
                        (
                            int(r.warehouse_id),
                            float(r.days_to_stockout),
                            int(r.product_id),
                            int(r.stock_on_hand),
                            float(r.velocity_7d),
                        ),
                    )
                session.execute(batch)

            total_rows += len(wh_rows)
            print(f"  warehouse {wh_id}: {len(wh_rows):,} rows written to Cassandra")

        elapsed = time.perf_counter() - t0
        print(f"BR6 OK: {total_rows:,} rows across {len(wh_ids)} warehouses in {elapsed:.1f} s")
        return True
    finally:
        cluster.shutdown()


# ── BR4: RFM Segments (Khang) ─────────────────────────────────────────────────

LAST_SNAPSHOT = date(2019, 11, 30)
RFM_GOLD_COLUMNS = ["user_id", "recency_days", "frequency", "monetary", "r_score", "f_score", "m_score", "segment"]
SEGMENTS = ["champion", "loyal", "promising", "needs_attention", "at_risk", "hibernating", "no_purchase"]
MANY_CURRENT_VERSIONS = "SELECT user_id FROM dim_user WHERE is_current GROUP BY user_id HAVING count(*) > 1"


def run_rfm_segments(spark: SparkSession) -> bool:
    """Owner: Khang (W40). Projects rfm_segments gold from dim_user WHERE is_current."""
    if not DIM_USER_DIR.exists() or not list(DIM_USER_DIR.glob("**/*.parquet")):
        print(f"{DIM_USER_DIR} is missing. Run python processing/batch_warehouse.py first.")
        return False

    dim = spark.read.parquet(str(DIM_USER_DIR))
    dim.createOrReplaceTempView("dim_user")
    many = spark.sql(MANY_CURRENT_VERSIONS).count()
    if many:
        print("RFM_SEGMENTS MISMATCH: nothing was overwritten")
        return False

    gold_df = (
        dim.where("is_current")
        .select(*RFM_GOLD_COLUMNS)
        .withColumn("snapshot_date", F.lit(LAST_SNAPSHOT))
    )
    gold_df.write.mode("overwrite").partitionBy("snapshot_date").parquet(str(RFM_SEGMENTS_DIR))
    gold = spark.read.parquet(str(RFM_SEGMENTS_DIR))

    unscored = F.col("r_score").isNull()
    no_purchase = F.col("segment") == "no_purchase"
    stats = gold.agg(
        F.count("*").alias("rfm_segments rows"),
        F.countDistinct("user_id").alias("distinct users"),
        F.count_if(~unscored).alias("buyers"),
        F.countDistinct("segment").alias("segments"),
        F.count_if(unscored != no_purchase).alias("score and segment disagree"),
        F.count_if(~F.col("segment").isin(SEGMENTS)).alias("unknown segment"),
        F.countDistinct("snapshot_date").alias("snapshot partitions"),
    ).first().asDict()

    current_versions = dim.where("is_current").count()
    ok = (
        stats["rfm_segments rows"] == current_versions == stats["distinct users"]
        and stats["score and segment disagree"] == 0
        and stats["unknown segment"] == 0
        and stats["snapshot partitions"] == 1
    )
    print("RFM_SEGMENTS OK" if ok else "RFM_SEGMENTS MISMATCH")
    return ok


# ── Main CLI ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Build batch gold tables from the star schema.")
    parser.add_argument("--br6", action="store_true", help="Run BR6 stockout_risk (Cassandra) only")
    parser.add_argument("--rfm", action="store_true", help="Run BR4 rfm_segments (Parquet) only")
    args = parser.parse_args()

    spark = (
        SparkSession.builder
        .master("local[*]")
        .appName("batch_gold")
        .getOrCreate()
    )

    all_ok = True
    try:
        run_all = not (args.br6 or args.rfm)

        if args.br6 or run_all:
            if FACT_INVENTORY_DIR.exists():
                print("Running BR6 (stockout_risk) ...")
                ok_br6 = run_br6(spark)
                all_ok = all_ok and ok_br6
            elif args.br6:
                print(f"{FACT_INVENTORY_DIR} is missing. Run batch_warehouse.py first.")
                all_ok = False

        if args.rfm or run_all:
            if DIM_USER_DIR.exists():
                print("Running BR4 (rfm_segments) ...")
                ok_rfm = run_rfm_segments(spark)
                all_ok = all_ok and ok_rfm
            elif args.rfm:
                print(f"{DIM_USER_DIR} is missing. Run batch_warehouse.py first.")
                all_ok = False

    finally:
        spark.stop()

    if not all_ok:
        sys.exit(1)
    print("BATCH GOLD OK")


if __name__ == "__main__":
    main()
