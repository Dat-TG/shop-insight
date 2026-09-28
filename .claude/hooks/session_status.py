#!/usr/bin/env python3
"""SessionStart hook. Prints where the project is, today, from the filesystem.

CLAUDE.md carries a "Current status" section that goes stale the moment someone
commits a script or generates a tier. This hook reads the real state instead:
which project week it is and what that week is for, which data tiers hold files,
which of the scripts in SYSTEM_DESIGN section 10 exist yet, and whether the two
containers are up.

Everything here is a cheap check - one scandir per directory (capped), one stat,
one docker call with a 1 second timeout. Fails OPEN: any unexpected error exits 0
and prints nothing.
"""

import datetime
import json
import os
import subprocess
import sys

PROJECT_DIR = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
DEADLINE = datetime.date(2026, 11, 15)

# ISO week -> (dates, what the week is for). From PLAN.md's week table.
WEEKS = {
    38: ("14-20 Sep", "kickoff + infrastructure; everyone installs JDK 21, Python 3.14, pyspark==4.1.3, Docker"),
    39: ("21-27 Sep", "everyone generates bronze+silver locally; warehouse layer: 5 dimensions (2 SCD2), 2 generated sources, Postgres DDL"),
    40: ("28 Sep-4 Oct", "streaming foundation + BR1 + BR6; the other 2 facts; BR4/BR7 overflow; star loaded into Postgres. Gate 1a"),
    41: ("5-11 Oct", "streaming BR3, BR5, BR8 + BR2 overflow + benchmark. Gate 1b, and Gate 2a: all 8 BRs demonstrable"),
    42: ("12-18 Oct", "code freeze; every screen measured under 2 s via the QueryMeta footer (Gate 2b); slides; record video"),
    43: ("19-25 Oct", "SUBMIT PRESENTATION; video assembled by Wed 21 Oct (Gate 3); 45-minute rehearsal; demo machine"),
    44: ("26 Oct-1 Nov", "IN-CLASS TALK; the three evaluation experiments: correctness, performance, effectiveness (Gate 4)"),
    45: ("2-8 Nov", "report, 6 sections, plus UI polish. PLAN.md records BR9 as cut"),
    46: ("9-15 Nov", "SUBMIT PROJECT: report + slide + video + product"),
}

TIERS = ["bronze", "silver", "warehouse", "gold", "catalog", "inventory", "stream_landing"]

SCRIPTS = [
    ("ingestion", ["load_bronze.py", "replayer.py", "gen_catalog.py", "gen_inventory.py"]),
    ("processing", ["schema.py", "source.py", "kata.py", "batch_silver.py",
                    "batch_warehouse.py", "dim_product.py", "dim_user.py",
                    "streaming_gold.py", "batch_gold.py"]),
    ("serving", ["check_infra.py", "cassandra_schema.cql", "apply_schema.py",
                 "load_star_postgres.py"]),
]
SINGLE_FILES = ["warehouse/ddl.sql", "seed/holidays_2019.csv", "checks/scd2_integrity.py", "checks/fact_event_spot.py"]


def week_lines(today):
    iso_year, iso_week, _ = today.isocalendar()
    days_left = (DEADLINE - today).days
    if days_left >= 0:
        deadline = "%d days to the 2026-11-15 submission deadline." % days_left
    else:
        deadline = "The 2026-11-15 submission deadline has passed."
    stamp = today.strftime("%Y-%m-%d %a") + " - ISO week %d" % iso_week
    if iso_year != 2026 or iso_week not in WEEKS:
        when = "before W38" if (iso_year, iso_week) < (2026, 38) else "after W46"
        return ["%s - outside the project window W38-W46 (%s)." % (stamp, when), deadline]
    dates, purpose = WEEKS[iso_week]
    return ["%s = project week W%d (%s): %s" % (stamp, iso_week, dates, purpose), deadline]


def count_entries(path, cap=200):
    """Top-level entry count only. Never walks into a multi-GB tree."""
    count = 0
    with os.scandir(path) as entries:
        for entry in entries:
            if entry.name.startswith("."):
                continue
            count += 1
            if count >= cap:
                return "%d+ entries" % cap
    return "%d entries" % count if count else "empty"


def data_line():
    parts = []
    for tier in TIERS:
        path = os.path.join(PROJECT_DIR, "data", tier)
        parts.append("%s %s" % (tier, count_entries(path) if os.path.isdir(path) else "MISSING dir"))
    return "Data tiers: " + ", ".join(parts)


def raw_line():
    path = os.path.join(PROJECT_DIR, "data", "raw", "2019-Nov.csv")
    if not os.path.isfile(path):
        return "Raw: data/raw/2019-Nov.csv absent - each person downloads it from Kaggle themselves; it never travels through git."
    gigabytes = os.path.getsize(path) / 1e9
    return "Raw: data/raw/2019-Nov.csv present, %.1f GB (expected 9.0 GB, 67,501,979 rows)." % gigabytes


def code_lines():
    parts = []
    total_present = 0
    for directory, names in SCRIPTS:
        present = [n for n in names if os.path.isfile(os.path.join(PROJECT_DIR, directory, n))]
        total_present += len(present)
        summary = "%s %d/%d" % (directory, len(present), len(names))
        if present:
            summary += " (" + ", ".join(present) + ")"
        parts.append(summary)
    for relative in SINGLE_FILES:
        exists = os.path.isfile(os.path.join(PROJECT_DIR, relative))
        total_present += 1 if exists else 0
        parts.append("%s %s" % (relative, "present" if exists else "missing"))
    return "Code (SYSTEM_DESIGN section 10): " + ", ".join(parts), total_present


def docker_line():
    try:
        result = subprocess.run(["docker", "ps", "--format", "{{.Names}} {{.Image}}"],
                                capture_output=True, text=True, timeout=1.0)
    except Exception:
        return "Docker: not checked (no docker on PATH, or it did not answer within 1 s)."
    if result.returncode != 0:
        return "Docker: not checked (daemon not reachable)."
    running = result.stdout.lower()
    return "Docker: " + ", ".join(
        "%s %s" % (name, "UP" if name in running else "not running") for name in ("cassandra", "postgres"))


def main():
    sys.stdin.read()
    today = datetime.date.today()
    lines = ["ShopInsight repo status (.claude/hooks/session_status.py, read from disk just now):"]
    lines += week_lines(today)
    lines.append(raw_line())
    lines.append(data_line())
    code, total_present = code_lines()
    lines.append(code)
    lines.append(docker_line())

    bronze = os.path.join(PROJECT_DIR, "data", "bronze")
    if total_present == 0:
        lines.append("No application code exists yet. CLAUDE.md's first task: docs/SETUP_SPARK.md plus processing/kata.py, then bronze and silver so the batch BRs have input.")
    elif not os.path.isdir(bronze) or count_entries(bronze) == "empty":
        lines.append("bronze holds no data, so no batch job can run yet - work through the load order in SYSTEM_DESIGN section 11 first.")

    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": "\n".join(lines),
    }}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # fail open: a session never fails to start because this hook has a bug
    sys.exit(0)
