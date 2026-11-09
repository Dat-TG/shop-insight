"""The query benchmark (T12): every query in benchmark/queries.sql, timed on Postgres, DuckDB and Cassandra.

    .venv/bin/python benchmark/run_benchmark.py
    .venv/bin/python benchmark/run_benchmark.py --only postgres --only duckdb --runs 20 --warmup 3

Protocol, for every (system, query, variant) block of queries.sql, in file order:
  1. run the block's setup statements once (SET enable_*, the benchmark index), on the
     connection every run of that system shares;
  2. --warmup runs of the timed query, not recorded (cold caches, first plan);
  3. --runs timed runs. Each is client-side wall time, time.perf_counter() around
     execute + fetch of ALL rows, so driver and transfer cost are included, the way a
     screen would see them;
  4. one EXPLAIN (ANALYZE, BUFFERS) on Postgres or EXPLAIN ANALYZE on DuckDB, written to
     plans_<ts>.txt and checked against the block's "-- expect:" lines; Cassandra has no
     EXPLAIN, so one traced execution is written and checked instead;
  5. Postgres only: RESET ALL and DROP INDEX IF EXISTS bench_fe_time_btree, in a finally.

p50 and p95 use the nearest-rank method over the timed runs: sort the n values, take
the value at 1-based rank ceil(p / 100 * n). No interpolation, so every reported number
is one that was actually measured. With n = 20, p50 is the 10th value and p95 the 19th.

Outputs in --out-dir, ts = local time YYYYMMDD_HHMMSS:
  raw_<ts>.csv      system,query,variant,run,ms,rows - one line per timed run
  summary_<ts>.csv  system,query,variant,runs,p50_ms,p95_ms,min_ms,max_ms,mean_ms,rows
  env_<ts>.txt      machine, versions, git commit, command line, table row counts
  plans_<ts>.txt    one plan (or trace) per variant, with the expect checks

Prints BENCHMARK OK at the end, or BENCHMARK FAILED (exit 1) when a plan did not
match its "-- expect:" lines: then the forced plan did not take effect and that
variant's numbers measure something else. An empty Cassandra table only warns.

Run it with nothing else on the CPU (no Spark, no stream, no browser build). It
reads only, apart from the benchmark-only B-tree index it creates and drops, and
the ANALYZE that follows it. It never touches warehouse/ddl.sql's own objects.
"""

import argparse
import csv
import datetime as dt
import math
import os
import platform
import shlex
import subprocess
import sys
import time
from pathlib import Path

import cassandra
import duckdb
import psycopg2
from cassandra.cluster import EXEC_PROFILE_DEFAULT, Cluster, ExecutionProfile
from cassandra.policies import DCAwareRoundRobinPolicy

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from serving.check_infra import read_env  # noqa: E402  (needs REPO on sys.path)

QUERIES = REPO / "benchmark" / "queries.sql"
SYSTEMS = ["postgres", "duckdb", "cassandra"]
BENCH_INDEX = "bench_fe_time_btree"     # created by postgres.event_time_one_hour.btree
CASSANDRA_DC = "datacenter1"            # as in serving/api/cassandra.py
CASSANDRA_TIMEOUT_S = 120               # ALLOW FILTERING scans the whole table

# Row counts written to env_<ts>.txt before any timing.
PG_TABLES = ["fact_event", "dim_product", "dim_event_type"]
CASSANDRA_TABLES = ["gmv_by_minute", "stockout_risk"]


def parse_queries(path):
    """The blocks of queries.sql, in file order: dicts with system, query, variant,
    setup (statements), sql (the timed statement), expect and expect_not."""
    blocks = []
    for line in path.read_text().splitlines():
        if line.startswith("-- name:"):
            system, query, variant = line.split(":", 1)[1].strip().split(".")
            blocks.append({"system": system, "query": query, "variant": variant,
                           "expect": [], "expect_not": [], "lines": []})
        elif not blocks:
            continue                                    # the file header
        elif line.startswith("-- expect not:"):
            blocks[-1]["expect_not"].append(line.split(":", 1)[1].strip())
        elif line.startswith("-- expect:"):
            blocks[-1]["expect"].append(line.split(":", 1)[1].strip())
        elif not line.lstrip().startswith("--"):
            blocks[-1]["lines"].append(line)
    for b in blocks:
        statements = [s.strip() for s in "\n".join(b.pop("lines")).split(";") if s.strip()]
        b["setup"], b["sql"] = statements[:-1], statements[-1]
    return blocks


def percentile(values, p):
    """Nearest-rank percentile: the value at 1-based rank ceil(p/100 * n) of the sorted values."""
    ordered = sorted(values)
    return ordered[max(1, math.ceil(p / 100 * len(ordered))) - 1]


def check_plan(block, plan):
    """The expect lines this plan breaks, as a list of messages (empty = plan OK)."""
    missing = [f"missing '{t}'" for t in block["expect"] if t not in plan]
    present = [f"unexpected '{t}'" for t in block["expect_not"] if t in plan]
    return missing + present


