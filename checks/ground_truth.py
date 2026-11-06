import argparse, datetime as dt, math, sys
from pathlib import Path
import duckdb

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
DW, GOLD, SILVER = REPO / "data/warehouse", REPO / "data/gold", REPO / "data/silver"
THRESHOLD = 99.0

def pq(path):
    return f"read_parquet('{path}/**/*.parquet', hive_partitioning=true)"

def cassandra():
    from cassandra.cluster import Cluster
    from serving.check_infra import read_env
    env = read_env()
    cluster = Cluster([env.get("CASSANDRA_HOST", "127.0.0.1")],
                      port=int(env.get("CASSANDRA_PORT", 9042)))
    return cluster.connect(env.get("CASSANDRA_KEYSPACE", "shopinsight"))

def line(name, ok, total, note=""):
    pct = 100.0 * ok / total if total else 0.0
    flag = "OK  " if pct >= THRESHOLD else "LOW "
    print(f"{flag}{name}  {pct:6.2f}%  ({ok:,}/{total:,})  {note}")
    return pct

# ---------------- BR6 ----------------
def br6(con, cs):
    truth = {(w, p): d for w, p, d in con.execute(f"""
        WITH fi AS (SELECT * FROM {pq(DW / 'fact_inventory_daily')}),
             last AS (SELECT max(snapshot_date) d FROM fi)
        SELECT warehouse_id, product_id,
               CASE WHEN velocity_7d > 0 THEN stock_on_hand / velocity_7d ELSE 9999.0 END
        FROM fi, last WHERE snapshot_date = last.d""").fetchall()}
    gold = {}
    for wh in range(1, 6):
        for r in cs.execute("SELECT warehouse_id, product_id, days_to_stockout "
                            "FROM stockout_risk WHERE warehouse_id = %s", (wh,)):
            gold[(r.warehouse_id, r.product_id)] = r.days_to_stockout
    ok = sum(1 for k, g in gold.items()
             if k in truth and math.isclose(g, truth[k], rel_tol=1e-4, abs_tol=1e-3))
    total = len(set(gold) | set(truth))
    return line("BR6 stockout_risk", ok, total,
                f"gold {len(gold):,} rows, truth {len(truth):,} rows")

# ---------------- BR7 ----------------
def br7(con):
    ok, total = con.execute(f"""
        WITH p AS (  -- distinct (session, product): silver/fact_event hold 7,312 exact duplicates
          SELECT DISTINCT e.user_session, d.product_id
          FROM {pq(DW / 'fact_event')} e
          JOIN {pq(DW / 'dim_product')} d USING (product_sk)
          WHERE e.event_type_key = 3),
        n AS (SELECT count(DISTINCT user_session) n FROM p),
        f AS (SELECT product_id, count(*) c FROM p GROUP BY 1),
        t AS (
          SELECT a.product_id pa, b.product_id pb, count(*) co,
                 count(*) * (SELECT n FROM n) / (fa.c * fb.c)::DOUBLE AS lift
          FROM p a JOIN p b ON a.user_session = b.user_session AND a.product_id <> b.product_id
          JOIN f fa ON fa.product_id = a.product_id
          JOIN f fb ON fb.product_id = b.product_id
          GROUP BY a.product_id, b.product_id, fa.c, fb.c),
        g AS (SELECT * FROM {pq(GOLD / 'product_affinity')})
        SELECT count_if(t.co IS NOT NULL AND g.co_count = t.co
                        AND abs(g.lift - t.lift) <= 0.01 * t.lift), count(*)
        FROM g LEFT JOIN t ON g.product_a = t.pa AND g.product_b = t.pb""").fetchone()
    return line("BR7 product_affinity", ok, total, "per gold row: co_count exact, lift within 1%")

