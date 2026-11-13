"""Size of the look-ahead bias in dim_user for 1-7 Nov (report section 4.1.3, edit R2-B13).

Events of 1-7 Nov have no earlier RFM snapshot, so batch_warehouse.py gives them
the segment of the first snapshot (7 Nov), computed from data up to the end of
7 Nov. This script counts how many week-one events that touches, and how many
of them happened before the customer's own first purchase (so carry a "bought"
segment while the customer had not bought yet).

Read-only: DuckDB over data/silver and data/warehouse/stg_rfm_snapshot.
Run from the repo root: .venv/bin/python -I docs/evidence/review_20261113/r2_lookahead.py
"""
import duckdb

SILVER = "data/silver/**/*.parquet"
RFM = "data/warehouse/stg_rfm_snapshot/**/*.parquet"


def measure(con):
    return con.sql(f"""
        WITH s AS (
            SELECT user_id, event_time, event_date, event_type
            FROM read_parquet('{SILVER}', hive_partitioning = true)
        ),
        first_buy AS (
            SELECT user_id, min(event_time) AS first_purchase_at
            FROM s WHERE event_type = 'purchase' GROUP BY user_id
        ),
        scored_7nov AS (
            SELECT user_id
            FROM read_parquet('{RFM}', hive_partitioning = true)
            WHERE snapshot_date = DATE '2019-11-07' AND rfm_cell IS NOT NULL
        ),
        week1 AS (
            SELECT s.user_id, s.event_time, f.first_purchase_at,
                   r.user_id IS NOT NULL AS scored
            FROM s
            LEFT JOIN first_buy f USING (user_id)
            LEFT JOIN scored_7nov r USING (user_id)
            WHERE s.event_date BETWEEN DATE '2019-11-01' AND DATE '2019-11-07'
        )
        SELECT
            (SELECT count(*) FROM s)                                        AS silver_events,
            count(*)                                                        AS week1_events,
            count(DISTINCT user_id)                                         AS week1_users,
            count(*) FILTER (WHERE scored)                                  AS week1_events_scored_7nov,
            count(*) FILTER (WHERE scored AND event_time < first_purchase_at)  AS before_first_purchase,
            count(DISTINCT user_id) FILTER (WHERE scored AND event_time < first_purchase_at) AS users_before_first_purchase,
            count(*) FILTER (WHERE scored AND event_time >= first_purchase_at) AS on_or_after_first_purchase
        FROM week1
    """).fetchone()


def main():
    con = duckdb.connect()
    (silver, week1, users, scored, before, users_before, after) = measure(con)
    print(f"silver events                         {silver:>10,}")
    print(f"events 1-7 Nov                        {week1:>10,}  ({week1 / silver:.1%} of silver)")
    print(f"customers with an event 1-7 Nov       {users:>10,}")
    print(f"  events of customers scored at 7 Nov {scored:>10,}")
    print(f"    before their first purchase       {before:>10,}  ({before / week1:.1%} of week-one events), {users_before:,} customers")
    print(f"    at or after their first purchase  {after:>10,}")
    print(f"  events of customers not scored      {week1 - scored:>10,}  (no purchase by 7 Nov: 'not bought' is correct)")


if __name__ == "__main__":
    main()
