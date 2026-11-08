"""DuckDB ground truth for BR4, BR6, BR7 and BR8 (T13): each stored result against an answer in SQL.

    python checks/ground_truth.py --replay-start "2019-11-17 15:00:00" --replay-end "2019-11-17 21:30:00"

Each answer is plain DuckDB SQL over the warehouse Parquet (BR4, BR6, BR7) or silver (BR8), written
from the BR's definition, not copied from the Spark code. It is compared with what the screen reads:
the gold Parquet for BR4 and BR7, Cassandra for BR6 and BR8. One line per BR: OK or LOW with the
match (threshold 99%), matched/total and what was compared, or MISS when it could not run. A
missing, an extra or a duplicated stored row counts against the score. Prints GROUND TRUTH OK and
exits 0 only when all four pass.

What each line covers:
  BR4  recency_days, frequency and monetary of every buyer, as of the snapshot_date that the user's
       current dim_user row records. Not the scores or the segment, and not "as of 30 Nov": a user
       whose RFM cell did not change keeps an earlier snapshot's values. checks/correctness_8br.py
       compares the scores and segment, and measures that gap on its "BR4 raw" line.
  BR6  days_to_stockout per (warehouse, product) on the last day of fact_inventory_daily, 9999.0
       when velocity_7d is 0.
  BR7  co_count, support and lift of every pair the rules keep: products bought in >= 20 sessions,
       pairs seen >= 3 times, lift > 1, both directions.
  BR8  order_count and total_value per (5-minute window, user) on --date, for every window with a
       purchase that lies wholly inside the replay.

BR8 needs the span the stream was fed, in Vietnam time as silver and Cassandra store it; it is
not read back from the table under test. ./run_demo.sh stream replays from 08:00 UTC on 17 Nov,
which is 15:00 Vietnam time, and the end is where the replayer stopped. Start the stream with
--fresh before the replay, or an earlier replay's rows stay in the table, and run this check
once the stream has processed the last replayed file.
"""

import argparse
import datetime as dt
import math
import sys
from decimal import Decimal
from pathlib import Path

import duckdb

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
DW, GOLD, SILVER = REPO / "data/warehouse", REPO / "data/gold", REPO / "data/silver"
THRESHOLD = 99.0
BR8_WINDOW = dt.timedelta(minutes=5)
MIN_PRODUCT_SESSIONS = 20               # BR7 cut-offs, processing/gold_br7.py
MIN_CO_COUNT = 3


def pq(path):
    return f"read_parquet('{path}/**/*.parquet', hive_partitioning=true)"


def cents(value):
    return Decimal(value).quantize(Decimal("0.01"))


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
    rows = []
    for wh in range(1, 6):
        rows += cs.execute("SELECT warehouse_id, product_id, days_to_stockout "
                           "FROM stockout_risk WHERE warehouse_id = %s", (wh,))
    # Rows, not keys: the clustering key holds days_to_stockout, so a stale row left by a failed
    # delete is a second row for the same product. Counting rows lets it lower the score.
    gold = {(r.warehouse_id, r.product_id): r.days_to_stockout for r in rows}
    ok = sum(1 for k, g in gold.items()
             if k in truth and math.isclose(g, truth[k], rel_tol=1e-4, abs_tol=1e-3))
    total = max(len(rows), len(truth))
    return line("BR6 stockout_risk", ok, total,
                f"gold {len(rows):,} rows, truth {len(truth):,} rows")


# ---------------- BR7 ----------------
def br7(con):
    ok, gold_rows, truth_rows = con.execute(f"""
        WITH p AS (  -- distinct (session, product): a repeat buy in one session counts once, as in gold_br7
          SELECT DISTINCT e.user_session, d.product_id
          FROM {pq(DW / 'fact_event')} e
          JOIN {pq(DW / 'dim_product')} d USING (product_sk)
          WHERE e.event_type_key = 3),
        n AS (SELECT count(DISTINCT user_session) n FROM p),
        f AS (SELECT product_id, count(*) c FROM p GROUP BY 1 HAVING count(*) >= {MIN_PRODUCT_SESSIONS}),
        t AS (
          SELECT a.product_id pa, b.product_id pb, count(*) co,
                 count(*) / (SELECT n FROM n)::DOUBLE AS support,
                 count(*) * (SELECT n FROM n) / (fa.c * fb.c)::DOUBLE AS lift
          FROM p a JOIN p b ON a.user_session = b.user_session AND a.product_id <> b.product_id
          JOIN f fa ON fa.product_id = a.product_id
          JOIN f fb ON fb.product_id = b.product_id
          GROUP BY a.product_id, b.product_id, fa.c, fb.c
          HAVING count(*) >= {MIN_CO_COUNT}),
        kept AS (SELECT * FROM t WHERE lift > 1),
        g AS (SELECT * FROM {pq(GOLD / 'product_affinity')})
        SELECT count(DISTINCT (k.pa, k.pb)) FILTER (
                 WHERE g.co_count = k.co
                   AND abs(g.support - k.support) <= 1e-4 * k.support
                   AND abs(g.lift - k.lift) <= 1e-4 * k.lift),
               (SELECT count(*) FROM g), (SELECT count(*) FROM kept)
        FROM kept k LEFT JOIN g ON g.product_a = k.pa AND g.product_b = k.pb""").fetchone()
    return line("BR7 product_affinity", ok, max(gold_rows, truth_rows),
                f"gold {gold_rows:,} rows, truth {truth_rows:,} rows: co_count, support, lift per pair")


