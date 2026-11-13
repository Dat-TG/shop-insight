"""How unusual are BR8's alert levels? Purchases per user per 5-minute window, from silver.

Measures:
  1. over the whole month of the 7% sample, the (user, 5-minute window) pairs with at least one
     purchase, by purchase count, with the cumulative share (so the 90th / 99th / 99.9th percentile);
  2. over the demo replay (17 Nov 15:00-21:30 Vietnam time, what Cassandra's order_velocity_alerts
     holds), the alerts per level with BR8's thresholds (low 1, medium 2-3, high >= 4; streaming_gold.py),
     how many sit in a single session and how many are all different products;
  3. every high alert of the replay, event by event;
  4. whether silver has a quantity or order id column.
Windows are 5-minute tumbling windows aligned like Spark's (time_bucket on event_time, which silver
already holds in Vietnam time).

Used by report edits R5-E7a (section 6.3, the BR8 paragraph) and R5-E7b (6.1.2). Read-only.

Run from the repo root:  .venv/bin/python -I docs/evidence/review_20261113/r5_br8_thresholds.py
"""
import duckdb

S = "read_parquet('data/silver/**/*.parquet', hive_partitioning=true)"
REPLAY = "event_time >= TIMESTAMP '2019-11-17 15:00:00' AND event_time < TIMESTAMP '2019-11-17 21:30:00'"


def month_distribution(con):
    rows = con.execute(f"""WITH w AS (SELECT user_id, time_bucket(INTERVAL 5 MINUTE, event_time) ws, count(*) n
        FROM {S} WHERE event_type = 'purchase' GROUP BY 1, 2)
        SELECT n, count(*) FROM w GROUP BY 1 ORDER BY 1""").fetchall()
    total = sum(c for _, c in rows)
    print(f"1. month: (user, 5-minute window) pairs with a purchase: {total:,}")
    running = 0
    for n, c in rows:
        running += c
        print(f"   {n} purchase(s)  {c:7,}  {100 * c / total:6.2f}%   cumulative {100 * running / total:6.2f}%")
    print(f"   2 or 3 purchases (medium): {sum(c for n, c in rows if 2 <= n <= 3):,} "
          f"= {100 * sum(c for n, c in rows if 2 <= n <= 3) / total:.2f}%")
    print(f"   4 or more (high): {sum(c for n, c in rows if n >= 4):,}")


def replay_levels(con):
    rows = con.execute(f"""WITH e AS (SELECT * FROM {S} WHERE event_type = 'purchase' AND {REPLAY}),
        w AS (SELECT user_id, time_bucket(INTERVAL 5 MINUTE, event_time) ws, count(*) n,
              count(DISTINCT user_session) s, count(DISTINCT product_id) p FROM e GROUP BY 1, 2)
        SELECT CASE WHEN n >= 4 THEN 'high' WHEN n >= 2 THEN 'medium' ELSE 'low' END lvl, count(*),
          count(*) FILTER (WHERE s = 1), count(*) FILTER (WHERE p = n), count(*) FILTER (WHERE p = 1)
        FROM w GROUP BY 1 ORDER BY 2 DESC""").fetchall()
    print("2. replay 17 Nov 15:00-21:30: level, alerts, in one session, all different products, one product")
    for r in rows:
        print(f"   {r[0]:6} {r[1]:5,} {r[2]:5,} {r[3]:5,} {r[4]:5,}")
    total = sum(r[1] for r in rows)
    low = next(r[1] for r in rows if r[0] == "low")
    print(f"   all {total:,}; low share {100 * low / total:.1f}%")


def high_alerts(con):
    print("3. high alerts of the replay, event by event: window, user, session, product, price, time, category")
    rows = con.execute(f"""WITH e AS (SELECT *, time_bucket(INTERVAL 5 MINUTE, event_time) ws
          FROM {S} WHERE event_type = 'purchase' AND {REPLAY}),
        hi AS (SELECT user_id, ws FROM e GROUP BY 1, 2 HAVING count(*) >= 4)
        SELECT e.ws, e.user_id, e.user_session, e.product_id, e.price, e.event_time,
               coalesce(e.category_code, '-'), coalesce(e.brand, '-')
        FROM e JOIN hi USING (user_id, ws) ORDER BY e.ws, e.user_id, e.event_time""").fetchall()
    for r in rows:
        print(f"   {r[0]:%H:%M}  {r[1]}  {r[2][:8]}  {r[3]}  {r[4]:>9}  {r[5]:%H:%M:%S}  {r[6]} {r[7]}")


def silver_columns(con):
    cols = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM {S}").fetchall()]
    print(f"4. silver columns: {cols}")
    print(f"   a quantity or order id column: {any('quant' in c or 'order' in c for c in cols)}")


def main():
    con = duckdb.connect()
    month_distribution(con)
    replay_levels(con)
    high_alerts(con)
    silver_columns(con)


if __name__ == "__main__":
    main()
