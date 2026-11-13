"""How far the streaming branch's labels drift from the warehouse (report section 4.1.6, edit R2-B7).

The streaming BRs read silver-shaped events, not the Type 2 dim_product. This
script joins every silver event to the dim_product version valid on its
event_date (valid_from <= event_date < valid_to) and counts how often the
event's own category_l1 and brand differ from that version's. It also counts
the products whose brand varies inside silver, the root cause of the drift,
and the size of dim_product's current version (the broadcast candidate).

Read-only: DuckDB over data/silver and data/warehouse/dim_product.
Run from the repo root: .venv/bin/python -I docs/evidence/review_20261113/r2_brand_drift.py
"""
import duckdb

SILVER = "data/silver/**/*.parquet"
DIM_PRODUCT = "data/warehouse/dim_product/*.parquet"


def drift(con):
    return con.sql(f"""
        WITH s AS (
            SELECT product_id, event_date, brand, category_l1
            FROM read_parquet('{SILVER}', hive_partitioning = true)
        ),
        p AS (
            SELECT product_id, valid_from, valid_to, brand, category_l1
            FROM read_parquet('{DIM_PRODUCT}')
        ),
        j AS (
            SELECT s.product_id, s.brand AS ev_brand, p.brand AS dim_brand,
                   s.category_l1 AS ev_l1, p.category_l1 AS dim_l1
            FROM s JOIN p
              ON s.product_id = p.product_id
             AND s.event_date >= p.valid_from AND s.event_date < p.valid_to
        )
        SELECT
            (SELECT count(*) FROM s)                                       AS silver_events,
            count(*)                                                       AS joined_events,
            count(*) FILTER (WHERE ev_l1 IS DISTINCT FROM dim_l1)          AS l1_mismatch,
            count(*) FILTER (WHERE ev_brand IS DISTINCT FROM dim_brand)    AS brand_mismatch,
            count(DISTINCT product_id) FILTER (WHERE ev_brand IS DISTINCT FROM dim_brand) AS brand_mismatch_products,
            count(*) FILTER (WHERE ev_brand = 'unknown' AND dim_brand <> 'unknown') AS ev_unknown_dim_real,
            count(*) FILTER (WHERE ev_brand <> 'unknown' AND dim_brand = 'unknown') AS ev_real_dim_unknown,
            count(*) FILTER (WHERE ev_brand <> 'unknown' AND dim_brand <> 'unknown'
                             AND ev_brand <> dim_brand)                    AS two_real_brands
        FROM j
    """).fetchone()


def multi_brand_products(con):
    return con.sql(f"""
        SELECT count(*) FROM (
            SELECT product_id FROM read_parquet('{SILVER}', hive_partitioning = true)
            GROUP BY product_id HAVING count(DISTINCT brand) > 1
        )
    """).fetchone()[0]


def current_versions(con):
    return con.sql(f"SELECT count(*) FROM read_parquet('{DIM_PRODUCT}') WHERE is_current").fetchone()[0]


def main():
    con = duckdb.connect()
    (silver, joined, l1, brand, products, unk_real, real_unk, two_real) = drift(con)
    print(f"silver events                                   {silver:>10,}")
    print(f"events joined to their dim_product version      {joined:>10,}")
    print(f"category_l1 differs from the version            {l1:>10,}")
    print(f"brand differs from the version                  {brand:>10,}  ({brand / joined:.2%}), {products:,} products")
    print(f"  event 'unknown', version a real brand         {unk_real:>10,}")
    print(f"  event a real brand, version 'unknown'         {real_unk:>10,}")
    print(f"  two different real brands                     {two_real:>10,}")
    print(f"products with more than one brand in silver     {multi_brand_products(con):>10,}")
    print(f"dim_product current versions (is_current)       {current_versions(con):>10,}")


if __name__ == "__main__":
    main()
