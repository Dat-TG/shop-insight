"""Why dim_user opens new SCD2 versions, and how many events carry a look-ahead segment.

Read-only. Reads data/silver and data/warehouse/{dim_user,stg_rfm_snapshot} with DuckDB.
Used by the report review of 13 Nov 2026, region R3 (section 4.4):
  - edit R3-AF2 (4.4.3): 61,096 new versions = 23,974 first purchases + 37,122 cell changes;
    31,204 of the changes keep frequency and monetary; 23,172 change only R (always down),
    8,032 change F or M.
  - edit R3-C3 (4.4.1): events on 1-7 Nov and those of users already scored on 7 Nov.
Run: .venv/bin/python docs/evidence/review_20261113/r3_dim_user_versions.py
"""
import duckdb

SILVER = "data/silver/*/*/*.parquet"
DIM_USER = "data/warehouse/dim_user/*.parquet"
RFM = "data/warehouse/stg_rfm_snapshot/*/*.parquet"


def version_breakdown(con):
    print("== dim_user versions ==")
    rows, users, current, new_versions = con.sql(f"""
        SELECT count(*), count(DISTINCT user_id), count(*) FILTER (WHERE is_current),
               count(*) FILTER (WHERE version_no > 1)
        FROM read_parquet('{DIM_USER}')""").fetchone()
    print(f"rows {rows:,}  users {users:,}  current {current:,}  versions with version_no > 1: {new_versions:,}")

    # A new version opens at a snapshot whose rfm_cell differs from the previous snapshot.
    # Compare that snapshot row with the previous snapshot row of the same user.
    con.sql(f"""
        CREATE TEMP TABLE opened AS
        WITH s AS (
            SELECT *, lag(rfm_cell) OVER w AS prev_cell, lag(frequency) OVER w AS prev_f,
                   lag(monetary) OVER w AS prev_m, lag(r_score) OVER w AS prev_r,
                   lag(f_score) OVER w AS prev_fs, lag(m_score) OVER w AS prev_ms,
                   lag(snapshot_date) OVER w AS prev_snap
            FROM read_parquet('{RFM}', hive_partitioning = true)
            WINDOW w AS (PARTITION BY user_id ORDER BY snapshot_date)
        )
        SELECT * FROM s
        WHERE prev_snap IS NOT NULL AND rfm_cell IS DISTINCT FROM prev_cell""")
    total, first_buy, changed = con.sql("""
        SELECT count(*), count(*) FILTER (WHERE prev_cell IS NULL),
               count(*) FILTER (WHERE prev_cell IS NOT NULL) FROM opened""").fetchone()
    print(f"cell changes between snapshots: {total:,}")
    print(f"  NULL -> scored (first purchase): {first_buy:,}")
    print(f"  scored -> other cell:            {changed:,}")
    same_fm, r_only, r_down, r_up, f_or_m = con.sql("""
        SELECT count(*),
               count(*) FILTER (WHERE f_score = prev_fs AND m_score = prev_ms),
               count(*) FILTER (WHERE f_score = prev_fs AND m_score = prev_ms AND r_score < prev_r),
               count(*) FILTER (WHERE f_score = prev_fs AND m_score = prev_ms AND r_score > prev_r),
               count(*) FILTER (WHERE f_score <> prev_fs OR m_score <> prev_ms)
        FROM opened WHERE prev_cell IS NOT NULL AND frequency = prev_f AND monetary = prev_m""").fetchone()
    print(f"  of which frequency and monetary unchanged: {same_fm:,} ({same_fm / changed:.1%} of {changed:,})")
    print(f"    only R changed: {r_only:,} (R down {r_down:,}, R up {r_up:,})")
    print(f"    F or M changed: {f_or_m:,}")


def look_ahead(con):
    print("== events that map to the 7 Nov snapshot ==")
    total, early = con.sql(f"""
        SELECT count(*), count(*) FILTER (WHERE event_date <= DATE '2019-11-07')
        FROM read_parquet('{SILVER}', hive_partitioning = true)""").fetchone()
    scored = con.sql(f"""
        SELECT count(*)
        FROM read_parquet('{SILVER}', hive_partitioning = true) e
        JOIN read_parquet('{RFM}', hive_partitioning = true) r
          ON r.user_id = e.user_id AND r.snapshot_date = DATE '2019-11-07'
        WHERE e.event_date <= DATE '2019-11-07' AND r.rfm_cell IS NOT NULL""").fetchone()[0]
    print(f"silver events: {total:,}")
    print(f"events on 1-7 Nov: {early:,} ({early / total:.1%})")
    print(f"  of users with a 7 Nov RFM cell: {scored:,} ({scored / total:.2%} of all events)")
    snaps = con.sql(f"""
        SELECT string_agg(DISTINCT CAST(snapshot_date AS VARCHAR), ', ' ORDER BY CAST(snapshot_date AS VARCHAR))
        FROM read_parquet('{RFM}', hive_partitioning = true)""").fetchone()[0]
    print(f"snapshot dates: {snaps}")


def main():
    con = duckdb.connect()
    version_breakdown(con)
    look_ahead(con)


if __name__ == "__main__":
    main()
