"""BR6 on the last day, and where the 32-bit floats of BR6 come from.

Measures, on data/warehouse/fact_inventory_daily (the table batch_gold.py builds stockout_risk
from, last day 2019-11-30):
  1. per warehouse, the product-warehouse pairs with days_to_stockout < 3 (the screen's critical,
     red) and 3 <= days_to_stockout < 7 (its low stock, amber; BR6Page.tsx CRITICAL_DAYS = 3,
     WARNING_DAYS = 7), against the 100 rows per warehouse the API reads (br6.py _LIMIT_PER_WAREHOUSE);
  2. the Parquet column types of velocity_7d and days_to_stockout, and of support and lift in
     data/gold/product_affinity;
  3. one row where 32-bit storage shows: warehouse 1, product 1005161.

Used by report edits R5-E4 (6.1.2), R5-E13c (Bảng 18, BR6 cell), R5-E11 (6.1.1) and R5-E11b (6.1.3).
Read-only.

Run from the repo root:  .venv/bin/python -I docs/evidence/review_20261113/r5_br6_inventory.py
"""
import duckdb

FID = "read_parquet('data/warehouse/fact_inventory_daily/**/*.parquet', hive_partitioning=true)"
PA = "read_parquet('data/gold/product_affinity/*.parquet')"


def per_warehouse(con):
    rows = con.execute(f"""SELECT warehouse_id, count(*) AS pairs,
          count(*) FILTER (WHERE days_to_stockout < 3) AS critical,
          count(*) FILTER (WHERE days_to_stockout >= 3 AND days_to_stockout < 7) AS low_stock,
          count(*) FILTER (WHERE days_to_stockout < 3 AND stock_on_hand = 0) AS critical_at_zero
        FROM {FID} WHERE snapshot_date = DATE '2019-11-30' GROUP BY 1 ORDER BY 1""").fetchall()
    print("1. 30 Nov per warehouse: pairs, < 3 days, 3 to < 7 days, < 3 days with stock 0")
    for r in rows:
        print(f"   warehouse {r[0]}  {r[1]:6,}  {r[2]:4}  {r[3]:4}  {r[4]:4}")
    print(f"   total        {sum(r[1] for r in rows):6,}  {sum(r[2] for r in rows):4}  "
          f"{sum(r[3] for r in rows):4}  {sum(r[4] for r in rows):4}")
    print(f"   every warehouse has more than 100 critical pairs: {all(r[2] > 100 for r in rows)}")


def column_types(con):
    print("2. Parquet column types")
    for table, cols in ((FID, ("velocity_7d", "days_to_stockout")), (PA, ("support", "lift"))):
        for name, typ, *_ in con.execute(f"DESCRIBE SELECT * FROM {table}").fetchall():
            if name in cols:
                print(f"   {name:18} {typ}")


def float_example(con):
    r = con.execute(f"""SELECT stock_on_hand, velocity_7d::DOUBLE, days_to_stockout::DOUBLE
        FROM {FID} WHERE snapshot_date = DATE '2019-11-30' AND warehouse_id = 1 AND product_id = 1005161""").fetchone()
    print("3. warehouse 1, product 1005161, 30 Nov")
    print(f"   stock_on_hand {r[0]}, velocity_7d stored {r[1]!r}, days_to_stockout stored {r[2]!r}")
    print(f"   16/7 in 64 bit = {16 / 7!r}; 13 / (16/7) in 64 bit = {13 / (16 / 7)!r}")


def main():
    con = duckdb.connect()
    per_warehouse(con)
    column_types(con)
    float_example(con)


if __name__ == "__main__":
    main()
