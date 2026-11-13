"""Counts on silver, the warehouse and the replay window that back the source rows of report appendix A.

Measures, read-only, with DuckDB on the Parquet that batch_silver.py and batch_warehouse.py
built on 3 Nov 2026 (nothing here writes):

  1. silver_duplicates     exact duplicate rows in silver, per event_type, the largest group,
                           and the same count on the 4-column key (user_session, product_id,
                           event_type, event_time)                    -> new Table A.8 (section 7.1)
  2. br8_distribution      purchases per (user, 5-minute bucket) on silver, and percentiles
                                                                       -> new Table A.8 (section 7.1)
  3. dim_product_mismatch  silver events vs the dim_product version valid that day: category_l1
                           and brand mismatches                        -> Table A.4 (section 4.1.6)
  4. rfm_lookahead         events of 1-7 Nov whose user already has an RFM cell on the 7 Nov
                           snapshot before the user's first purchase  -> Table A.4 (section 4.1.3)
  5. gmv_by_minute_rows    BR1's rows rebuilt from silver for the 17 Nov replay window
                           (15:00-21:30 Vietnam time): partitions and rows -> Table A.5 (C1d,
                           "quét qua 15 phân vùng")
  6. br6_last_day          fact_inventory_daily on its last day: (product, warehouse) pairs with
                           days_to_stockout < 3 and in [3, 7), per warehouse -> Table A.7 (EF4)
  7. fact_event_bytes      bytes of fact_event's Parquet files (MB vs MiB) -> Table A.6 (F14b)

Run from the repo root:
  .venv/bin/python -I docs/evidence/review_20261113/r7_silver_warehouse_counts.py
"""
import datetime
import glob
import os

import duckdb

SILVER = "read_parquet('data/silver/*/*/*.parquet', hive_partitioning = true)"
DIM_PRODUCT = "read_parquet('data/warehouse/dim_product/*.parquet')"
RFM = "read_parquet('data/warehouse/stg_rfm_snapshot/*/*.parquet', hive_partitioning = true)"
INVENTORY = "read_parquet('data/warehouse/fact_inventory_daily/*/*.parquet', hive_partitioning = true)"
# Silver's event_time is already Vietnam time (batch_silver.py shifts it by 7 hours).
REPLAY = "event_time >= TIMESTAMP '2019-11-17 15:00:00' AND event_time < TIMESTAMP '2019-11-17 21:30:00'"


def show(con, title, sql):
    print(f"-- {title}")
    print(sql.strip())
    for row in con.sql(sql).fetchall():
        print("  ", row)
    print()


def silver_duplicates(con):
    show(con, "1a. silver: exact duplicate rows (extra copies) per event_type, largest group", f"""
SELECT event_type, sum(c - 1) AS extra_rows, max(c) AS largest_group
FROM (SELECT *, count(*) AS c FROM {SILVER} GROUP BY ALL HAVING count(*) > 1)
GROUP BY 1 ORDER BY 1""")
    show(con, "1b. silver: rows per event_type", f"""
SELECT event_type, count(*) FROM {SILVER} GROUP BY 1 ORDER BY 1""")
    show(con, "1c. silver: rows minus distinct (user_session, product_id, event_type, event_time)", f"""
SELECT count(*) - (SELECT count(*) FROM (SELECT DISTINCT user_session, product_id, event_type, event_time
                                         FROM {SILVER})) AS extra_rows
FROM {SILVER}""")


def br8_distribution(con):
    show(con, "2a. BR8: (user, 5-minute bucket) pairs by number of purchases", f"""
WITH b AS (SELECT user_id, time_bucket(INTERVAL 5 MINUTE, event_time) AS w, count(*) AS n
           FROM {SILVER} WHERE event_type = 'purchase' GROUP BY ALL)
SELECT n, count(*) AS pairs, sum(count(*)) OVER () AS all_pairs FROM b GROUP BY 1 ORDER BY 1""")
    show(con, "2b. BR8: percentiles 50, 90, 95, 99, 99.9 of purchases per pair (nearest rank)", f"""
WITH b AS (SELECT user_id, time_bucket(INTERVAL 5 MINUTE, event_time) AS w, count(*) AS n
           FROM {SILVER} WHERE event_type = 'purchase' GROUP BY ALL)
SELECT quantile_disc(n, [0.5, 0.9, 0.95, 0.99, 0.999]) FROM b""")


