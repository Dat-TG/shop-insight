"""The same screen question answered two ways: read the gold table, or compute it at read time.

Measures, for BR2, BR4 and BR7 on the 7% sample, the in-process DuckDB time (3 warm-up runs,
then 20 timed runs, nearest-rank p50 / p95, wall time around execute + fetchall; no API, no HTTP)
of:
  - BR2: the 1-30 Nov funnel, all categories: gold funnel_daily, star fact_session_funnel, silver
  - BR4: the customers with R score 5 on 30 Nov: gold rfm_segments, silver with RFM scored at read time
  - BR7: the ten partners of product 1005115: gold product_affinity, silver with pairs built at read time
and checks that both ways return the same answer. It also prints the BR7 rows the screen shows
for 1005115 (ordered by lift, as serving/api/routers/br7.py does).

Used by report edits R5-E1 (section 6.2.1, Bảng 17b) and R5-E13b (Bảng 18, BR7 cell). Read-only.

Run from the repo root:  .venv/bin/python -I docs/evidence/review_20261113/r5_gold_vs_onthefly.py
"""
import math
import os
import platform
import time

import duckdb

S = "read_parquet('data/silver/**/*.parquet', hive_partitioning=true)"
FSF = "read_parquet('data/warehouse/fact_session_funnel/**/*.parquet', hive_partitioning=true)"
G2 = "read_parquet('data/gold/funnel_daily/**/*.parquet', hive_partitioning=true)"
G4 = "read_parquet('data/gold/rfm_segments/snapshot_date=2019-11-30/*.parquet')"
G7 = "read_parquet('data/gold/product_affinity/*.parquet')"

BR2_GOLD = f"""SELECT sum(views), sum(carts), sum(purchases), sum(view_events), sum(cart_events), sum(purchase_events)
FROM {G2} WHERE category_l1 = 'all' AND event_date BETWEEN DATE '2019-11-01' AND DATE '2019-11-30'"""
BR2_STAR = f"""SELECT count(*) FILTER (WHERE funnel_stage >= 1), count(*) FILTER (WHERE funnel_stage >= 2),
  count(*) FILTER (WHERE funnel_stage = 3), sum(view_count), sum(cart_count), sum(purchase_count)
FROM {FSF} WHERE session_start_date BETWEEN DATE '2019-11-01' AND DATE '2019-11-30'"""
BR2_SILVER = f"""WITH per AS (SELECT user_session, arg_min(event_date, event_time) AS d,
    count(*) FILTER (WHERE event_type = 'view') v, count(*) FILTER (WHERE event_type = 'cart') c,
    count(*) FILTER (WHERE event_type = 'purchase') p FROM {S} GROUP BY 1)
SELECT count(*) FILTER (WHERE v + c + p > 0), count(*) FILTER (WHERE c > 0 OR p > 0), count(*) FILTER (WHERE p > 0),
  sum(v), sum(c), sum(p)
FROM per WHERE d BETWEEN DATE '2019-11-01' AND DATE '2019-11-30'"""

BR4_GOLD = f"""SELECT user_id, recency_days, frequency, monetary FROM {G4}
WHERE r_score = 5 ORDER BY monetary DESC, user_id"""
BR4_SILVER = f"""WITH buys AS (
    SELECT user_id, max(event_date) AS last_buy, count(*) AS f, sum(price) AS m
    FROM {S} WHERE event_type = 'purchase' AND event_date <= DATE '2019-11-30' GROUP BY 1),
  raw AS (SELECT user_id, date_diff('day', last_buy, DATE '2019-11-30') AS r_days, f, m FROM buys),
  scored AS (SELECT *, ntile(5) OVER (ORDER BY r_days DESC, user_id) AS r FROM raw)
SELECT user_id, r_days, f, m FROM scored WHERE r = 5 ORDER BY m DESC, user_id"""

