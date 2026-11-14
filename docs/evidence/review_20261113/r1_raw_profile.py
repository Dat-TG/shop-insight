"""Profile the raw CSV (data/raw/2019-Nov.csv) and the bronze sample for report sections 1 and 3.

Measures, all with DuckDB, read-only:
  1. purchases per Vietnam-time day (UTC+7) and their ranking       -> edits R1-02 (1.1), R1-30 (3.1.4), manual task M1 (Hình 1)
  2. purchase-free gaps longer than 6 hours, in UTC                 -> edit R1-30 (3.1.4), manual task M1
  3. events per type and the three conversion ratios, raw vs bronze -> edit R1-24 (3.1.2)
  4. source rate: month average, the demo replay window
     (17/11 08:00-14:30 UTC) and the busiest minute of the month    -> edit R1-37 (3.5)
  5. exact duplicate rows among cart and purchase events of the raw
     file (all nine columns equal; view rows are not grouped, to keep
     the hash table in memory)                                      -> edit R1-28 (3.1.3)

Run from the repo root:  .venv/bin/python docs/evidence/review_20261113/r1_raw_profile.py
"""
import duckdb

CSV = "data/raw/2019-Nov.csv"
COLUMNS = ("{'event_time': 'VARCHAR', 'event_type': 'VARCHAR', 'product_id': 'BIGINT', "
           "'category_id': 'BIGINT', 'category_code': 'VARCHAR', 'brand': 'VARCHAR', "
           "'price': 'DECIMAL(10,2)', 'user_id': 'BIGINT', 'user_session': 'VARCHAR'}")
RAW = f"read_csv('{CSV}', header = true, columns = {COLUMNS})"
BRONZE = "read_parquet('data/bronze/*/*.parquet', hive_partitioning = true)"
TS = "strptime(event_time, '%Y-%m-%d %H:%M:%S UTC')"


def purchases_per_vietnam_day(con):
    rows = con.sql(f"""
        SELECT cast({TS} + INTERVAL 7 HOUR AS date) AS vn_day, count(*) AS purchases
        FROM {RAW} WHERE event_type = 'purchase' GROUP BY 1 ORDER BY 1""").fetchall()
    print("1. purchases per Vietnam-time day (whole raw file)")
    for day, n in rows:
        print(f"   {day}  {n:>8,}")
    ranked = sorted(rows, key=lambda r: -r[1])
    print("   ranking:", ", ".join(f"#{i + 1} {d} {n:,}" for i, (d, n) in enumerate(ranked[:5])))
    top, bf = dict(rows)[ranked[0][0]], [n for d, n in rows if str(d) == "2019-11-29"][0]
    print(f"   top day / Black Friday (29/11) = {top:,} / {bf:,} = {top / bf:.2f}")
    print()


def purchase_gaps(con):
    rows = con.sql(f"""
        WITH t AS (SELECT {TS} AS ts FROM {RAW} WHERE event_type = 'purchase'),
             g AS (SELECT lag(ts) OVER (ORDER BY ts) AS prev, ts FROM t)
        SELECT prev, ts, round(epoch(ts - prev) / 3600, 2) AS hours
        FROM g WHERE ts - prev > INTERVAL 6 HOUR ORDER BY hours DESC""").fetchall()
    print("2. purchase-free gaps longer than 6 hours (UTC; add 7 hours for Vietnam time)")
    for prev, ts, hours in rows:
        print(f"   {prev} -> {ts}   {hours} h")
    print()


def conversion_ratios(con):
    print("3. events per type and conversion ratios")
    for name, src in (("raw   ", RAW), ("bronze", BRONZE)):
        v, c, p = con.sql(f"""
            SELECT count(*) FILTER (WHERE event_type = 'view'),
                   count(*) FILTER (WHERE event_type = 'cart'),
                   count(*) FILTER (WHERE event_type = 'purchase') FROM {src}""").fetchone()
        print(f"   {name} view {v:>11,}  cart {c:>10,}  purchase {p:>8,} | "
              f"cart/view {100 * c / v:.3f}%  purchase/view {100 * p / v:.3f}%  purchase/cart {100 * p / c:.2f}%")
    print()


def source_rate(con):
    total = con.sql(f"SELECT count(*) FROM {RAW}").fetchone()[0]
    window = con.sql(f"""SELECT count(*) FROM {RAW}
        WHERE event_time >= '2019-11-17 08:00:00' AND event_time < '2019-11-17 14:30:00'""").fetchone()[0]
    minute, n = con.sql(f"""SELECT substr(event_time, 1, 16), count(*) FROM {RAW}
        GROUP BY 1 ORDER BY 2 DESC LIMIT 1""").fetchone()
    replay = 480.7  # docs/evidence/streaming_perf.txt, run 1, offered rate in rows/s
    print("4. source rate, whole marketplace (raw file)")
    print(f"   month: {total:,} events / (30 x 86,400 s) = {total / 2_592_000:.1f} events/s")
    print(f"   demo window 17/11 08:00-14:30 UTC: {window:,} events / 23,400 s = {window / 23_400:.1f} events/s")
    print(f"   busiest minute {minute} UTC: {n:,} events = {n / 60:.1f} events/s")
    print(f"   replay 480.7 rows/s (streaming_perf.txt run 1) / window rate = {replay / (window / 23_400):.2f}; "
          f"/ busiest minute = {replay / (n / 60):.2f}")
    print()


def raw_duplicates(con):
    rows = con.sql(f"""
        SELECT event_type, sum(n - 1) AS extra_rows, max(n) AS largest_group
        FROM (SELECT event_time, event_type, product_id, category_id, category_code, brand,
                     price, user_id, user_session, count(*) AS n
              FROM {RAW} WHERE event_type IN ('cart', 'purchase')
              GROUP BY ALL HAVING count(*) > 1)
        GROUP BY 1 ORDER BY 1""").fetchall()
    totals = dict(con.sql(f"""SELECT event_type, count(*) FROM {RAW}
        WHERE event_type IN ('cart', 'purchase') GROUP BY 1""").fetchall())
    print("5. exact duplicate rows in the raw file, cart and purchase only (all nine columns equal)")
    for event_type, extra, largest in rows:
        print(f"   {event_type:<8} extra rows {extra:>7,} of {totals[event_type]:>9,} "
              f"({100 * extra / totals[event_type]:.2f}%), largest group {largest}")


def main():
    con = duckdb.connect()
    print(f"DuckDB {duckdb.__version__}; raw = {CSV}; bronze = data/bronze (7% user sample)\n")
    purchases_per_vietnam_day(con)
    purchase_gaps(con)
    conversion_ratios(con)
    source_rate(con)
    raw_duplicates(con)


if __name__ == "__main__":
    main()
