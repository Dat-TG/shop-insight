"""Gate 4, correctness: every BR's stored result against an independent answer.

    python checks/correctness_8br.py --replay-start "2019-11-17 15:00:00" --replay-end "2019-11-17 21:30:00" \
        --watermark "2019-11-17 21:19:59"

The independent answer is plain DuckDB SQL over data/silver/ (and, for BR6, the
inventory series in data/inventory/), written from each BR's definition in
docs/BR_SCOPE.md and API_CONTRACT, not from the Spark code. Nothing here imports
processing/. The system side is what the screens read: the gold Parquet tables
(BR2, BR4, BR7) and the Cassandra tables (BR1, BR3, BR5, BR6, BR8).

The four streaming BRs are compared over one replay. Run, in this order:
    python processing/streaming_gold.py --fresh
    python ingestion/replayer.py --speed 60 --start "2019-11-17 08:00:00"   # stop after the 21:30 file
Then pass the replayed span (Vietnam time, as silver stores it) and the final
watermark the stream log printed. BR3 and BR5 write a window only once the
watermark closes it, so their answer stops at that watermark too.

A row matches when its key and every compared value are equal (decimals to the
cent, floats to 1e-4 relative). The score per BR is matched / max(answer rows,
stored rows), so a missing row and an extra row both count against it. The
threshold is 99%. Prints CORRECTNESS OK when all eight pass.
"""

import argparse
import math
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import duckdb
from cassandra.cluster import EXEC_PROFILE_DEFAULT, Cluster, ExecutionProfile
from cassandra.policies import DCAwareRoundRobinPolicy

from serving.check_infra import read_env

DATA = REPO / "data"
SILVER = f"read_parquet('{DATA}/silver/**/*.parquet', hive_partitioning=true)"
INVENTORY = f"read_parquet('{DATA}/inventory/**/*.parquet', hive_partitioning=true)"
THRESHOLD = 99.0
LAST_SNAPSHOT = date(2019, 11, 30)
NO_STOCKOUT = 9999.0          # the Cassandra sentinel for "never runs out" (SYSTEM_DESIGN 6.1)
TRENDING_TOP = 20
MIN_PRODUCT_SESSIONS = 20     # BR7 cut-offs, API_CONTRACT section 9
MIN_CO_COUNT = 3


def gold(name):
    return f"read_parquet('{DATA}/gold/{name}/**/*.parquet', hive_partitioning=true)"


def norm(value):
    """One comparable form per value: cents for money, naive seconds for times. Floats stay floats."""
    if isinstance(value, Decimal):
        return round(float(value), 2)
    if isinstance(value, datetime):
        return value.replace(tzinfo=None, microsecond=0)
    return value


def same(a, b):
    """Equal values; floats within 1e-4 relative (Cassandra float is 32-bit, DuckDB computes in 64)."""
    if a is None or b is None or len(a) != len(b):
        return a == b
    return all(math.isclose(x, y, rel_tol=1e-4) if isinstance(x, float) and isinstance(y, float) else x == y
               for x, y in zip(a, b))


def as_map(rows, key_len):
    return {tuple(norm(v) for v in r[:key_len]): tuple(norm(v) for v in r[key_len:]) for r in rows}


def score(name, compared, answer, stored, key_len):
    """matched / max(len): extra and missing rows both lower the score. Returns a result dict."""
    a, s = as_map(answer, key_len), as_map(stored, key_len)
    matched = sum(1 for k, v in a.items() if same(v, s.get(k)))
    total = max(len(a), len(s))
    pct = 100.0 * matched / total if total else 0.0
    wrong = [(k, a.get(k), s.get(k)) for k in sorted(set(a) | set(s), key=str) if not same(a.get(k), s.get(k))]
    return {"br": name, "compared": compared, "answer": len(a), "stored": len(s), "matched": matched,
            "pct": pct, "examples": wrong[:3], "wrong": len(wrong)}


def cassandra_rows(session, cql):
    return [tuple(r) for r in session.execute(cql)]