def dim_product_mismatch(con):
    show(con, "3. silver events vs the dim_product version valid on event_date: "
              "events, category_l1 mismatches, brand mismatches, products with a brand mismatch", f"""
WITH s AS (SELECT product_id, event_date, brand, category_l1 FROM {SILVER}),
     p AS (SELECT product_id, valid_from, valid_to, brand, category_l1 FROM {DIM_PRODUCT})
SELECT count(*),
       count(*) FILTER (WHERE s.category_l1 IS DISTINCT FROM p.category_l1),
       count(*) FILTER (WHERE s.brand IS DISTINCT FROM p.brand),
       count(DISTINCT s.product_id) FILTER (WHERE s.brand IS DISTINCT FROM p.brand)
FROM s JOIN p ON s.product_id = p.product_id AND s.event_date >= p.valid_from AND s.event_date < p.valid_to""")


def rfm_lookahead(con):
    show(con, "4. events of 1-7 Nov: events, users, events whose user has an RFM cell on the 7 Nov "
              "snapshot, of those before the user's first purchase, and their users", f"""
WITH s AS (SELECT user_id, event_time FROM {SILVER} WHERE event_date <= DATE '2019-11-07'),
     r AS (SELECT user_id FROM {RFM} WHERE snapshot_date = DATE '2019-11-07' AND rfm_cell IS NOT NULL),
     f AS (SELECT user_id, min(event_time) AS first_buy FROM {SILVER} WHERE event_type = 'purchase' GROUP BY 1)
SELECT count(*), count(DISTINCT s.user_id), count(r.user_id),
       count(*) FILTER (WHERE r.user_id IS NOT NULL AND s.event_time < f.first_buy),
       count(DISTINCT s.user_id) FILTER (WHERE r.user_id IS NOT NULL AND s.event_time < f.first_buy)
FROM s LEFT JOIN r USING (user_id) LEFT JOIN f USING (user_id)""")


def gmv_by_minute_rows(con):
    # BR1 (start_br1 in processing/streaming_gold.py) writes one row per (1-minute window,
    # category_l1) with at least one event of any type, plus one 'all' row per window.
    show(con, "5. BR1 rebuilt from silver for the replay window: partitions (event_date, category_l1), "
              "rows, rows of the 'all' partition", f"""
WITH e AS (SELECT event_date, category_l1, date_trunc('minute', event_time) AS w FROM {SILVER} WHERE {REPLAY}),
     k AS (SELECT DISTINCT event_date, category_l1, w FROM e
           UNION ALL
           SELECT DISTINCT event_date, 'all', w FROM e)
SELECT count(DISTINCT (event_date, category_l1)) AS partitions, count(*) AS rows,
       count(*) FILTER (WHERE category_l1 = 'all') AS all_rows
FROM k""")


def br6_last_day(con):
    show(con, "6. fact_inventory_daily, last snapshot_date: pairs with days_to_stockout < 3 and in [3, 7), "
              "per warehouse and in total", f"""
SELECT warehouse_id, max(snapshot_date) AS day,
       count(*) FILTER (WHERE days_to_stockout < 3) AS under_3,
       count(*) FILTER (WHERE days_to_stockout >= 3 AND days_to_stockout < 7) AS from_3_to_7,
       count(*) AS pairs
FROM {INVENTORY}
WHERE snapshot_date = (SELECT max(snapshot_date) FROM {INVENTORY})
GROUP BY ROLLUP (warehouse_id) ORDER BY warehouse_id NULLS LAST""")


def fact_event_bytes():
    files = glob.glob("data/warehouse/fact_event/*/*.parquet")
    size = sum(os.path.getsize(f) for f in files)
    print("-- 7. fact_event Parquet files: count, bytes, MiB (bytes / 2^20), MB (bytes / 10^6)")
    print(f"   {len(files)} files, {size:,} bytes, {size / 2**20:.1f} MiB, {size / 1e6:.1f} MB")
    print()


def main():
    print(f"DuckDB {duckdb.__version__}")
    for marker in ["data/silver/_SUCCESS", "data/warehouse/fact_event/_SUCCESS"]:
        if os.path.exists(marker):
            print(f"{marker} written {datetime.datetime.fromtimestamp(os.path.getmtime(marker)):%Y-%m-%d %H:%M} (local time)")
    print()
    con = duckdb.connect()
    silver_duplicates(con)
    br8_distribution(con)
    dim_product_mismatch(con)
    rfm_lookahead(con)
    gmv_by_minute_rows(con)
    br6_last_day(con)
    fact_event_bytes()


if __name__ == "__main__":
    main()
