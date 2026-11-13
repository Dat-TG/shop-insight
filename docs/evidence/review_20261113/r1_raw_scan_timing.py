"""Time one parallel engine (DuckDB) answering report 1.3's question on the raw CSV.

Measures: wall time and process CPU time of "revenue per category_l1 for the month"
read straight from data/raw/2019-Nov.csv (9.0 GB), once with the OS page cache as it
is when the script starts, then three more times with the file already cached.
The page cache size (Cached in /proc/meminfo) is printed before each run, so a reader
can tell a cold run from a warm one.

Used by report edit R1-13 (section 1.3, "Hai công cụ này chạy đơn luồng...") and,
through it, R1-15 (section 2.1). Read-only: it reads the CSV and writes nothing.

Run from the repo root:  .venv/bin/python docs/evidence/review_20261113/r1_raw_scan_timing.py
"""
import os
import platform
import resource
import time

import duckdb

CSV = "data/raw/2019-Nov.csv"
COLUMNS = ("{'event_time': 'VARCHAR', 'event_type': 'VARCHAR', 'product_id': 'BIGINT', "
           "'category_id': 'BIGINT', 'category_code': 'VARCHAR', 'brand': 'VARCHAR', "
           "'price': 'DECIMAL(10,2)', 'user_id': 'BIGINT', 'user_session': 'VARCHAR'}")
QUERY = f"""
SELECT coalesce(nullif(split_part(category_code, '.', 1), ''), 'unknown') AS category_l1,
       sum(price) AS revenue, count(*) AS orders
FROM read_csv('{CSV}', header = true, columns = {COLUMNS})
WHERE event_type = 'purchase'
GROUP BY 1 ORDER BY revenue DESC
"""


def page_cache_gb():
    for line in open("/proc/meminfo"):
        if line.startswith("Cached:"):
            return int(line.split()[1]) / 1024 / 1024
    return float("nan")


def cpu_seconds():
    r = resource.getrusage(resource.RUSAGE_SELF)
    return r.ru_utime + r.ru_stime


def timed_run(con, label):
    cache = page_cache_gb()
    t0, c0 = time.perf_counter(), cpu_seconds()
    rows = con.sql(QUERY).fetchall()
    wall, cpu = time.perf_counter() - t0, cpu_seconds() - c0
    print(f"{label:<8} page cache before {cache:5.1f} GB | wall {wall:6.2f} s | "
          f"cpu {cpu:6.1f} s | busy cores (cpu/wall) {cpu / wall:5.1f}")
    return rows


def main():
    print(f"machine  {platform.node()} | {os.cpu_count()} logical cores | "
          f"{os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / 1024**3:.1f} GB RAM")
    print(f"versions Python {platform.python_version()} | DuckDB {duckdb.__version__}")
    print(f"file     {CSV}, {os.path.getsize(CSV):,} bytes")
    print(QUERY.strip())
    con = duckdb.connect()
    rows = timed_run(con, "run 1")
    for i in range(2, 5):
        timed_run(con, f"run {i}")
    print("top 2 groups:", [(k, f"{float(v):,.2f}", n) for k, v, n in rows[:2]])
    print("groups:", len(rows), "| orders:", f"{sum(r[2] for r in rows):,}")


if __name__ == "__main__":
    main()