# ---------------------------------------------------------------------------
# Batch BRs: whole month, gold Parquet
# ---------------------------------------------------------------------------

def br2_funnel(con):
    """Sessions that reached each step, per session start date, overall and per top category."""
    answer = con.sql(f"""
        WITH ev AS (SELECT user_session, event_time, event_date, event_type, category_l1 FROM {SILVER}),
        start AS (SELECT user_session, arg_min(event_date, event_time) AS d FROM ev GROUP BY 1),
        per AS (
            SELECT user_session, category_l1,
                   count(*) FILTER (WHERE event_type = 'view')     AS v,
                   count(*) FILTER (WHERE event_type = 'cart')     AS c,
                   count(*) FILTER (WHERE event_type = 'purchase') AS p
            FROM ev GROUP BY GROUPING SETS ((user_session), (user_session, category_l1))
        ),
        staged AS (
            SELECT s.d, coalesce(per.category_l1, 'all') AS cat, v, c, p,
                   CASE WHEN p > 0 THEN 3 WHEN c > 0 THEN 2 WHEN v > 0 THEN 1 ELSE 0 END AS stage
            FROM per JOIN start s USING (user_session)
        )
        SELECT d, cat, count(*) FILTER (WHERE stage >= 1), count(*) FILTER (WHERE stage >= 2),
               count(*) FILTER (WHERE stage = 3), sum(v), sum(c), sum(p)
        FROM staged GROUP BY 1, 2
    """).fetchall()
    stored = con.sql(f"""SELECT event_date, category_l1, views, carts, purchases,
                                view_events, cart_events, purchase_events FROM {gold('funnel_daily')}""").fetchall()
    return score("BR2", "sessions and events per (start date, category), incl. 'all'", answer, stored, 2)


