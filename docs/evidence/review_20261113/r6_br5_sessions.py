"""BR5 abandoned carts: a batch simulation of session_window on silver.

Read-only. Reads data/silver with DuckDB. Used by the report review of 13 Nov 2026,
region R6:
  - edit R6-7.1-br5 (7.1): abandoned windows of a session that later buys in a new
    window of the same session (the upsert-only table keeps the stale row), and
    abandoned windows that share the key ((event_date), user_session) with an earlier
    one of the same day (the later write overwrites cart_value);
  - edit R6-7.1-dups (7.1): on the 17 Nov 15:00-21:30 replay, how many closed abandoned
    carts contain exact-duplicate cart events, and how much value the duplicates add.

How the simulation follows processing/streaming_gold.py (start_br5):
  - session_window("event_time", "30 minutes") per user_session: a new window starts
    when the gap to the previous event of the session is 30 minutes or more. Gaps are
    taken between DISTINCT event times, so events sharing a timestamp never split a
    window and the result does not depend on row order;
  - a window is abandoned when it has a cart event and no purchase event;
  - cart_value = sum(price) of the window's cart events; event_date = date of the
    window's last event (silver event_time is already Vietnam time);
  - replay only: a window is written once the watermark (max event_time - 10 minutes)
    passes its end (last event + 30 minutes).
This is a batch approximation, not a streaming run; the replay count is close to,
not equal to, the 2,600 carts the BR5 screen showed.
Run: .venv/bin/python docs/evidence/review_20261113/r6_br5_sessions.py
"""
import duckdb

SILVER = "read_parquet('data/silver/*/*/*.parquet', hive_partitioning = true)"
REPLAY = ("event_time >= TIMESTAMP '2019-11-17 15:00:00' "
          "AND event_time < TIMESTAMP '2019-11-17 21:30:00'")


def build_windows(con, where):
    """Create table ev: every event of `where` with its session window id `win`."""
    con.execute(f"CREATE OR REPLACE TEMP TABLE raw AS SELECT * FROM {SILVER} WHERE {where}")
    con.execute("""
        CREATE OR REPLACE TEMP TABLE times AS
        WITH t AS (SELECT DISTINCT user_session, event_time FROM raw),
        g AS (SELECT *, CASE WHEN lag(event_time) OVER w IS NULL
                              OR event_time - lag(event_time) OVER w >= INTERVAL 30 MINUTE
                             THEN 1 ELSE 0 END AS new_win
              FROM t WINDOW w AS (PARTITION BY user_session ORDER BY event_time))
        SELECT user_session, event_time,
               sum(new_win) OVER (PARTITION BY user_session ORDER BY event_time
                                  ROWS UNBOUNDED PRECEDING) AS win
        FROM g""")
    con.execute("CREATE OR REPLACE TEMP TABLE ev AS SELECT raw.*, win FROM raw JOIN times USING (user_session, event_time)")
    con.execute("""
        CREATE OR REPLACE TEMP TABLE win AS
        SELECT user_session, win,
               bool_or(event_type = 'cart') AS has_cart,
               bool_or(event_type = 'purchase') AS has_purchase,
               sum(CASE WHEN event_type = 'cart' THEN price ELSE 0 END) AS cart_value,
               max(event_time) AS last_event_at,
               CAST(max(event_time) AS DATE) AS event_date
        FROM ev GROUP BY 1, 2""")


def month(con):
    build_windows(con, "user_session IS NOT NULL")
    windows, abandoned, sessions = con.sql("""
        SELECT count(*), count(*) FILTER (WHERE has_cart AND NOT has_purchase),
               count(DISTINCT user_session) FILTER (WHERE has_cart AND NOT has_purchase)
        FROM win""").fetchone()
    print(f"whole month: {windows:,} session windows; {abandoned:,} abandoned windows "
          f"in {sessions:,} sessions")
    later_buy, later_buy_sessions = con.sql("""
        SELECT count(*), count(DISTINCT a.user_session) FROM win a
        WHERE a.has_cart AND NOT a.has_purchase
          AND EXISTS (SELECT 1 FROM win b WHERE b.user_session = a.user_session
                      AND b.win > a.win AND b.has_purchase)""").fetchone()
    print(f"  abandoned windows followed by a later window of the same session with a purchase: "
          f"{later_buy:,} ({later_buy / abandoned:.2%}) in {later_buy_sessions:,} sessions")
    keys, overwritten = con.sql("""
        SELECT count(*), sum(n - 1) FROM (
            SELECT event_date, user_session, count(*) AS n FROM win
            WHERE has_cart AND NOT has_purchase GROUP BY 1, 2 HAVING count(*) > 1)""").fetchone()
    print(f"  keys (event_date, user_session) holding more than one abandoned window: {keys:,}; "
          f"windows whose cart_value a later window of the same key overwrites: {overwritten:,}")


def replay(con):
    build_windows(con, f"user_session IS NOT NULL AND {REPLAY}")
    con.execute("""
        CREATE OR REPLACE TEMP TABLE closed AS
        SELECT * FROM win
        WHERE has_cart AND NOT has_purchase
          AND last_event_at + INTERVAL 30 MINUTE
              <= (SELECT max(event_time) FROM raw) - INTERVAL 10 MINUTE""")
    carts, value = con.sql("SELECT count(*), sum(cart_value) FROM closed").fetchone()
    with_dups, extra = con.sql("""
        WITH c AS (SELECT ev.* FROM ev JOIN closed USING (user_session, win) WHERE event_type = 'cart'),
        d AS (SELECT user_session, win, sum((n - 1) * price) AS extra FROM (
                  SELECT *, count(*) AS n FROM c GROUP BY ALL HAVING count(*) > 1)
              GROUP BY 1, 2)
        SELECT count(*), sum(extra) FROM d""").fetchone()
    print(f"replay 17 Nov 15:00-21:30: {carts:,} closed abandoned carts, total cart_value {value:,.2f}")
    print(f"  carts holding exact-duplicate cart events: {with_dups:,}; value the duplicates add "
          f"{extra:,.2f} ({extra / value:.2%} of the total cart_value)")


def main():
    con = duckdb.connect()
    month(con)
    replay(con)


if __name__ == "__main__":
    main()
