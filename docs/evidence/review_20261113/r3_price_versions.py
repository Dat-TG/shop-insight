"""dim_product grain: price versions per change versus per day, and the cost of a range join.

Read-only. Reads data/silver and data/warehouse/dim_product with DuckDB.
Used by the report review of 13 Nov 2026, region R3, edit R3-C4 (section 4.4.3):
  - versions if every price change opened one (ordered by event_time, then price for ties),
    against the 210,454 day-grain versions of dim_product;
  - the same for product 1005115;
  - rows a range join (event x every version of its product) would produce
    with per-change versions: sum over products of events x versions.
Run: .venv/bin/python docs/evidence/review_20261113/r3_price_versions.py
"""
import duckdb

SILVER = "data/silver/*/*/*.parquet"
DIM_PRODUCT = "data/warehouse/dim_product/*.parquet"
HOT_PRODUCT = 1005115


def main():
    con = duckdb.connect()
    con.sql(f"""
        CREATE TEMP TABLE changes AS
        SELECT product_id,
               price IS DISTINCT FROM lag(price) OVER (PARTITION BY product_id ORDER BY event_time, price)
                   AS opens_version
        FROM read_parquet('{SILVER}', hive_partitioning = true)""")
    con.sql("""
        CREATE TEMP TABLE per_product AS
        SELECT product_id, count(*) AS events, count(*) FILTER (WHERE opens_version) AS versions
        FROM changes GROUP BY product_id""")
    products, events, versions, join_rows = con.sql(
        "SELECT count(*), sum(events), sum(versions), sum(events * versions) FROM per_product").fetchone()
    print(f"silver: {events:,} events, {products:,} products")
    print(f"versions if every price change opens one: {versions:,}")
    hot_events, hot_versions = con.sql(
        f"SELECT events, versions FROM per_product WHERE product_id = {HOT_PRODUCT}").fetchone()
    print(f"product {HOT_PRODUCT}: {hot_events:,} events, {hot_versions:,} per-change versions")
    print(f"range join rows with per-change versions (sum events x versions): {join_rows:,}"
          f" = {join_rows / events:.1f} x the fact")
    print(f"  of which product {HOT_PRODUCT}: {hot_events * hot_versions:,} ({hot_events * hot_versions / join_rows:.0%})")

    dim_rows, dim_products, hot_dim = con.sql(f"""
        SELECT count(*), count(DISTINCT product_id), count(*) FILTER (WHERE product_id = {HOT_PRODUCT})
        FROM read_parquet('{DIM_PRODUCT}')""").fetchone()
    print(f"dim_product (day grain): {dim_rows:,} versions of {dim_products:,} products; "
          f"product {HOT_PRODUCT}: {hot_dim} versions")


if __name__ == "__main__":
    main()
