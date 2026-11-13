"""Which numbers of the 7% sample carry over to the full file: same SQL on both.

Read-only. Reads data/bronze (the 7% user sample, before cleaning, UTC),
data/raw/2019-Nov.csv (all 67.5M events, UTC), data/silver and data/gold/product_affinity
with DuckDB. Neither side is cleaned, so the comparison is like for like.
Used by the report review of 13 Nov 2026, region R6:
  - edit R6-7.1-scale (7.1): the BR7 rule of processing/gold_br7.py
    (MIN_PRODUCT_SESSIONS = 20, MIN_CO_COUNT = 3, lift > 1) keeps far more pairs on the
    full file than on the sample;
  - edit R6-7.1-sampling (7.1): users kept by the sample;
  - manual task R6-M-table (new table in 7.1): session funnel rates, the BR8 purchases
    per (user, 5-minute window) distribution, the BR7 rule (duplicated cart events come
    from r6_duplicates.py).
Run: .venv/bin/python docs/evidence/review_20261113/r6_sample_vs_full.py
"""
import tempfile
import time

import duckdb

BRONZE = """(SELECT event_time, event_type, product_id, user_id, user_session
             FROM read_parquet('data/bronze/*/*.parquet', hive_partitioning = true))"""
RAW = """(SELECT strptime(event_time, '%Y-%m-%d %H:%M:%S UTC') AS event_time, event_type,
                 CAST(product_id AS BIGINT) AS product_id, CAST(user_id AS BIGINT) AS user_id, user_session
          FROM read_csv('data/raw/2019-Nov.csv', header = true, all_varchar = true))"""
SILVER = """(SELECT event_time, event_type, product_id, user_id, user_session
             FROM read_parquet('data/silver/*/*/*.parquet', hive_partitioning = true))"""
GOLD_BR7 = "read_parquet('data/gold/product_affinity/*.parquet')"


def measure(con, name, src):
    started = time.perf_counter()
    events, users = con.sql(f"SELECT count(*), count(DISTINCT user_id) FROM {src}").fetchone()
    print(f"== {name}: {events:,} events, {users:,} users")

    sessions, carted, bought = con.sql(f"""
        WITH s AS (SELECT user_session,
                          bool_or(event_type IN ('cart', 'purchase')) AS carted,
                          bool_or(event_type = 'purchase') AS bought
                   FROM {src} WHERE user_session IS NOT NULL GROUP BY 1)
        SELECT count(*), count(*) FILTER (WHERE carted), count(*) FILTER (WHERE bought) FROM s""").fetchone()
    print(f"  sessions {sessions:,}; with a cart or purchase {carted / sessions:.2%}; "
          f"with a purchase {bought / sessions:.2%}")

    pairs, two_plus, four_plus, top = con.sql(f"""
        WITH w AS (SELECT user_id, time_bucket(INTERVAL 5 MINUTE, event_time) AS ws, count(*) AS n
                   FROM {src} WHERE event_type = 'purchase' GROUP BY 1, 2)
        SELECT count(*), count(*) FILTER (WHERE n >= 2), count(*) FILTER (WHERE n >= 4), max(n) FROM w""").fetchone()
    print(f"  BR8 (user, 5-minute window) pairs with a purchase {pairs:,}; >= 2 purchases "
          f"{two_plus:,} ({two_plus / pairs:.2%}); >= 4 purchases {four_plus:,} ({four_plus / pairs:.3%}); "
          f"largest {top}")

    con.execute(f"""CREATE OR REPLACE TEMP TABLE baskets AS
                    SELECT DISTINCT user_session, product_id FROM {src}
                    WHERE event_type = 'purchase' AND user_session IS NOT NULL""")
    n_sessions, n_popular, n_pairs = con.sql("""
        WITH n AS (SELECT count(DISTINCT user_session) AS n FROM baskets),
        pop AS (SELECT product_id, count(*) AS k FROM baskets GROUP BY 1 HAVING count(*) >= 20),
        kept AS (SELECT baskets.* FROM baskets JOIN pop USING (product_id)),
        pr AS (SELECT a.product_id AS pa, b.product_id AS pb, count(*) AS co
               FROM kept a JOIN kept b ON a.user_session = b.user_session AND a.product_id < b.product_id
               GROUP BY 1, 2 HAVING count(*) >= 3)
        SELECT (SELECT n FROM n), (SELECT count(*) FROM pop),
               count(*) FILTER (WHERE co * (SELECT n FROM n) / (x.k * y.k) > 1)
        FROM pr JOIN pop x ON x.product_id = pa JOIN pop y ON y.product_id = pb""").fetchone()
    print(f"  BR7 rule: purchase sessions {n_sessions:,}; products in >= 20 sessions {n_popular:,}; "
          f"product pairs with co_count >= 3 and lift > 1 {n_pairs:,}")
    print(f"  ({time.perf_counter() - started:.1f} s)")


def main():
    con = duckdb.connect()
    con.execute(f"SET temp_directory = '{tempfile.gettempdir()}/duckdb_r6'")
    measure(con, "bronze, 7% user sample", BRONZE)
    measure(con, "raw CSV, full file", RAW)
    measure(con, "silver (for the link to the gold table)", SILVER)
    rows = con.sql(f"SELECT count(*) FROM {GOLD_BR7}").fetchone()[0]
    print(f"gold product_affinity rows (each pair stored in both directions): {rows:,}")


if __name__ == "__main__":
    main()
