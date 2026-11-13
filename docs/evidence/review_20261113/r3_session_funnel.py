"""fact_session_funnel: sessions with several users, and sessions that cross midnight.

Read-only. Reads data/silver and data/warehouse/fact_session_funnel with DuckDB.
Used by the report review of 13 Nov 2026, region R3:
  - edit R3-C6 (4.4.2): user_session values that carry more than one user_id;
  - edit R3-C7 (4.4.7): sessions whose last event falls after their start date, and the
    longest span, i.e. how far back a per-date incremental rebuild would have to reach.
Run: .venv/bin/python docs/evidence/review_20261113/r3_session_funnel.py
"""
import duckdb

SILVER = "data/silver/*/*/*.parquet"
FUNNEL = "data/warehouse/fact_session_funnel/*/*.parquet"


def main():
    con = duckdb.connect()
    multi = con.sql(f"""
        SELECT count(*) FROM (
            SELECT user_session FROM read_parquet('{SILVER}', hive_partitioning = true)
            GROUP BY user_session HAVING count(DISTINCT user_id) > 1)""").fetchone()[0]
    print(f"user_session values with more than one user_id (silver): {multi}")

    sessions, crossing, longest = con.sql(f"""
        SELECT count(*),
               count(*) FILTER (WHERE CAST(last_event_at AS DATE) > session_start_date),
               max(date_diff('day', session_start_date, CAST(last_event_at AS DATE)))
        FROM read_parquet('{FUNNEL}', hive_partitioning = true)""").fetchone()
    print(f"fact_session_funnel sessions: {sessions:,}")
    print(f"last event on a later date than the start date: {crossing:,} ({crossing / sessions:.2%})")
    print(f"longest span from start date to last-event date: {longest} days")


if __name__ == "__main__":
    main()