# ---------------- BR8 ----------------
def br8(con, cs, day, start, end):
    gold = {(r.window_start, r.user_id): (r.order_count, cents(r.total_value))
            for r in cs.execute("SELECT window_start, user_id, order_count, total_value "
                                "FROM order_velocity_alerts WHERE event_date = %s", (day,))}
    # NO dedup here: the stream also counts the exact-duplicate rows.
    # Every window with a purchase: API_CONTRACT section 10 labels even 1 order (low).
    truth = {(ws, u): (n, cents(v)) for ws, u, n, v in con.execute(f"""
        SELECT time_bucket(INTERVAL 5 MINUTE, event_time) ws, user_id, count(*), sum(price)
        FROM {pq(SILVER)}
        WHERE event_type = 'purchase' AND event_date = DATE '{day}'
        GROUP BY 1, 2""").fetchall()}

    def inside(ws):
        # Every event of the window was replayed: it starts at or after the first one sent and
        # ends by the end of the replay. BR8 writes in update mode, so its stored row then holds
        # the final count; no need to wait for the watermark, which only append mode does.
        return ws >= start and ws + BR8_WINDOW <= end

    g = {k: v for k, v in gold.items() if inside(k[0])}
    t = {k: v for k, v in truth.items() if inside(k[0])}
    ok = sum(1 for k in g if k in t and g[k] == t[k])
    return line("BR8 order_velocity_alerts", ok, len(set(g) | set(t)),
                f"windows inside {start} .. {end}, gold {len(g):,}, truth {len(t):,}")


# ---------------- BR4 ----------------
def br4(con):
    # Raw values only, as of each user's own snapshot_date; see the module docstring for the scores.
    ok, gold_rows, truth_rows = con.execute(f"""
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
        -- Each buyer matched once, over the larger row count: a missing, an extra or a
        -- duplicated gold row lowers the score.
        SELECT count(DISTINCT t.user_id) FILTER (
                 WHERE g.frequency = t.f AND g.monetary = t.m AND g.recency_days = t.r),
               (SELECT count(*) FROM g), (SELECT count(*) FROM t)
        FROM t LEFT JOIN g ON g.user_id = t.user_id""").fetchone()
    return line("BR4 rfm_segments", ok, max(gold_rows, truth_rows),
                f"gold {gold_rows:,} buyers, truth {truth_rows:,}: frequency, monetary, recency "
                "as of each user's current snapshot")


def safe(name, fn, *args):
    """Run one BR's comparison; on an error print a MISS line and return None."""
    try:
        return fn(*args)
    except Exception as e:
        print(f"MISS {name}: {type(e).__name__}: {(str(e).splitlines() or [''])[0][:150]}")
        return None


def main():
    ap = argparse.ArgumentParser(description="DuckDB ground truth for BR4, BR6, BR7 and BR8.")
    ap.add_argument("--date", default="2019-11-17", help="the replayed day, for BR8")
    ap.add_argument("--replay-start", required=True,
                    help="'YYYY-MM-DD HH:MM:SS', Vietnam time: the replayer's --start (UTC) plus 7 hours")
    ap.add_argument("--replay-end", required=True,
                    help="'YYYY-MM-DD HH:MM:SS', Vietnam time: the end of the replay (exclusive)")
    a = ap.parse_args()
    start = dt.datetime.fromisoformat(a.replay_start)
    end = dt.datetime.fromisoformat(a.replay_end)
    day = dt.date.fromisoformat(a.date)
    con = duckdb.connect()
    try:
        cs = cassandra()
    except Exception as e:
        print(f"MISS Cassandra not reachable ({type(e).__name__}). Run: docker compose up -d --wait")
        cs = None
    br6_pct = br8_pct = None              # None = could not run (MISS)
    br4_pct = safe("BR4", br4, con)
    if cs:
        br6_pct = safe("BR6", br6, con, cs)
    br7_pct = safe("BR7", br7, con)
    if cs:
        br8_pct = safe("BR8", br8, con, cs, day, start, end)
    else:
        print("MISS BR6, BR8: no Cassandra")
    pcts = [br4_pct, br6_pct, br7_pct, br8_pct]
    if None in pcts:
        print("GROUND TRUTH INCOMPLETE")
        sys.exit(1)
    ok = all(p >= THRESHOLD for p in pcts)
    print("GROUND TRUTH OK" if ok else "GROUND TRUTH BELOW THRESHOLD")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
