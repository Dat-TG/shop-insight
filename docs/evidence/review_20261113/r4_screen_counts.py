"""Counts behind the report's section 5.2 screen paragraphs (BR2, BR6, BR7, BR8).

Measures, with DuckDB on the Parquet in data/ (read-only):
  BR2  fact_session_funnel: sessions in the screen's default range (session_start_date
       1-30 Nov) by funnel_stage, the sessions that reached purchase with no cart event,
       the sessions with a real cart event, and the 1 Dec sessions the range leaves out;
       funnel_daily's 'all' rows for the same range, i.e. what the screen shows.
  BR6  fact_inventory_daily on its last day (2019-11-30): pairs by the screen's bands
       (critical < 3 days, low stock 3 to < 7 days, no sales = NULL days_to_stockout),
       critical pairs per warehouse, and critical pairs already at zero stock.
  BR7  product_affinity: ordered pairs, and those bought together exactly 3 times.
  BR8  silver purchases per user per 5-minute tumbling window (the streaming job's
       window, processing/streaming_gold.py start_br8): number of windows and the max.

Used by report edits R4-16 (BR2), R4-22 (BR6), R4-25 (BR7) and R4-27 (BR8) in section 5.2.

Run from the repo root:
  .venv/bin/python -I docs/evidence/review_20261113/r4_screen_counts.py
"""
import duckdb

FSF = "read_parquet('data/warehouse/fact_session_funnel/*/*.parquet', hive_partitioning = true)"
FUNNEL = "read_parquet('data/gold/funnel_daily/*/*.parquet', hive_partitioning = true)"
FID = "read_parquet('data/warehouse/fact_inventory_daily/*/*.parquet', hive_partitioning = true)"
AFFINITY = "read_parquet('data/gold/product_affinity/*.parquet')"
SILVER = "read_parquet('data/silver/*/*/*.parquet', hive_partitioning = true)"


def show(con, title, sql):
    cursor = con.execute(sql)
    names = [column[0] for column in cursor.description]
    print(f"-- {title}")
    print(sql.strip())
    for row in cursor.fetchall():
        print("   " + " | ".join(f"{name} = {value:,}" if isinstance(value, int) else f"{name} = {value}"
                                 for name, value in zip(names, row)))
    print()


def main():
    print(f"DuckDB {duckdb.__version__}\n")
    with duckdb.connect() as con:
        show(con, "BR2 fact_session_funnel, whole table vs the screen's range 1-30 Nov", f"""
SELECT count(*) AS sessions_all,
       count(*) FILTER (WHERE funnel_stage = 2) AS stage2_all,
       count(*) FILTER (WHERE funnel_stage = 3) AS stage3_all,
       count(*) FILTER (WHERE session_start_date <= DATE '2019-11-30') AS sessions_1_30,
       count(*) FILTER (WHERE session_start_date <= DATE '2019-11-30' AND funnel_stage >= 2) AS reached_cart_1_30,
       count(*) FILTER (WHERE session_start_date <= DATE '2019-11-30' AND funnel_stage = 2) AS stopped_at_cart_1_30,
       count(*) FILTER (WHERE session_start_date <= DATE '2019-11-30' AND funnel_stage = 3) AS purchased_1_30,
       count(*) FILTER (WHERE session_start_date <= DATE '2019-11-30' AND funnel_stage = 3 AND cart_count = 0) AS purchased_no_cart_event,
       count(*) FILTER (WHERE session_start_date <= DATE '2019-11-30' AND cart_count > 0) AS with_cart_event,
       count(*) FILTER (WHERE session_start_date <= DATE '2019-11-30' AND funnel_stage = 3 AND cart_count > 0) AS purchased_with_cart_event,
       count(*) FILTER (WHERE session_start_date <= DATE '2019-11-30' AND first_view_at IS NULL) AS no_view_event,
       count(*) FILTER (WHERE session_start_date = DATE '2019-12-01') AS sessions_dec1,
       count(*) FILTER (WHERE session_start_date = DATE '2019-12-01' AND funnel_stage = 3) AS purchased_dec1
FROM {FSF}""")
        show(con, "BR2 funnel_daily 'all' rows summed over 1-30 Nov (the screen's funnel card)", f"""
SELECT sum(views) AS views, sum(carts) AS carts, sum(purchases) AS purchases,
       round(100 * sum(carts) / sum(views), 2) AS view_to_cart_pct,
       round(100 * sum(purchases) / sum(carts), 2) AS cart_to_purchase_pct
FROM {FUNNEL}
WHERE category_l1 = 'all' AND event_date BETWEEN DATE '2019-11-01' AND DATE '2019-11-30'""")
        show(con, "BR6 fact_inventory_daily on 2019-11-30, by the screen's bands", f"""
SELECT count(*) AS pairs,
       count(*) FILTER (WHERE days_to_stockout < 3) AS critical,
       count(*) FILTER (WHERE days_to_stockout < 3 AND stock_on_hand = 0) AS critical_zero_stock,
       count(*) FILTER (WHERE days_to_stockout >= 3 AND days_to_stockout < 7) AS low_stock,
       count(*) FILTER (WHERE days_to_stockout IS NULL) AS no_sales_7d,
       round(100 * count(*) FILTER (WHERE days_to_stockout IS NULL) / count(*), 1) AS no_sales_pct
FROM {FID}
WHERE snapshot_date = DATE '2019-11-30'""")
        show(con, "BR6 critical pairs (< 3 days) per warehouse on 2019-11-30", f"""
SELECT warehouse_id, count(*) AS critical
FROM {FID}
WHERE snapshot_date = DATE '2019-11-30' AND days_to_stockout < 3
GROUP BY 1 ORDER BY 1""")
        show(con, "BR7 product_affinity ordered pairs", f"""
SELECT count(*) AS ordered_pairs,
       count(*) FILTER (WHERE co_count = 3) AS co_count_3,
       round(100 * count(*) FILTER (WHERE co_count = 3) / count(*), 1) AS co_count_3_pct
FROM {AFFINITY}""")
        show(con, "BR8 purchases per user per 5-minute window over the whole month (silver)", f"""
SELECT count(*) AS windows_with_purchase, max(n) AS max_purchases_in_window,
       count(*) FILTER (WHERE n >= 4) AS windows_4_or_more
FROM (SELECT user_id, time_bucket(INTERVAL 5 MINUTE, event_time) AS w, count(*) AS n
      FROM {SILVER}
      WHERE event_type = 'purchase'
      GROUP BY ALL)""")


if __name__ == "__main__":
    main()