BR7_GOLD = f"""SELECT product_b, co_count, lift FROM {G7}
WHERE product_a = 1005115 ORDER BY lift DESC, co_count DESC LIMIT 10"""
BR7_SILVER = f"""WITH baskets AS (SELECT DISTINCT user_session, product_id FROM {S} WHERE event_type = 'purchase'),
  n AS (SELECT count(DISTINCT user_session) AS n FROM baskets),
  popular AS (SELECT product_id, count(*) AS k FROM baskets GROUP BY 1 HAVING count(*) >= 20),
  kept AS (SELECT b.* FROM baskets b JOIN popular USING (product_id)),
  pairs AS (SELECT a.product_id pa, b.product_id pb, count(*) co FROM kept a JOIN kept b
    ON a.user_session = b.user_session AND a.product_id <> b.product_id
    WHERE a.product_id = 1005115 GROUP BY 1, 2 HAVING count(*) >= 3)
SELECT pb, co, co * n.n / (x.k * y.k) AS lift FROM pairs, n, popular x, popular y
WHERE x.product_id = pa AND y.product_id = pb AND co * n.n / (x.k * y.k) > 1
ORDER BY lift DESC, co DESC LIMIT 10"""

QUERIES = [
    ("BR2 gold funnel_daily", BR2_GOLD),
    ("BR2 star fact_session_funnel", BR2_STAR),
    ("BR2 silver, per session at read time", BR2_SILVER),
    ("BR4 gold rfm_segments, r_score = 5", BR4_GOLD),
    ("BR4 silver, RFM scored at read time", BR4_SILVER),
    ("BR7 gold product_affinity, 1005115", BR7_GOLD),
    ("BR7 silver, pairs at read time", BR7_SILVER),
]


def nearest_rank(values, p):
    ordered = sorted(values)
    return ordered[math.ceil(p * len(ordered) / 100) - 1]


def timed(con, sql):
    for _ in range(3):
        rows = con.execute(sql).fetchall()
    ms = []
    for _ in range(20):
        t0 = time.perf_counter()
        rows = con.execute(sql).fetchall()
        ms.append((time.perf_counter() - t0) * 1000)
    return rows, ms


def main():
    print(f"machine  {platform.node()} | {os.cpu_count()} logical cores")
    print(f"versions Python {platform.python_version()} | DuckDB {duckdb.__version__}")
    print("method   3 warm-up + 20 timed runs per query, in-process, ms, nearest rank")
    print("load     1-min load average before: %.2f (other processes on the machine)" % os.getloadavg()[0])
    con = duckdb.connect()
    result = {}
    for name, sql in QUERIES:
        rows, ms = timed(con, sql)
        result[name] = rows
        print(f"{name:40} p50 {nearest_rank(ms, 50):7.1f}  p95 {nearest_rank(ms, 95):7.1f}  rows {len(rows):6,}")

    print("load     1-min load average after: %.2f" % os.getloadavg()[0])
    print()
    print("same answer?")
    b2 = [result[n][0] for n in names_with("BR2")]
    print(f"  BR2 (view, cart, purchase sessions; view, cart, purchase events): {b2[0]}")
    print(f"      gold = star = silver: {b2[0] == b2[1] == b2[2]}")
    gold4 = {r[0]: r[1:] for r in result["BR4 gold rfm_segments, r_score = 5"]}
    live4 = {r[0]: r[1:] for r in result["BR4 silver, RFM scored at read time"]}
    differ = sum(1 for u in gold4 if u in live4 and tuple(gold4[u]) != tuple(live4[u]))
    print(f"  BR4 users with r_score 5: gold {len(gold4):,}, read time {len(live4):,}, same set: {set(gold4) == set(live4)}")
    print(f"      of them, raw recency/frequency/monetary differ (section 6.1.4): {differ:,}")
    g7 = [(r[0], r[1], round(r[2], 4)) for r in result["BR7 gold product_affinity, 1005115"]]
    s7 = [(r[0], r[1], round(r[2], 4)) for r in result["BR7 silver, pairs at read time"]]
    print(f"  BR7 ten partners of 1005115, same products, counts and lift in the same order: {g7 == s7}")

    print()
    print("BR7 rows for 1005115 as the screen orders them (lift DESC, co_count DESC): product_b, co_count, lift")
    for r in g7:
        print(f"  {r[0]}  {r[1]:3}  {r[2]:.2f}")
    top_co = con.execute(f"""SELECT product_b, co_count, lift FROM {G7} WHERE product_a = 1005115
        ORDER BY co_count DESC, lift DESC LIMIT 1""").fetchone()
    print(f"most sessions together with 1005115: {top_co[0]}, {top_co[1]} sessions, lift {top_co[2]:.2f}")


def names_with(prefix):
    return [n for n, _ in QUERIES if n.startswith(prefix)]


if __name__ == "__main__":
    main()
