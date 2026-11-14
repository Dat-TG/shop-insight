"""BR8: purchases per user per 5-minute window under three definitions of an order.

Read-only. Reads data/silver with DuckDB. Used by the report review of 13 Nov 2026,
region R6, edit R6-7.2-br8 (7.2):
  - the whole month: windows with >= 4 orders when an order is (a) one purchase event,
    as processing/streaming_gold.py counts it today, (b) one distinct
    (user_session, event_time) pair, (c) one distinct product_id;
  - the percentiles of (a) that place the proposed thresholds;
  - the 17 Nov 15:00-21:30 replay: windows by number of purchases, i.e. how many alerts
    the proposed thresholds (medium = 3, high >= 4, nothing for 1-2) would raise.
Windows are 5-minute tumbling windows per user_id, as start_br8 groups them.
Run: .venv/bin/python docs/evidence/review_20261113/r6_br8_orders.py
"""
import duckdb

SILVER = "read_parquet('data/silver/*/*/*.parquet', hive_partitioning = true)"


def windows(where=""):
    return f"""
        SELECT user_id, time_bucket(INTERVAL 5 MINUTE, event_time) AS window_start,
               count(*) AS purchases,
               count(DISTINCT (user_session, event_time)) AS checkouts,
               count(DISTINCT product_id) AS products
        FROM {SILVER} WHERE event_type = 'purchase' {where} GROUP BY 1, 2"""


def main():
    con = duckdb.connect()
    con.execute(f"CREATE TEMP TABLE w AS {windows()}")
    total = con.sql("SELECT count(*) FROM w").fetchone()[0]
    print(f"whole month: {total:,} (user, 5-minute window) pairs with a purchase")
    print("  by purchases:", con.sql("SELECT purchases, count(*) FROM w GROUP BY 1 ORDER BY 1").fetchall())
    q = con.sql("""SELECT quantile_disc(purchases, [0.5, 0.9, 0.95, 0.99, 0.999]) FROM w""").fetchone()[0]
    print("  percentiles 50 / 90 / 95 / 99 / 99.9 of purchases:", q)
    a, b, c = con.sql("""SELECT count(*) FILTER (WHERE purchases >= 4), count(*) FILTER (WHERE checkouts >= 4),
                                count(*) FILTER (WHERE products >= 4) FROM w""").fetchone()
    print(f"  windows with >= 4 orders: one purchase event = one order {a}; "
          f"one (user_session, event_time) = one order {b}; one distinct product = one order {c}")

    replay = ("AND event_time >= TIMESTAMP '2019-11-17 15:00:00' "
              "AND event_time < TIMESTAMP '2019-11-17 21:30:00'")
    con.execute(f"CREATE TEMP TABLE r AS {windows(replay)}")
    by_n = con.sql("SELECT purchases, count(*) FROM r GROUP BY 1 ORDER BY 1").fetchall()
    print("replay 17 Nov 15:00-21:30, windows by purchases:", by_n)
    now = sum(n for _, n in by_n)
    medium = sum(n for k, n in by_n if k == 3)
    high = sum(n for k, n in by_n if k >= 4)
    print(f"  alerts today (every window is low, medium or high): {now:,}; "
          f"proposed thresholds: medium {medium}, high {high}")


if __name__ == "__main__":
    main()
