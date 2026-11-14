"""How ntile(5) splits ties in BR4's RFM scores (data/warehouse/stg_rfm_snapshot, snapshot 30/11).

Measures, with DuckDB, read-only:
  - buyers at the 30/11 snapshot and how many bought exactly once
  - the f_score of the one-time buyers (ntile breaks the tie by user_id)
  - the segments those one-time buyers land in, against each segment's size
  - the R split of buyers whose last purchase was 5 days before the snapshot
  - snapshot dates present in stg_rfm_snapshot
Scoring code: processing/dim_user.py, score() and segment().
Used by report edit R1-19 (section 2.4) and the BR4 row of manual task M3 (Bảng 2).

Run from the repo root:  .venv/bin/python docs/evidence/review_20261113/r1_rfm_ties.py
"""
import duckdb

RFM = "read_parquet('data/warehouse/stg_rfm_snapshot/*/*.parquet', hive_partitioning = true)"
SNAP = "snapshot_date = DATE '2019-11-30'"


def main():
    con = duckdb.connect()
    print(f"DuckDB {duckdb.__version__}; {RFM}\n")
    dates = [str(d) for (d,) in con.sql(f"SELECT DISTINCT snapshot_date FROM {RFM} ORDER BY 1").fetchall()]
    print("snapshot dates:", ", ".join(dates))
    users, buyers, once = con.sql(f"""SELECT count(*), count(*) FILTER (WHERE frequency > 0),
        count(*) FILTER (WHERE frequency = 1) FROM {RFM} WHERE {SNAP}""").fetchone()
    print(f"30/11: users {users:,}, buyers {buyers:,}, bought once {once:,} ({100 * once / buyers:.1f}% of buyers)")
    print("buyers per frequency (1..5, >= 6):",
          con.sql(f"""SELECT list(n ORDER BY k) FROM (SELECT least(frequency, 6) AS k, count(*) AS n
              FROM {RFM} WHERE {SNAP} AND frequency > 0 GROUP BY 1)""").fetchone()[0])
    print("f_score of one-time buyers:",
          con.sql(f"""SELECT f_score, count(*) FROM {RFM} WHERE {SNAP} AND frequency = 1
              GROUP BY 1 ORDER BY 1""").fetchall())
    print("segment: one-time buyers / all buyers in the segment")
    for seg, n_once, n_all in con.sql(f"""SELECT segment, count(*) FILTER (WHERE frequency = 1), count(*)
            FROM {RFM} WHERE {SNAP} AND frequency > 0 GROUP BY 1 ORDER BY 1""").fetchall():
        print(f"   {seg:<16} {n_once:>6,} / {n_all:>6,}  ({100 * n_once / n_all:.1f}%)")
    print("r_score of buyers with recency_days = 5:",
          con.sql(f"""SELECT r_score, count(*) FROM {RFM} WHERE {SNAP} AND recency_days = 5
              GROUP BY 1 ORDER BY 1""").fetchall())


if __name__ == "__main__":
    main()
