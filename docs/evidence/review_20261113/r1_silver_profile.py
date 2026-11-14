"""Profile the silver layer (and fact_session_funnel) for report sections 2.8 and 3.1.

Measures, all with DuckDB on data/ Parquet, read-only. Silver event_time is already
Vietnam time (UTC+7), as written by processing/batch_silver.py.
  1. events, purchases and purchase/view per day around the purchase gap   -> R1-30, R1-31 (3.1.4)
  2. events per hour of day, and sessions whose events fall on two dates
     when the day boundary is Vietnam time, UTC+3 or UTC                   -> R1-27 (3.1.3)
  3. purchases dated 1/12 in silver (outside the 1-30/11 inventory series) -> R1-27 (3.1.3)
  4. exact duplicate rows (all columns equal) and their effect on the
     cart value of sessions that carted and did not buy                    -> R1-28 (3.1.3)
  5. purchases per user per fixed 5-minute window (BR8's count)            -> R1-22 (2.8)
  6. abandoned sessions per session start date (fact_session_funnel)      -> R1-31 (3.1.4)

Run from the repo root:  .venv/bin/python docs/evidence/review_20261113/r1_silver_profile.py
"""
import duckdb

SILVER = "read_parquet('data/silver/*/*/*.parquet', hive_partitioning = true)"
FSF = "read_parquet('data/warehouse/fact_session_funnel/*/*.parquet', hive_partitioning = true)"
EVENT_COLUMNS = "event_time, event_type, product_id, price, user_id, user_session"


def gap_days(con):
    print("1. silver per day around the purchase gap (Vietnam time)")
    rows = con.sql(f"""
        SELECT event_date, count(*) AS events,
               count(*) FILTER (WHERE event_type = 'purchase') AS purchases,
               count(*) FILTER (WHERE event_type = 'view') AS views
        FROM {SILVER} WHERE event_date BETWEEN DATE '2019-11-14' AND DATE '2019-11-18'
        GROUP BY 1 ORDER BY 1""").fetchall()
    for day, events, purchases, views in rows:
        print(f"   {day}  events {events:>8,}  purchases {purchases:>6,}  purchase/view {100 * purchases / views:.2f}%")
    print()


def day_boundary(con):
    print("2. events per hour of day (silver, all month), hour in Vietnam time and UTC")
    hours = con.sql(f"""SELECT hour(event_time) AS h, count(*) FROM {SILVER} GROUP BY 1 ORDER BY 1""").fetchall()
    for h, n in hours:
        print(f"   {h:02d}:00 VN = {(h - 7) % 24:02d}:00 UTC  {n:>8,}")
    by_n = sorted(hours, key=lambda r: r[1])
    print(f"   quietest hour: {by_n[0][0]:02d}:00 VN ({by_n[0][1]:,} events); "
          f"four busiest: {', '.join(f'{h:02d}:00' for h, _ in sorted(by_n[-4:]))} VN")
    total = con.sql(f"SELECT count(DISTINCT user_session) FROM {SILVER}").fetchone()[0]
    print(f"   sessions whose events fall on two dates, of {total:,} sessions:")
    for name, shift in (("Vietnam time (UTC+7)", 0), ("UTC+3", 4), ("UTC", 7)):
        n = con.sql(f"""
            SELECT count(*) FROM (
                SELECT user_session FROM {SILVER}
                GROUP BY 1
                HAVING min(cast(event_time - INTERVAL {shift} HOUR AS date))
                    <> max(cast(event_time - INTERVAL {shift} HOUR AS date)))""").fetchone()[0]
        print(f"     {name:<22} {n:>6,}  ({100 * n / total:.2f}%)")
    print()


def december_purchases(con):
    n = con.sql(f"""SELECT count(*) FROM {SILVER}
        WHERE event_date = DATE '2019-12-01' AND event_type = 'purchase'""").fetchone()[0]
    print(f"3. silver purchases dated 2019-12-01: {n:,}")
    print()


