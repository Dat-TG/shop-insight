"""BR2's and BR7's screen questions computed at read time straight from the full raw CSV.

Measures the wall time (execute + fetchall) DuckDB needs over data/raw/2019-Nov.csv (all
67,501,979 events, no cleaning rules, UTC times) for:
  - BR2: the month's per-session funnel (sessions with a view / cart / purchase, and event counts)
  - BR7: the ten partners of product 1005115 with gold_br7.py's cut-offs (>= 20 sessions per
    product, >= 3 sessions per pair, lift > 1)
One warm-up count(*) first, so the file sits in the OS page cache as far as RAM allows; then
3 timed runs per question. This is the read-time side only: silver and the gold tables exist
for the 7% sample, not for the full file, so the gold side at this size is not measured.

Used by report edit R5-E1 (section 6.2.1, the paragraph on the full data). Read-only; DuckDB may
spill to a temporary directory outside the repo.

Run from the repo root:  .venv/bin/python -I docs/evidence/review_20261113/r5_fullcsv.py
"""
import os
import platform
import tempfile
import time

import duckdb

CSV = """read_csv('data/raw/2019-Nov.csv', header=true, columns={'event_time':'VARCHAR','event_type':'VARCHAR',
 'product_id':'BIGINT','category_id':'BIGINT','category_code':'VARCHAR','brand':'VARCHAR','price':'DOUBLE',
 'user_id':'BIGINT','user_session':'VARCHAR'})"""

BR2 = f"""WITH per AS (SELECT user_session,
    count(*) FILTER (WHERE event_type = 'view') v, count(*) FILTER (WHERE event_type = 'cart') c,
    count(*) FILTER (WHERE event_type = 'purchase') p FROM {CSV} GROUP BY 1)
SELECT count(*) FILTER (WHERE v + c + p > 0), count(*) FILTER (WHERE c > 0 OR p > 0), count(*) FILTER (WHERE p > 0),
  sum(v), sum(c), sum(p) FROM per"""

BR7 = f"""WITH baskets AS (SELECT DISTINCT user_session, product_id FROM {CSV} WHERE event_type = 'purchase'),
  n AS (SELECT count(DISTINCT user_session) AS n FROM baskets),
  popular AS (SELECT product_id, count(*) AS k FROM baskets GROUP BY 1 HAVING count(*) >= 20),
  kept AS (SELECT b.* FROM baskets b JOIN popular USING (product_id)),
  pairs AS (SELECT a.product_id pa, b.product_id pb, count(*) co FROM kept a JOIN kept b
    ON a.user_session = b.user_session AND a.product_id <> b.product_id
    WHERE a.product_id = 1005115 GROUP BY 1, 2 HAVING count(*) >= 3)
SELECT pb, co, co * n.n / (x.k * y.k) AS lift FROM pairs, n, popular x, popular y
WHERE x.product_id = pa AND y.product_id = pb AND co * n.n / (x.k * y.k) > 1
ORDER BY lift DESC, co DESC LIMIT 10"""


def page_cache_gb():
    with open("/proc/meminfo") as f:
        info = dict(line.split(":", 1) for line in f)
    return int(info["Cached"].split()[0]) / 1024 / 1024


def run(con, name, sql, i):
    load = os.getloadavg()[0]
    t0 = time.perf_counter()
    rows = con.execute(sql).fetchall()
    s = time.perf_counter() - t0
    print(f"{name:26} run {i}  {s:5.1f} s  (load before {load:5.2f})  first row {rows[0]}  rows {len(rows)}", flush=True)


def main():
    print(f"machine  {platform.node()} | {os.cpu_count()} logical cores")
    print(f"versions Python {platform.python_version()} | DuckDB {duckdb.__version__}")
    print(f"file     data/raw/2019-Nov.csv, {os.path.getsize('data/raw/2019-Nov.csv'):,} bytes")
    with tempfile.TemporaryDirectory() as tmp:
        con = duckdb.connect()
        con.execute(f"SET memory_limit='6GB'; SET temp_directory='{tmp}'")
        threads = con.execute("SELECT current_setting('threads')").fetchone()[0]
        print(f"threads  {threads}")
        print(f"page cache before warm-up {page_cache_gb():.1f} GB")
        run(con, "warm-up count(*)", f"SELECT count(*) FROM {CSV}", 0)
        print(f"page cache after warm-up  {page_cache_gb():.1f} GB")
        for i in (1, 2, 3):
            run(con, "BR2 per-session funnel", BR2, i)
        for i in (1, 2, 3):
            run(con, "BR7 partners of 1005115", BR7, i)


if __name__ == "__main__":
    main()