def time_runs(run_once, warmup, runs):
    """Warm-up runs, then timed runs. run_once() executes and fetches, returning the row count."""
    for _ in range(warmup):
        run_once()
    timings = []
    for i in range(1, runs + 1):
        start = time.perf_counter()
        rows = run_once()
        timings.append((i, (time.perf_counter() - start) * 1000.0, rows))
    return timings


# --- the three systems ---------------------------------------------------------------

def pg_connect():
    env = read_env()
    conn = psycopg2.connect(host=env["POSTGRES_HOST"], port=int(env["POSTGRES_PORT"]),
                            dbname=env["POSTGRES_DB"], user=env["POSTGRES_USER"],
                            password=env["POSTGRES_PASSWORD"])
    conn.autocommit = True
    return conn


def pg_fetch(cur, sql):
    cur.execute(sql)
    return cur.fetchall()


def run_postgres(blocks, args, record):
    conn = pg_connect()
    cur = conn.cursor()
    cur.execute(f"DROP INDEX IF EXISTS {BENCH_INDEX}")   # left over by a crashed run
    try:
        for b in blocks:
            try:
                for statement in b["setup"]:
                    cur.execute(statement)
                timings = time_runs(lambda: len(pg_fetch(cur, b["sql"])), args.warmup, args.runs)
                plan = "\n".join(r[0] for r in pg_fetch(cur, "EXPLAIN (ANALYZE, BUFFERS) " + b["sql"]))
                record(b, timings, plan)
            finally:
                cur.execute("RESET ALL")
                cur.execute(f"DROP INDEX IF EXISTS {BENCH_INDEX}")
    finally:
        conn.close()


def run_duckdb(blocks, args, record):
    con = duckdb.connect()                              # one in-memory connection for every run
    warehouse = str(Path(args.data_dir) / "warehouse")
    try:
        for b in blocks:
            sql = b["sql"].replace("{warehouse}", warehouse)
            for statement in b["setup"]:
                con.execute(statement.replace("{warehouse}", warehouse))
            timings = time_runs(lambda: len(con.execute(sql).fetchall()), args.warmup, args.runs)
            plan = con.execute("EXPLAIN ANALYZE " + sql).fetchall()[0][1]
            record(b, timings, plan)
    finally:
        con.close()


def cassandra_connect():
    env = read_env()
    profile = ExecutionProfile(load_balancing_policy=DCAwareRoundRobinPolicy(local_dc=CASSANDRA_DC),
                               request_timeout=CASSANDRA_TIMEOUT_S)
    cluster = Cluster([env["CASSANDRA_HOST"]], port=int(env["CASSANDRA_PORT"]),
                      execution_profiles={EXEC_PROFILE_DEFAULT: profile})
    return cluster, cluster.connect(env["CASSANDRA_KEYSPACE"])


def run_cassandra(blocks, args, record):
    cluster, session = cassandra_connect()
    try:
        for b in blocks:
            for statement in b["setup"]:
                session.execute(statement)
            prepared = session.prepare(b["sql"])         # prepared once, as the API routers do
            timings = time_runs(lambda: len(list(session.execute(prepared))), args.warmup, args.runs)
            if timings and timings[-1][2] == 0:
                print(f"  WARNING cassandra.{b['query']}.{b['variant']} returned 0 rows: is the table empty?")
            result = session.execute(prepared, trace=True)
            trace = result.get_query_trace(max_wait_sec=30)
            events = [f"{e.source_elapsed}  {e.description}" for e in trace.events]
            plan = (f"trace: {len(events)} events, duration {trace.duration}\n"
                    + "\n".join(events))
            record(b, timings, plan)
    finally:
        cluster.shutdown()


# --- environment -----------------------------------------------------------------------

def git(*argv):
    return subprocess.run(["git", *argv], cwd=REPO, capture_output=True, text=True).stdout.strip()


def ram_gb():
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemTotal:"):
            return f"{int(line.split()[1]) / 1024 / 1024:.1f} GB"
    return "unknown"