def duplicates(con):
    print(f"4. exact duplicate rows in silver ({EVENT_COLUMNS} all equal)")
    rows = con.sql(f"""
        SELECT event_type, sum(n - 1) AS extra, max(n) AS largest
        FROM (SELECT {EVENT_COLUMNS}, count(*) AS n FROM {SILVER} GROUP BY ALL HAVING count(*) > 1)
        GROUP BY 1 ORDER BY 1""").fetchall()
    totals = dict(con.sql(f"SELECT event_type, count(*) FROM {SILVER} GROUP BY 1").fetchall())
    for event_type, extra, largest in rows:
        print(f"   {event_type:<8} extra rows {extra:>6,} of {totals[event_type]:>9,} "
              f"({100 * extra / totals[event_type]:.2f}%), largest group {largest}")
    print(f"   total extra rows {sum(r[1] for r in rows):,}")
    sessions, with_dup, value, deduped = con.sql(f"""
        WITH carted AS (
            SELECT user_session FROM {SILVER} GROUP BY 1
            HAVING bool_or(event_type = 'cart') AND NOT bool_or(event_type = 'purchase')),
        carts AS (
            SELECT s.user_session, s.event_time, s.product_id, s.price, s.user_id
            FROM {SILVER} s JOIN carted USING (user_session) WHERE s.event_type = 'cart'),
        per_session AS (
            SELECT user_session, sum(price) AS value,
                   count(*) - count(DISTINCT (event_time, product_id, price, user_id)) AS dup_rows
            FROM carts GROUP BY 1),
        distinct_value AS (
            SELECT sum(price) AS v FROM (SELECT DISTINCT user_session, event_time, product_id, price, user_id FROM carts))
        SELECT count(*), count(*) FILTER (WHERE dup_rows > 0), sum(value), (SELECT v FROM distinct_value)
        FROM per_session""").fetchone()
    print(f"   sessions that carted and never bought: {sessions:,}; with a duplicated cart row: {with_dup:,}")
    print(f"   their cart value: with duplicates {value:,.2f}, without {deduped:,.2f}, "
          f"excess {value - deduped:,.2f} ({100 * (value - deduped) / deduped:.2f}% of the deduplicated value)")
    print()


def purchases_per_window(con):
    print("5. purchases per (user, fixed 5-minute window), silver, all month")
    rows = con.sql(f"""
        SELECT n, count(*) FROM (
            SELECT user_id, time_bucket(INTERVAL 5 MINUTE, event_time) AS w, count(*) AS n
            FROM {SILVER} WHERE event_type = 'purchase' GROUP BY 1, 2)
        GROUP BY 1 ORDER BY 1""").fetchall()
    total = sum(c for _, c in rows)
    for n, c in rows:
        print(f"   {n} purchase(s): {c:>6,} windows")
    print(f"   windows with a purchase {total:,}; max purchases in one window {rows[-1][0]}; "
          f"windows with >= 10: {sum(c for n, c in rows if n >= 10)}")
    print()


def abandoned_per_day(con):
    print("6. abandoned sessions (fact_session_funnel.is_abandoned) per session_start_date")
    rows = con.sql(f"""SELECT session_start_date, count(*) FILTER (WHERE is_abandoned) AS n
        FROM {FSF} GROUP BY 1 ORDER BY 1""").fetchall()
    top = max(rows, key=lambda r: r[1])
    median = con.sql(f"""SELECT median(n) FROM (SELECT session_start_date, count(*) FILTER (WHERE is_abandoned) AS n
        FROM {FSF} GROUP BY 1)""").fetchone()[0]
    print(f"   days {len(rows)}; most: {top[0]} with {top[1]:,}; median per day {median:,}")
    for day, n in rows:
        if str(day) in ("2019-11-14", "2019-11-15", "2019-11-16", "2019-11-17"):
            print(f"   {day}  {n:>6,}")


def main():
    con = duckdb.connect()
    print(f"DuckDB {duckdb.__version__}; silver = data/silver, fact_session_funnel = data/warehouse\n")
    gap_days(con)
    day_boundary(con)
    december_purchases(con)
    duplicates(con)
    purchases_per_window(con)
    abandoned_per_day(con)


if __name__ == "__main__":
    main()