def br4_rfm(con):
    """RFM at the last snapshot. Scores and segment are what the heatmap shows."""
    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE rfm_answer AS
        WITH users AS (SELECT DISTINCT user_id FROM {SILVER}),
        buys AS (
            SELECT user_id, max(event_date) AS last_buy, count(*) AS f, sum(price) AS m
            FROM {SILVER} WHERE event_type = 'purchase' AND event_date <= DATE '{LAST_SNAPSHOT}' GROUP BY 1
        ),
        raw AS (
            SELECT u.user_id, date_diff('day', b.last_buy, DATE '{LAST_SNAPSHOT}') AS r_days,
                   coalesce(b.f, 0) AS f, coalesce(b.m, 0) AS m, b.user_id IS NOT NULL AS buyer
            FROM users u LEFT JOIN buys b USING (user_id)
        ),
        scored AS (
            SELECT *,
                CASE WHEN buyer THEN ntile(5) OVER (PARTITION BY buyer ORDER BY r_days DESC, user_id) END AS r,
                CASE WHEN buyer THEN ntile(5) OVER (PARTITION BY buyer ORDER BY f, user_id) END AS fs,
                CASE WHEN buyer THEN ntile(5) OVER (PARTITION BY buyer ORDER BY m, user_id) END AS ms
            FROM raw
        )
        SELECT user_id, r_days, f, m, r, fs, ms,
            CASE WHEN NOT buyer THEN 'no_purchase'
                 WHEN r >= 4 AND fs >= 4 THEN 'champion'
                 WHEN r >= 3 AND fs >= 3 THEN 'loyal'
                 WHEN r >= 4 AND fs <= 2 THEN 'promising'
                 WHEN r = 3 AND fs <= 2 THEN 'needs_attention'
                 WHEN r <= 2 AND fs >= 3 THEN 'at_risk'
                 ELSE 'hibernating' END AS segment
        FROM scored
    """)
    answer = con.sql("SELECT user_id, r, fs, ms, segment FROM rfm_answer").fetchall()
    stored = con.sql(f"SELECT user_id, r_score, f_score, m_score, segment FROM {gold('rfm_segments')}").fetchall()
    result = score("BR4", "r, f, m score and segment per user (the heatmap and its filter)", answer, stored, 1)
    raw_answer = con.sql("SELECT user_id, r_days, f, m FROM rfm_answer").fetchall()
    raw_stored = con.sql(f"SELECT user_id, recency_days, frequency, monetary FROM {gold('rfm_segments')}").fetchall()
    result["side"] = score("BR4 raw", "recency_days, frequency, monetary per user", raw_answer, raw_stored, 1)
    return result


def br7_affinity(con):
    """Pairs bought in the same session, with support and lift, both directions."""
    answer = con.sql(f"""
        WITH baskets AS (SELECT DISTINCT user_session, product_id FROM {SILVER} WHERE event_type = 'purchase'),
        n AS (SELECT count(DISTINCT user_session) AS n FROM baskets),
        popular AS (SELECT product_id, count(*) AS k FROM baskets GROUP BY 1 HAVING count(*) >= {MIN_PRODUCT_SESSIONS}),
        kept AS (SELECT b.* FROM baskets b JOIN popular USING (product_id)),
        pairs AS (
            SELECT a.product_id AS pa, b.product_id AS pb, count(*) AS co
            FROM kept a JOIN kept b ON a.user_session = b.user_session AND a.product_id < b.product_id
            GROUP BY 1, 2 HAVING count(*) >= {MIN_CO_COUNT}
        ),
        scored AS (
            SELECT pa, pb, co, co / n.n AS support, co * n.n / (x.k * y.k) AS lift
            FROM pairs, n, popular x, popular y WHERE x.product_id = pa AND y.product_id = pb
        )
        SELECT pa, pb, co, support, lift FROM scored WHERE lift > 1
        UNION ALL
        SELECT pb, pa, co, support, lift FROM scored WHERE lift > 1
    """).fetchall()
    stored = con.sql(f"SELECT product_a, product_b, co_count, support, lift FROM {gold('product_affinity')}").fetchall()
    return score("BR7", "co_count, support, lift per ordered pair", answer, stored, 2)


def br6_stockout(con, cass):
    """Days to stock-out on the last day, units sold rebuilt from the inventory balance itself."""
    answer = con.sql(f"""
        WITH inv AS (
            SELECT *, lag(stock_on_hand) OVER (PARTITION BY product_id, warehouse_id ORDER BY snapshot_date) AS prev
            FROM {INVENTORY}
        ),
        sold AS (  -- stock today = stock yesterday + received - sold
            SELECT product_id, warehouse_id, snapshot_date, stock_on_hand, prev + units_received - stock_on_hand AS units
            FROM inv
        ),
        last AS (
            SELECT warehouse_id, product_id, arg_max(stock_on_hand, snapshot_date) AS stock,
                   sum(units) FILTER (WHERE snapshot_date > DATE '{LAST_SNAPSHOT}' - 7) / 7.0 AS v
            FROM sold GROUP BY 1, 2
        )
        SELECT warehouse_id, product_id, CASE WHEN v > 0 THEN stock / v ELSE {NO_STOCKOUT} END, stock, v FROM last
    """).fetchall()
    answer = [(w, p, float(d), s, float(v)) for w, p, d, s, v in answer]
    stored = cassandra_rows(cass, "SELECT warehouse_id, product_id, days_to_stockout, stock_on_hand, velocity_7d "
                                  "FROM stockout_risk")
    return score("BR6", "days_to_stockout, stock, velocity per (warehouse, product) on 30 Nov", answer, stored, 2)


# ---------------------------------------------------------------------------
# Streaming BRs: one replay, Cassandra
# ---------------------------------------------------------------------------

def replayed(start, end):
    return f"(SELECT * FROM {SILVER} WHERE event_time >= TIMESTAMP '{start}' AND event_time < TIMESTAMP '{end}')"


def br1_gmv(con, cass, start, end):
    """GMV and orders per minute and top category, plus the 'all' row; minutes with any event."""
    answer = con.sql(f"""
        WITH ev AS {replayed(start, end)}
        SELECT event_date, coalesce(category_l1, 'all'), date_trunc('minute', event_time),
               coalesce(sum(price) FILTER (WHERE event_type = 'purchase'), 0),
               count(*) FILTER (WHERE event_type = 'purchase')
        FROM ev GROUP BY GROUPING SETS ((event_date, date_trunc('minute', event_time), category_l1),
                                        (event_date, date_trunc('minute', event_time)))
    """).fetchall()
    stored = cassandra_rows(cass, "SELECT event_date, category_l1, window_start, gmv, order_count FROM gmv_by_minute")
    stored = [(_date(r[0]), *r[1:]) for r in stored]
    return score("BR1", "gmv and order_count per (day, category incl. 'all', minute)", answer, stored, 3)


def br3_trending(con, cass, start, end, watermark):
    """Top 20 by views, then carts, then product_id, per 15-minute window sliding every minute."""
    answer = con.sql(f"""
        WITH ev AS (SELECT * FROM {replayed(start, end)} WHERE event_type IN ('view', 'cart')),
        starts AS (SELECT unnest(generate_series(date_trunc('minute', TIMESTAMP '{start}') - INTERVAL 14 MINUTE,
                                                 TIMESTAMP '{watermark}' - INTERVAL 15 MINUTE, INTERVAL 1 MINUTE)) AS ws),
        counts AS (
            SELECT ws, product_id, count(*) FILTER (WHERE event_type = 'view') AS v,
                   count(*) FILTER (WHERE event_type = 'cart') AS c
            FROM starts JOIN ev ON ev.event_time >= ws AND ev.event_time < ws + INTERVAL 15 MINUTE
            WHERE ws + INTERVAL 15 MINUTE <= TIMESTAMP '{watermark}'
            GROUP BY 1, 2
        )
        SELECT ws, rk, product_id, v, c FROM (
            SELECT *, row_number() OVER (PARTITION BY ws ORDER BY v DESC, c DESC, product_id) AS rk FROM counts
        ) WHERE rk <= {TRENDING_TOP}
    """).fetchall()
    stored = cassandra_rows(cass, "SELECT window_start, rank, product_id, view_count, cart_count FROM trending_products")
    return score("BR3", "product, views, carts per (window, rank), windows closed by the watermark", answer, stored, 2)


def br5_carts(con, cass, start, end, watermark):
    """Sessions split at 30-minute gaps; a split with a cart, no purchase, closed by the watermark."""
    answer = con.sql(f"""
        WITH ev AS {replayed(start, end)},
        marked AS (
            SELECT *, CASE WHEN lag(event_time) OVER w IS NULL
                            OR event_time >= lag(event_time) OVER w + INTERVAL 30 MINUTE THEN 1 ELSE 0 END AS new_split
            FROM ev WINDOW w AS (PARTITION BY user_session ORDER BY event_time)
        ),
        numbered AS (SELECT *, sum(new_split) OVER (PARTITION BY user_session ORDER BY event_time
                                                   ROWS UNBOUNDED PRECEDING) AS split FROM marked),
        splits AS (
            SELECT user_session, split, max(event_time) AS last_at, max(user_id) AS user_id,
                   sum(price) FILTER (WHERE event_type = 'cart') AS cart_value,
                   count(DISTINCT product_id) FILTER (WHERE event_type = 'cart') AS items,
                   count(*) FILTER (WHERE event_type = 'cart') AS carts,
                   count(*) FILTER (WHERE event_type = 'purchase') AS buys
            FROM numbered GROUP BY 1, 2
        ),
        closed AS (
            SELECT * FROM splits
            WHERE carts > 0 AND buys = 0 AND last_at + INTERVAL 30 MINUTE <= TIMESTAMP '{watermark}'
        )
        SELECT CAST(last_at AS DATE), user_session, arg_max(cart_value, last_at), arg_max(user_id, last_at),
               arg_max(items, last_at), max(last_at)
        FROM closed GROUP BY 1, 2
    """).fetchall()
    stored = cassandra_rows(cass, "SELECT event_date, user_session, cart_value, user_id, item_count, last_event_at "
                                  "FROM abandoned_carts")
    stored = [(_date(r[0]), *r[1:]) for r in stored]
    return score("BR5", "cart_value, user, items, last event per (day, session)", answer, stored, 2)


def br8_velocity(con, cass, start, end):
    """Purchases per user in 5-minute tumbling windows, with the low / medium / high label."""
    answer = con.sql(f"""
        WITH ev AS (SELECT * FROM {replayed(start, end)} WHERE event_type = 'purchase'),
        w AS (
            SELECT event_date, time_bucket(INTERVAL 5 MINUTE, event_time) AS ws, user_id,
                   count(*) AS n, sum(price) AS total
            FROM ev GROUP BY 1, 2, 3
        )
        SELECT event_date, ws, user_id, n, total,
               CASE WHEN n >= 10 THEN 'high' WHEN n >= 3 THEN 'medium' ELSE 'low' END FROM w
    """).fetchall()
    stored = cassandra_rows(cass, "SELECT event_date, window_start, user_id, order_count, total_value, severity "
                                  "FROM order_velocity_alerts")
    stored = [(_date(r[0]), *r[1:]) for r in stored]
    return score("BR8", "order_count, total_value, severity per (day, 5-minute window, user)", answer, stored, 3)


def _date(value):
    """cassandra-driver returns a Date object for a date column; make it a datetime.date."""
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def connect():
    env = read_env()
    profile = ExecutionProfile(load_balancing_policy=DCAwareRoundRobinPolicy(local_dc="datacenter1"),
                               request_timeout=60)
    cluster = Cluster([env["CASSANDRA_HOST"]], port=int(env["CASSANDRA_PORT"]),
                      execution_profiles={EXEC_PROFILE_DEFAULT: profile})
    return cluster, cluster.connect(env["CASSANDRA_KEYSPACE"])


def print_result(r):
    flag = "" if r["pct"] >= THRESHOLD else "   BELOW 99%"
    print(f"{r['br']:<8}{r['answer']:>10,}{r['stored']:>10,}{r['matched']:>10,}{r['pct']:>9.2f}%{flag}   {r['compared']}")
    for k, a, s in r["examples"]:
        print(f"{'':8}  differs: key {k}  answer {a}  stored {s}")


def main():
    parser = argparse.ArgumentParser(description="Compare every BR's stored result with an independent answer.")
    parser.add_argument("--replay-start", required=True, help="first replayed event time, Vietnam time")
    parser.add_argument("--replay-end", required=True, help="end of the replayed span (exclusive), Vietnam time")
    parser.add_argument("--watermark", required=True, help="the stream's final watermark, Vietnam time")
    args = parser.parse_args()

    con = duckdb.connect()
    cluster, cass = connect()
    try:
        results = [
            br1_gmv(con, cass, args.replay_start, args.replay_end),
            br2_funnel(con),
            br3_trending(con, cass, args.replay_start, args.replay_end, args.watermark),
            br4_rfm(con),
            br5_carts(con, cass, args.replay_start, args.replay_end, args.watermark),
            br6_stockout(con, cass),
            br7_affinity(con),
            br8_velocity(con, cass, args.replay_start, args.replay_end),
        ]
    finally:
        cluster.shutdown()

    print(f"replay {args.replay_start} .. {args.replay_end} (Vietnam time), final watermark {args.watermark}")
    print(f"{'BR':<8}{'answer':>10}{'stored':>10}{'matched':>10}{'match':>10}   compared")
    for r in results:
        print_result(r)
    side = results[3]["side"]
    print(f"{'':8}  BR4 raw values (shown in the cell list, not in the heatmap):")
    print_result(side)
    ok = all(r["pct"] >= THRESHOLD for r in results)
    print("CORRECTNESS OK" if ok else "CORRECTNESS BELOW THRESHOLD")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
