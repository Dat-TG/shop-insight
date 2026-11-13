"""Parquet footer statistics of fact_event: what row-group skipping can and cannot do.

Read-only. Reads the footers of data/warehouse/fact_event and data/silver with DuckDB
parquet_metadata(), plus one count over fact_event.
Used by the report review of 13 Nov 2026, region R3 (section 4.4.5):
  - edits R3-C2 / R3-C2b: date_key has min/max in all 31 column chunks and min = max in each,
    so footer statistics can skip the other 30 days, but only after opening all 31 footers;
  - edit R3-C15: price max per fact_event row group, share of rows with price > 1000,
    and event_time (INT96) without statistics in both silver and fact_event.
Run: .venv/bin/python docs/evidence/review_20261113/r3_parquet_footer.py
"""
import duckdb

LAYERS = {
    "fact_event": "data/warehouse/fact_event/event_date=*/*.parquet",
    "silver": "data/silver/*/*/*.parquet",
}
COLUMNS = ("date_key", "event_time", "price", "product_sk")


def footer_stats(con, layer, glob):
    files, row_groups = con.sql(f"""
        SELECT count(DISTINCT file_name), count(DISTINCT (file_name, row_group_id))
        FROM parquet_metadata('{glob}')""").fetchone()
    print(f"== {layer}: {files} files, {row_groups} row groups ==")
    rows = con.sql(f"""
        SELECT path_in_schema, any_value(type), count(*) AS chunks,
               count(*) FILTER (WHERE stats_min_value IS NOT NULL) AS with_stats,
               count(*) FILTER (WHERE stats_min_value IS NOT NULL AND stats_min_value = stats_max_value) AS min_eq_max,
               min(TRY_CAST(stats_max_value AS DOUBLE)), max(TRY_CAST(stats_max_value AS DOUBLE))
        FROM parquet_metadata('{glob}')
        WHERE path_in_schema IN {COLUMNS}
        GROUP BY path_in_schema ORDER BY path_in_schema""").fetchall()
    for name, ptype, chunks, with_stats, min_eq_max, lo, hi in rows:
        line = f"{name:<11} {ptype:<8} chunks {chunks:>3}  with min/max {with_stats:>3}  min = max {min_eq_max:>3}"
        if name == "price":
            line += f"  max per row group: {lo:,.2f} .. {hi:,.2f}"
        print(line)


def main():
    con = duckdb.connect()
    for layer, glob in LAYERS.items():
        footer_stats(con, layer, glob)
    rows, over = con.sql(f"""
        SELECT count(*), count(*) FILTER (WHERE price > 1000)
        FROM read_parquet('{LAYERS['fact_event']}', hive_partitioning = true)""").fetchone()
    print(f"fact_event rows with price > 1000: {over:,} of {rows:,} ({over / rows:.2%})")


if __name__ == "__main__":
    main()
