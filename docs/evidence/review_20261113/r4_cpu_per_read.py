"""CPU cost of one read: the same query on CSV and on silver Parquet, plus the raw file.

Measures: process CPU time (user + system, from resource.getrusage, which counts every
DuckDB worker thread) and wall time of report E4's query, "revenue and orders per
category_l1 for the purchases of the month", read three ways:
  1. data/scratch/sample_7pct.csv (the 7% sample exported as CSV, E4's "before"),
  2. data/silver/*/*/*.parquet (the same 7% sample, cleaned, E4's "after"),
  3. data/raw/2019-Nov.csv (the full 9.0 GB file).
1 and 2: 1 warm-up + 5 timed runs each, a fresh connection per run as the API opens one.
3: 1 warm-up + 3 timed runs (each takes seconds); Cached in /proc/meminfo is printed
before each run so a reader can tell whether the file sat in the OS page cache.

Used by report edit R4-04 (section 4.5.2, the sentence that replaces "Trên tệp gốc,
truy vấn doanh thu theo ngành mất 50 giây..."). Read-only: reads data/, writes nothing.

Run from the repo root:
  .venv/bin/python -I docs/evidence/review_20261113/r4_cpu_per_read.py
"""
import os
import platform
import resource
import statistics
import time

import duckdb

COLUMNS = ("{'event_time': 'VARCHAR', 'event_type': 'VARCHAR', 'product_id': 'BIGINT', "
           "'category_id': 'BIGINT', 'category_code': 'VARCHAR', 'brand': 'VARCHAR', "
           "'price': 'DECIMAL(10,2)', 'user_id': 'BIGINT', 'user_session': 'VARCHAR'}")


def csv_query(path):
    return f"""
SELECT coalesce(nullif(split_part(category_code, '.', 1), ''), 'unknown') AS category_l1,
       sum(price) AS revenue, count(*) AS orders
FROM read_csv('{path}', header = true, columns = {COLUMNS})
WHERE event_type = 'purchase'
GROUP BY 1 ORDER BY revenue DESC"""


SILVER_QUERY = """
SELECT category_l1, sum(price) AS revenue, count(*) AS orders
FROM read_parquet('data/silver/*/*/*.parquet', hive_partitioning = true)
WHERE event_type = 'purchase'
GROUP BY 1 ORDER BY revenue DESC"""


def cpu_seconds():
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_utime + usage.ru_stime


def page_cache_gb():
    with open("/proc/meminfo") as meminfo:
        for line in meminfo:
            if line.startswith("Cached:"):
                return int(line.split()[1]) / 1024 / 1024
    return float("nan")


def one_run(sql):
    """Wall ms, CPU ms and the result rows of one run on a fresh connection."""
    cpu0, wall0 = cpu_seconds(), time.perf_counter()
    with duckdb.connect() as con:
        rows = con.execute(sql).fetchall()
    return (time.perf_counter() - wall0) * 1000, (cpu_seconds() - cpu0) * 1000, rows


def measure(label, sql, timed):
    one_run(sql)  # warm-up
    walls, cpus, rows = [], [], None
    for i in range(timed):
        cache = page_cache_gb()
        wall, cpu, rows = one_run(sql)
        walls.append(wall)
        cpus.append(cpu)
        print(f"  {label:<12} run {i + 1}  page cache before {cache:5.1f} GB | wall {wall:9.1f} ms | cpu {cpu:9.1f} ms")
    orders = sum(row[2] for row in rows)
    print(f"  {label:<12} median wall {statistics.median(walls):9.1f} ms | median cpu {statistics.median(cpus):9.1f} ms"
          f" | groups {len(rows)} | orders {orders:,}")
    return statistics.median(cpus), sorted((row[0], row[2]) for row in rows)


def main():
    print(f"machine  {platform.node()} | {os.cpu_count()} logical cores")
    print(f"versions Python {platform.python_version()} | DuckDB {duckdb.__version__}")
    print("sample CSV vs silver Parquet (7% sample), 1 warm-up + 5 timed runs each")
    csv_cpu, csv_rows = measure("sample CSV", csv_query("data/scratch/sample_7pct.csv"), 5)
    pq_cpu, pq_rows = measure("silver", SILVER_QUERY, 5)
    print(f"  identical result (category, orders): {csv_rows == pq_rows}")
    print(f"  CPU ratio CSV / silver: {csv_cpu / pq_cpu:.1f}")
    print("full raw CSV (data/raw/2019-Nov.csv), 1 warm-up + 3 timed runs")
    raw_cpu, _ = measure("raw CSV", csv_query("data/raw/2019-Nov.csv"), 3)
    print(f"  four screens x one raw read every 10 s: {4 * raw_cpu / 1000:.0f} CPU s per 10 s"
          f" (machine: {os.cpu_count() * 10} CPU s per 10 s)")


if __name__ == "__main__":
    main()