def environment(args, systems):
    """The env_<ts>.txt lines. Opens its own short connections, so it runs before timing."""
    dirty = git("status", "--porcelain", "--untracked-files=no")
    lines = [
        f"date               {dt.datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"host               {platform.node()}",
        f"cpu_count          {os.cpu_count()}",
        f"ram                {ram_gb()}",
        f"os                 {platform.platform()}",
        f"kernel             {platform.release()}",
        f"python             {platform.python_version()}",
        f"duckdb             {duckdb.__version__}",
        f"psycopg2           {psycopg2.__version__}",
        f"cassandra-driver   {cassandra.__version__}",
        f"git_commit         {git('rev-parse', 'HEAD')}",
        f"git_dirty          {'yes' if dirty else 'no'}  (tracked files only)",
        f"command            {shlex.join([sys.executable, *sys.argv])}",
        f"runs               {args.warmup} warm-up + {args.runs} timed per variant",
        f"data_dir           {args.data_dir}",
    ]
    if "postgres" in systems:
        conn = pg_connect()
        cur = conn.cursor()
        lines.append(f"postgres_version   {pg_fetch(cur, 'SHOW server_version')[0][0]}")
        for setting in ["shared_buffers", "work_mem", "max_parallel_workers_per_gather", "jit"]:
            lines.append(f"postgres {setting:<32} {pg_fetch(cur, f'SHOW {setting}')[0][0]}")
        for table in PG_TABLES:
            lines.append(f"postgres rows {table:<27} {pg_fetch(cur, f'SELECT count(*) FROM {table}')[0][0]:,}")
        conn.close()
    if "duckdb" in systems:
        con = duckdb.connect()
        warehouse = Path(args.data_dir) / "warehouse"
        for table, glob in [("fact_event", "fact_event/event_date=*/*.parquet"),
                            ("dim_product", "dim_product/*.parquet")]:
            files = len(list(warehouse.glob(glob)))
            count = con.execute(f"SELECT count(*) FROM read_parquet('{warehouse / glob}')").fetchone()[0]
            lines.append(f"duckdb rows {table:<29} {count:,}  ({files} files)")
        con.close()
    if "cassandra" in systems:
        cluster, session = cassandra_connect()
        lines.append(f"cassandra_version  {session.execute('SELECT release_version FROM system.local').one()[0]}")
        for table in CASSANDRA_TABLES:
            count = session.execute(f"SELECT count(*) FROM {table}").one()[0]
            lines.append(f"cassandra rows {table:<26} {count:,}")
            if count == 0:
                print(f"WARNING Cassandra table {table} is empty: its variants will return 0 rows")
        cluster.shutdown()
    return lines


# --- main ------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs", type=int, default=20, help="timed runs per variant (default 20)")
    parser.add_argument("--warmup", type=int, default=3, help="untimed warm-up runs per variant (default 3)")
    parser.add_argument("--only", action="append", choices=SYSTEMS,
                        help="run only this system; repeat for several (default: all three)")
    parser.add_argument("--data-dir", default=str(REPO / "data"), help="holds warehouse/ (default REPO/data)")
    parser.add_argument("--out-dir", default=str(REPO / "benchmark" / "results"),
                        help="where the four output files go (default REPO/benchmark/results)")
    args = parser.parse_args()
    if args.runs < 1 or args.warmup < 0:
        parser.error("--runs must be >= 1 and --warmup >= 0")
    systems = [s for s in SYSTEMS if s in (args.only or SYSTEMS)]

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = {name: out / f"{name}_{ts}.{ext}"
             for name, ext in [("raw", "csv"), ("summary", "csv"), ("env", "txt"), ("plans", "txt")]}

    paths["env"].write_text("\n".join(environment(args, systems)) + "\n")
    blocks = parse_queries(QUERIES)
    summary, failures = [], []

    with paths["raw"].open("w", newline="") as raw_file, paths["plans"].open("w") as plans_file:
        raw = csv.writer(raw_file)
        raw.writerow(["system", "query", "variant", "run", "ms", "rows"])

        def record(b, timings, plan):
            """Write one variant's runs, plan and summary line, and print its progress line."""
            name = f"{b['system']}.{b['query']}.{b['variant']}"
            for run, ms, rows in timings:
                raw.writerow([b["system"], b["query"], b["variant"], run, f"{ms:.3f}", rows])
            raw_file.flush()
            ms = [t[1] for t in timings]
            p50, p95 = percentile(ms, 50), percentile(ms, 95)
            rows = timings[-1][2]
            summary.append([b["system"], b["query"], b["variant"], len(ms), f"{p50:.3f}", f"{p95:.3f}",
                            f"{min(ms):.3f}", f"{max(ms):.3f}", f"{sum(ms) / len(ms):.3f}", rows])
            problems = check_plan(b, plan)
            failures.extend(f"{name}: {p}" for p in problems)
            plans_file.write(f"{'=' * 100}\n{name}\n{'=' * 100}\n")
            for statement in b["setup"]:
                plans_file.write(f"setup: {statement}\n")
            plans_file.write(f"query: {b['sql']}\n")
            plans_file.write(f"plan check: {'OK' if not problems else 'FAILED ' + '; '.join(problems)}"
                             f"  (expect {b['expect']}, expect not {b['expect_not']})\n")
            plans_file.write(f"\n{plan}\n\n")
            plans_file.flush()
            flag = "" if not problems else "  PLAN CHECK FAILED"
            print(f"{name:<48} p50 {p50:8.1f} ms  p95 {p95:8.1f} ms  rows {rows}{flag}", flush=True)

        runners = {"postgres": run_postgres, "duckdb": run_duckdb, "cassandra": run_cassandra}
        for system in systems:
            runners[system]([b for b in blocks if b["system"] == system], args, record)

    with paths["summary"].open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["system", "query", "variant", "runs", "p50_ms", "p95_ms",
                         "min_ms", "max_ms", "mean_ms", "rows"])
        writer.writerows(summary)

    for name in ["raw", "summary", "env", "plans"]:
        print(f"{name:<8} {paths[name]}")
    if failures:
        print("BENCHMARK FAILED - these forced plans did not take effect:")
        for failure in failures:
            print(f"  {failure}")
        sys.exit(1)
    print("BENCHMARK OK")


if __name__ == "__main__":
    main()