# ---------------- BR8 ----------------
def br8(con, cs, day, replay_end):
    gold = {(r.window_start, r.user_id): (r.order_count, float(r.total_value))
            for r in cs.execute("SELECT window_start, user_id, order_count, total_value "
                                "FROM order_velocity_alerts WHERE event_date = %s", (day,))}
    if not gold:
        return line("BR8 order_velocity_alerts", 0, 0, "gold is empty: replay first")
    end = replay_end or max(k[0] for k in gold)
    min_n = min(v[0] for v in gold.values())
    # NO dedup here: the stream also counts the exact-duplicate rows.
    truth = {(ws, u): (n, float(v)) for ws, u, n, v in con.execute(f"""
        SELECT time_bucket(INTERVAL 5 MINUTE, event_time) ws, user_id, count(*), sum(price)
        FROM {pq(SILVER)}
        WHERE event_type = 'purchase' AND event_date = DATE '{day}'
        GROUP BY 1, 2 HAVING count(*) >= {min_n}""").fetchall()}
    # closed windows only: window end + 10 min watermark <= end of replay
    closed = lambda ws: ws + dt.timedelta(minutes=15) <= end
    g = {k: v for k, v in gold.items() if closed(k[0])}
    t = {k: v for k, v in truth.items() if closed(k[0])}
    ok = sum(1 for k in g if k in t and g[k][0] == t[k][0] and abs(g[k][1] - t[k][1]) < 0.01)
    return line("BR8 order_velocity_alerts", ok, len(set(g) | set(t)),
                f"closed windows up to {end}, min order_count {min_n}")

# ---------------- BR4 ----------------
def br4(con):
    # TODO: scores and segment need the rule in processing/dim_user.py (see below).
    ok, total = con.execute(f"""
        WITH cur AS (SELECT user_id, snapshot_date FROM {pq(DW / 'dim_user')} WHERE is_current),
        uid AS (SELECT DISTINCT user_sk, user_id FROM {pq(DW / 'dim_user')}),
        t AS (
          SELECT u.user_id, count(*) f, sum(e.price) m,
                 date_diff('day', max(e.event_date), c.snapshot_date) r
          FROM {pq(DW / 'fact_event')} e
          JOIN uid u USING (user_sk)
          JOIN cur c ON c.user_id = u.user_id
          WHERE e.event_type_key = 3 AND e.event_date <= c.snapshot_date
          GROUP BY u.user_id, c.snapshot_date),
        g AS (SELECT * FROM {pq(GOLD / 'rfm_segments')} WHERE frequency > 0)
        SELECT count_if(t.user_id IS NOT NULL AND g.frequency = t.f
                        AND abs(g.monetary - t.m) < 0.01 AND g.recency_days = t.r), count(*)
        FROM g LEFT JOIN t USING (user_id)""").fetchone()
    return line("BR4 rfm_segments", ok, total,
                "buyers: frequency, monetary, recency as of each user's current snapshot")

def safe(name, fn, *args):
    try:
        return fn(*args)
    except Exception as e:
        print(f"MISS {name}: {type(e).__name__}: {str(e).splitlines()[0][:150]}")
        return 0.0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="2019-11-17")
    ap.add_argument("--replay-end", default=None, help="'YYYY-MM-DD HH:MM:SS', Vietnam time")
    a = ap.parse_args()
    end = dt.datetime.fromisoformat(a.replay_end) if a.replay_end else None
    day = dt.date.fromisoformat(a.date)
    con = duckdb.connect()
    try:
        cs = cassandra()
    except Exception as e:
        print(f"MISS Cassandra not reachable ({type(e).__name__}). Run: docker compose up -d --wait")
        cs = None
    pcts = [
        safe("BR4", br4, con),
        safe("BR6", br6, con, cs) if cs else 0.0,
        safe("BR7", br7, con),
        safe("BR8", br8, con, cs, day, end) if cs else 0.0,
    ]
    sys.exit(0 if all(p >= THRESHOLD for p in pcts) else 1)

if __name__ == "__main__":
    main()