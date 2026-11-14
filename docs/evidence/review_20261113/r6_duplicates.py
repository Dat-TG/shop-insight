"""Duplicate events: silver, the 7% bronze sample and the full raw CSV.

Read-only. Reads data/silver, data/bronze and data/raw/2019-Nov.csv with DuckDB.
Used by the report review of 13 Nov 2026, region R6:
  - edit R6-7.1-dups (7.1): exact duplicates in the raw file (cart and purchase), and
    the same product bought several times in one session;
  - edit R6-7.2-dedup (7.2): deduplicating silver on four columns removes exactly the
    rows that an all-column DISTINCT removes;
  - manual task R6-M-table (new table in 7.1): duplicated cart events, sample vs full file.
An "exact duplicate" is a row identical to another one on every column; the extra
rows are count - 1 per group.
Run: .venv/bin/python docs/evidence/review_20261113/r6_duplicates.py
"""
import tempfile

import duckdb

SILVER = "read_parquet('data/silver/*/*/*.parquet', hive_partitioning = true)"
BRONZE = "read_parquet('data/bronze/*/*.parquet', hive_partitioning = true)"
RAW = "read_csv('data/raw/2019-Nov.csv', header = true, all_varchar = true)"


def per_type_duplicates(con, source, types=None):
    """(event_type, events, extra duplicate rows, largest group) for one source."""
    where = ""
    if types:
        where = "WHERE event_type IN (" + ", ".join(f"'{t}'" for t in types) + ")"
    return con.sql(f"""
        WITH e AS (SELECT * FROM {source} {where}),
        totals AS (SELECT event_type, count(*) AS events FROM e GROUP BY 1),
        dups AS (SELECT event_type, sum(c - 1) AS extra, max(c) AS biggest
                 FROM (SELECT *, count(*) AS c FROM e GROUP BY ALL HAVING count(*) > 1)
                 GROUP BY 1)
        SELECT t.event_type, t.events, coalesce(d.extra, 0), coalesce(d.biggest, 1)
        FROM totals t LEFT JOIN dups d USING (event_type) ORDER BY 1""").fetchall()


def show(label, rows):
    print(label)
    for event_type, events, extra, biggest in rows:
        print(f"  {event_type:9s} events {events:>11,}  extra duplicate rows {extra:>7,} "
              f"({extra / events:.2%})  largest group {biggest}")


def main():
    con = duckdb.connect()
    con.execute(f"SET temp_directory = '{tempfile.gettempdir()}/duckdb_r6'")

    show("silver, exact duplicates by event_type:", per_type_duplicates(con, SILVER))
    total, distinct_all, distinct_four = con.sql(f"""
        SELECT (SELECT count(*) FROM {SILVER}),
               (SELECT count(*) FROM (SELECT DISTINCT * FROM {SILVER})),
               (SELECT count(*) FROM (SELECT DISTINCT user_session, product_id, event_type, event_time
                                      FROM {SILVER}))""").fetchone()
    print(f"silver rows {total:,}; removed by DISTINCT on every column {total - distinct_all:,}; "
          f"removed by DISTINCT on (user_session, product_id, event_type, event_time) {total - distinct_four:,}")

    purchases, extra_same = con.sql(f"""
        SELECT (SELECT count(*) FROM {SILVER} WHERE event_type = 'purchase'),
               (SELECT sum(c - 1) FROM (SELECT user_session, product_id, count(*) AS c FROM {SILVER}
                                        WHERE event_type = 'purchase' GROUP BY ALL HAVING count(*) > 1))
        """).fetchone()
    print(f"silver purchases {purchases:,}; same product bought again in the same session: "
          f"{extra_same:,} extra rows ({extra_same / purchases:.2%})")

    show("bronze (7% sample, before cleaning), exact duplicates by event_type:",
         per_type_duplicates(con, BRONZE))
    show("raw CSV (all 67.5M events), exact duplicates, cart and purchase only:",
         per_type_duplicates(con, RAW, types=("cart", "purchase")))


if __name__ == "__main__":
    main()
