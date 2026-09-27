import sys
from pathlib import Path
 
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
 
from cassandra.cluster import Cluster  # noqa: E402
 
from serving.check_infra import read_env  # noqa: E402
 
CQL_FILE = REPO / "serving" / "cassandra_schema.cql"
 
EXPECTED_TABLES = {
    "gmv_by_minute",
    "trending_products",
    "abandoned_carts",
    "stockout_risk",
    "order_velocity_alerts",
}
 
 
def read_statements() -> list:
    """Read the CREATE statements from cassandra_schema.cql."""
    if not CQL_FILE.exists():
        sys.exit(f"{CQL_FILE} not found.")
    raw = CQL_FILE.read_text(encoding="utf-8")
    lines = [ln for ln in raw.splitlines() if not ln.strip().startswith("--")]
    body = "\n".join(lines)
    return [stmt.strip() for stmt in body.split(";") if stmt.strip()]
 
 
def apply_statements(session, statements: list) -> None:
    for stmt in statements:
        session.execute(stmt)
 
 
def report(session, keyspace: str) -> bool:
    """Verify the expected tables exist in Cassandra."""
    rows = session.execute(
        "SELECT table_name FROM system_schema.tables WHERE keyspace_name = %s",
        [keyspace],
    )
    found = {r.table_name for r in rows}
    missing = EXPECTED_TABLES - found
    extra = found - EXPECTED_TABLES
 
    print(f"keyspace  {keyspace}")
    for name in sorted(EXPECTED_TABLES):
        state = "present" if name in found else "MISSING"
        print(f"  {name:<24}{state}")
    if extra:
        print(f"  also present (unexpected): {sorted(extra)}")
 
    return not missing
 
 
def main():
    env = read_env()
    port = int(env.get("CASSANDRA_PORT", 9042))
    keyspace = env.get("CASSANDRA_KEYSPACE", "shopinsight")
 
    statements = read_statements()
 
    cluster = Cluster(["127.0.0.1"], port=port)
    session = cluster.connect()
    try:
        # Single-node setup: replication_factor 1 is the expected choice.
        session.execute(
            f"CREATE KEYSPACE IF NOT EXISTS {keyspace} "
            "WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}"
        )
        session.set_keyspace(keyspace)
        apply_statements(session, statements)
        ok = report(session, keyspace)
    finally:
        cluster.shutdown()
 
    if not ok:
        print("APPLY_SCHEMA CHECK FAILED: see MISSING tables above.")
        sys.exit(1)
    print("APPLY_SCHEMA OK")
 
 
if __name__ == "__main__":
    main()