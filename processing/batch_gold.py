"""batch_gold.py — reads the star schema Parquet and writes to Cassandra + gold Parquet.

Owner per BR (W40):
  BR6  stockout_risk (Cassandra)    — Tin   ← implemented
  BR2  funnel_daily (Parquet)       — stub  (W41, owner TBD)
  BR4  rfm_segments (Parquet)       — stub  (W40/W41 Khang)
  BR7  product_affinity (Parquet)   — stub  (W41, owner TBD)

Run AFTER batch_warehouse.py has populated data/warehouse/:
    python processing/batch_gold.py

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

Usage:
    python processing/batch_gold.py          # all BRs that are implemented
    python processing/batch_gold.py --br6    # BR6 only
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

WAREHOUSE_DIR = REPO / "data" / "warehouse"
FACT_INVENTORY_DIR = WAREHOUSE_DIR / "fact_inventory_daily"


# ── BR6: Stockout Risk → Cassandra:stockout_risk ───────────────────────────────

def _cassandra_session():
    """Open a cassandra-driver session on keyspace shopinsight.

    Uses the connection parameters from .env.example (overridden by .env),
    same as serving/check_infra.py and serving/api/cassandra.py.
    """
    from serving.check_infra import read_env
    from cassandra.cluster import Cluster
    from cassandra.policies import DCAwareRoundRobinPolicy

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


def run_br6():
    """Read fact_inventory_daily Parquet and write stockout_risk to Cassandra.

    Steps per warehouse (SYSTEM_DESIGN.md 6.1):
    1. Filter fact_inventory_daily to the most recent snapshot_date in that
       partition (the latest daily row for each SKU/warehouse).
    2. Substitute days_to_stockout NULL → 9999.0 (Cassandra sentinel).
    3. DELETE FROM stockout_risk WHERE warehouse_id = ? (whole partition).
    4. INSERT the new rows using a prepared statement.

    Reading from Parquet gold (fact_inventory_daily) via plain Python avoids
    spinning up a full SparkSession for what is essentially a SELECT + DELETE +
    INSERT. The Parquet files are small enough (~1.9 M rows) to hold in memory.
    """
    try:
        import pandas as pd
    except ImportError:
        sys.exit("pandas is required to read Parquet without Spark: pip install pandas pyarrow")

    if not FACT_INVENTORY_DIR.exists() or not list(FACT_INVENTORY_DIR.glob("**/*.parquet")):
        sys.exit(
            f"{FACT_INVENTORY_DIR} is empty or missing.\n"
            "Run python processing/batch_warehouse.py first."
        )

    t0 = time.perf_counter()

    # ── 1. Read the full fact_inventory_daily Parquet ─────────────────────────
    # Parquet is partitioned by snapshot_date / product_id (write_fact columns).
    # pandas read_parquet walks all partition directories automatically.
    print("reading fact_inventory_daily ...")
    df = pd.read_parquet(FACT_INVENTORY_DIR)
    print(f"  {len(df):,} rows loaded in {time.perf_counter() - t0:.1f}s")

    # ── 2. Keep only the latest snapshot_date per warehouse ───────────────────
    # stock_on_hand is semi-additive (SYSTEM_DESIGN.md 5.5): only one date makes
    # sense for a stockout estimate. The per-warehouse max may differ by one day
    # if the warehouse was added mid-window, so compute per warehouse.
    df["_max_date"] = df.groupby("warehouse_id")["snapshot_date"].transform("max")
    latest = df[df["snapshot_date"] == df["_max_date"]].copy()
    latest.drop(columns="_max_date", inplace=True)

    # ── 3. Apply Cassandra sentinel ───────────────────────────────────────────
    # NULL in Postgres → 9999.0 in Cassandra (clustering column cannot be NULL).
    latest["days_to_stockout"] = latest["days_to_stockout"].fillna(9999.0)

    # ── 4. Connect and write per warehouse ────────────────────────────────────
    cluster, session = _cassandra_session()
    try:
        delete_stmt = session.prepare(
            "DELETE FROM stockout_risk WHERE warehouse_id = ?"
        )
        insert_stmt = session.prepare(
            "INSERT INTO stockout_risk "
            "(warehouse_id, days_to_stockout, product_id, stock_on_hand, velocity_7d) "
            "VALUES (?, ?, ?, ?, ?)"
        )

        total_rows = 0
        for wh_id in sorted(latest["warehouse_id"].unique()):
            wh_rows = latest[latest["warehouse_id"] == wh_id]

            # Delete entire partition before inserting — idempotent (SYSTEM_DESIGN 6.1)
            session.execute(delete_stmt, (int(wh_id),))

            for _, row in wh_rows.iterrows():
                session.execute(insert_stmt, (
                    int(row["warehouse_id"]),
                    float(row["days_to_stockout"]),
                    int(row["product_id"]),
                    int(row["stock_on_hand"]),
                    float(row["velocity_7d"]),
                ))
            total_rows += len(wh_rows)
            print(
                f"  warehouse {int(wh_id)}: "
                f"{len(wh_rows):,} rows "
                f"(snapshot {wh_rows['snapshot_date'].iloc[0]})"
            )
    finally:
        cluster.shutdown()

    elapsed = time.perf_counter() - t0
    print(f"BR6 stockout_risk: {total_rows:,} rows → Cassandra in {elapsed:.1f}s")


# ── BR2: funnel_daily (Parquet) — Stub ─────────────────────────────────────────

def run_br2():
    """BR2 funnel_daily. Owner: TBD. Stub — returns immediately. W41."""
    print("BR2 funnel_daily: not implemented yet (W41)")


# ── BR4: rfm_segments (Parquet) — Stub ─────────────────────────────────────────

def run_br4():
    """BR4 rfm_segments. Owner: Khang. Stub — returns immediately. W40/W41."""
    print("BR4 rfm_segments: not implemented yet (Khang)")


# ── BR7: product_affinity (Parquet) — Stub ─────────────────────────────────────

def run_br7():
    """BR7 product_affinity. Owner: TBD. Stub — returns immediately. W41."""
    print("BR7 product_affinity: not implemented yet (W41)")


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--br6", action="store_true", help="Run BR6 only")
    parser.add_argument("--br2", action="store_true", help="Run BR2 only")
    parser.add_argument("--br4", action="store_true", help="Run BR4 only")
    parser.add_argument("--br7", action="store_true", help="Run BR7 only")
    args = parser.parse_args()

    run_all = not any([args.br6, args.br2, args.br4, args.br7])

    if run_all or args.br6:
        run_br6()
    if run_all or args.br2:
        run_br2()
    if run_all or args.br4:
        run_br4()
    if run_all or args.br7:
        run_br7()


if __name__ == "__main__":
    main()
