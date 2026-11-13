"""Which BR6 rows the inventory generator planted (report section 3.4).

fact_inventory_daily stores no "waiting for supplier" flag, so this script finds those
pairs by their trace: a (product, warehouse) pair whose stock_on_hand stays below its
reorder_point on every day of the month never received a batch
(ingestion/gen_inventory.py, run_stock). Measures, with DuckDB, read-only:
  - pairs, and pairs below the reorder point on all 30 days
  - share of pairs below the reorder point on 30/11
  - on 30/11, pairs under 3 days of stock (stock_on_hand < 3 * velocity_7d, as the
    generator's own check), how many are at zero stock, and how many of those are
    always-below pairs
Used by report edit R1-35 (section 3.4).

Run from the repo root:  .venv/bin/python docs/evidence/review_20261113/r1_inventory_waiting.py
"""
import duckdb

FID = "read_parquet('data/warehouse/fact_inventory_daily/*/*.parquet', hive_partitioning = true)"


def main():
    con = duckdb.connect()
    print(f"DuckDB {duckdb.__version__}; {FID}\n")
    pairs, always_below = con.sql(f"""
        SELECT count(*), count(*) FILTER (WHERE all_below) FROM (
            SELECT product_id, warehouse_id, bool_and(stock_on_hand < reorder_point) AS all_below,
                   count(*) AS days
            FROM {FID} GROUP BY 1, 2)""").fetchone()
    print(f"pairs {pairs:,}; below the reorder point on every day: {always_below:,} "
          f"({100 * always_below / pairs:.1f}%)")
    below_last = con.sql(f"""SELECT avg(CASE WHEN stock_on_hand < reorder_point THEN 1 ELSE 0 END)
        FROM {FID} WHERE snapshot_date = DATE '2019-11-30'""").fetchone()[0]
    print(f"below the reorder point on 30/11: {100 * below_last:.1f}% of pairs")
    at_risk, zero, zero_planted, zero_in_group = con.sql(f"""
        WITH planted AS (
            SELECT product_id, warehouse_id FROM {FID} GROUP BY 1, 2
            HAVING bool_and(stock_on_hand < reorder_point)),
        last AS (
            SELECT f.*, p.product_id IS NOT NULL AS is_planted FROM {FID} f
            LEFT JOIN planted p USING (product_id, warehouse_id)
            WHERE f.snapshot_date = DATE '2019-11-30')
        SELECT count(*) FILTER (WHERE stock_on_hand < 3 * velocity_7d),
               count(*) FILTER (WHERE stock_on_hand < 3 * velocity_7d AND stock_on_hand = 0),
               count(*) FILTER (WHERE stock_on_hand < 3 * velocity_7d AND stock_on_hand = 0 AND is_planted),
               count(*) FILTER (WHERE stock_on_hand = 0 AND is_planted)
        FROM last""").fetchone()
    print(f"30/11, under 3 days of stock: {at_risk:,}; of them at zero stock: {zero:,}; "
          f"of those, always-below pairs: {zero_planted:,}")
    print(f"30/11, always-below pairs at zero stock (any velocity): {zero_in_group:,}")


if __name__ == "__main__":
    main()
