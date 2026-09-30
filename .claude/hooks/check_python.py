#!/usr/bin/env python3
"""PostToolUse hook (matcher: Write|Edit). Two passes over a just-edited .py file.

Pass 1, syntax: the file is compiled with the standard library. A SyntaxError is
reported with file, line and message, on stdout as additionalContext, on stderr,
and with exit code 2. (Claude Code documents PostToolUse as non-blocking - exit 2
is ignored there - so exit 2 is the strongest signal available, and
additionalContext is what actually reaches the model.)

Pass 2, project traps: a short list of regex checks for the mistakes that this
project has already decided are expensive. Advisory only, never blocking, at most
5 warnings, each one line naming the consequence.

Every check is written so it CANNOT fire on correct code - a warning always means
something. Comments and docstrings are blanked out before matching (see
strip_prose), so the reference implementation can explain a trap in prose without
tripping the check that documents it. The one remaining edge: prose inside an
ordinary string literal - a print() message - is still read as code.

Two checks from the project's trap list were deliberately left out
because no precise regex exists for them: "batch jobs must not wait for the
stream" is about run order, not text, and "no abstractions" cannot be told apart
from a legitimate class by pattern alone.

Fails OPEN: any unexpected error exits 0 and prints nothing.
"""

import io
import json
import os
import re
import sys
import tokenize

PROJECT_DIR = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

# A STRING token is prose when it stands alone as a whole statement - a module,
# class or function docstring. That is recognised by its neighbours: a statement
# boundary before it, the end of the statement after it.
PROSE_BEFORE = (tokenize.NEWLINE, tokenize.NL, tokenize.INDENT, tokenize.DEDENT, tokenize.STRING)
PROSE_AFTER = (tokenize.NEWLINE, tokenize.STRING)


def without_comment_lines(text):
    """Drop whole-line # comments. Fallback for when tokenize refuses the file."""
    return "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))


def next_type(tokens, index):
    """Type of the next token after index, skipping a trailing comment."""
    for position in range(index + 1, len(tokens)):
        if tokens[position].type != tokenize.COMMENT:
            return tokens[position].type
    return None


def blank(lines, start, end):
    """Overwrite one token's characters with spaces, in place, line by line."""
    (first_row, first_column), (last_row, last_column) = start, end
    for row in range(first_row, last_row + 1):
        line = lines[row - 1]
        left = first_column if row == first_row else 0
        right = last_column if row == last_row else len(line)
        lines[row - 1] = line[:left] + " " * (right - left) + line[right:]


def strip_prose(text):
    """Blank out comments and docstrings, so prose cannot trip a check below.

    CLAUDE.md makes commented code the team's handover channel and BR1 the
    heavily-commented reference implementation the other three copy, so a
    docstring that documents a trap ("we pass EVENT_SCHEMA explicitly because
    readStream cannot infer schema") must not trip the check that documents it.

    Comments and docstrings only, never every string literal: half the checks
    below match text that lives inside a string in correct code - the CQL
    statements, "data/silver", "checkpointLocation", "rfm_cell", "cassandra",
    "Asia/Ho_Chi_Minh". Blanking every STRING would leave a hook that fires on
    nothing.

    Characters are replaced with spaces rather than removed, so line numbers and
    the ^ anchor of the banned-import check still line up. Any tokenize error
    falls back to without_comment_lines, the behaviour this replaced.
    """
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except Exception:
        return without_comment_lines(text)
    lines = text.split("\n")
    previous = tokenize.NEWLINE
    for index, token in enumerate(tokens):
        if token.type == tokenize.COMMENT or (
                token.type == tokenize.STRING
                and previous in PROSE_BEFORE
                and next_type(tokens, index) in PROSE_AFTER):
            blank(lines, token.start, token.end)
        if token.type != tokenize.COMMENT:
            previous = token.type
    return "\n".join(lines)


def find_warnings(path, source):
    name = os.path.basename(path)
    code = strip_prose(source)
    upper = code.upper()

    def has(pattern):
        return re.search(pattern, code, re.IGNORECASE | re.MULTILINE) is not None

    found = []

    if "readStream" in code and ".schema(" not in code:
        found.append("readStream without .schema(EVENT_SCHEMA): Structured Streaming cannot infer schema, so the query never starts.")

    if "writeStream" in code and "checkpointLocation" not in code and not has(r"""format\(\s*["'](console|memory)["']"""):
        found.append("writeStream without checkpointLocation: all streaming state is lost on restart and the job reprocesses from zero.")

    if ("from_utc_timestamp" in code or "Asia/Ho_Chi_Minh" in code) and "to_date(" not in code:
        found.append("event_time shifted to UTC+7 but event_date never recomputed: every event between 17:00 and 24:00 UTC is misfiled and BR1, BR2, BR6 skew.")

    if has(r"""\.config\(\s*["']spark\.driver\.memory"""):
        found.append("spark.driver.memory on SparkSession.builder only works if that builder starts the JVM; once one runs (shell, notebook, earlier session) it is ignored, silently after stop(): keep it in conf/spark-defaults.conf.")

    if "spark.executor.memory" in code:
        found.append("spark.executor.memory does nothing in local[*]: the driver IS the executor, so the setting is a no-op and the time spent on it is wasted.")

    if "data/silver" in code and name != "batch_silver.py" and ("writeStream" in code or "foreachBatch" in code):
        found.append("silver has exactly one writer, batch_silver.py: a streaming write creates data/silver/_spark_metadata/ or duplicates replayed rows, which voids the >=99% correctness gate.")

    if name == "replayer.py" and ("data/raw" in code or "2019-Nov.csv" in code):
        found.append("replayer.py must read data/bronze/ (258,390 users), never raw (3,696,117): a 14x population mismatch makes the correctness gate unreachable for BR1, BR3, BR5, BR8.")

    if has(r"insert\s+into\s+(\w+\.)?trending_products") and not has(r"delete[^;\n]*trending_products"):
        found.append("trending_products re-emits each window: DELETE WHERE window_start = ? before inserting the new top-N, or a product at rank 3 then rank 5 is returned twice by LIMIT 20.")

    if has(r"insert\s+into\s+(\w+\.)?stockout_risk") and not has(r"delete[^;\n]*stockout_risk"):
        found.append("stockout_risk rewrites every warehouse in full: DELETE WHERE warehouse_id = ? before inserting, or the BR6 screen shows duplicate SKUs.")

    # TRUNCATE too: inside write_batch it is worse than a DELETE, erasing every day, not one.
    # streaming_gold.py --fresh empties the table legitimately, but through STREAMING_TABLES,
    # so the name never stands on the same line as the word and this does not fire on it.
    if has(r"(delete|truncate)[^;\n]*abandoned_carts"):
        found.append("abandoned_carts must never be deleted from or truncated: it accumulates through the day, so a DELETE erases every cart found in earlier micro-batches (a TRUNCATE, every day's) and the BR5 screen empties itself mid-demo. The one reset is streaming_gold.py --fresh, before any query starts.")

    if has(r"stock_on_hand\s*/\s*velocity_7d") and "9999" not in code:
        found.append("days_to_stockout is a Cassandra clustering column and cannot be null: use when(velocity_7d > 0, ...).otherwise(9999.0) - velocity_7d is 0 for ~90% of SKUs, so nine inserts in ten would fail.")

    if "rfm_cell" in code and ("!=" in code or "<>" in code) and "eqNullSafe" not in code and "IS DISTINCT FROM" not in upper:
        found.append("rfm_cell is NULL for 88% of users at the first snapshot and NULL <> NULL is NULL: use eqNullSafe / IS DISTINCT FROM or dim_user emits a new SCD2 version every snapshot for every non-buyer.")

    if has(r"""org\.apache\.spark\.sql\.cassandra|spark-cassandra-connector|format\(\s*["']cassandra["']"""):
        found.append("Spark-Cassandra connector is banned by CLAUDE.md rule 2: write through foreachBatch plus the plain Python cassandra-driver.")

    if has(r"^\s*(import|from)\s+(airflow|dbt|pyflink|redis|pyiceberg|delta)\b") or "io.delta" in code:
        found.append("banned technology import: CLAUDE.md rule 1 forbids Airflow, dbt, Flink, Iceberg/Delta and Redis - each one costs a week the team does not have.")

    return found[:5]


def main():
    payload = json.loads(sys.stdin.read())
    path = payload.get("tool_input", {}).get("file_path") or ""
    if not isinstance(path, str) or not path.endswith(".py"):
        return
    path = os.path.abspath(path)
    if not path.startswith(PROJECT_DIR + os.sep):
        return
    try:
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
    except OSError:
        return

    relative = os.path.relpath(path, PROJECT_DIR)

    try:
        compile(source, path, "exec")
    except SyntaxError as error:
        message = "SYNTAX ERROR in %s line %s: %s. The file cannot be imported or run - fix it now." % (
            relative, error.lineno, error.msg)
        print(json.dumps({
            "hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": message},
            "systemMessage": message,
        }))
        sys.stderr.write(message + "\n")
        sys.exit(2)

    warnings = find_warnings(path, source)
    if warnings:
        lines = ["ShopInsight trap check on %s (advisory):" % relative]
        lines += ["  WARNING: " + w for w in warnings]
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": "\n".join(lines),
        }}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # fail open: an edit is never rejected because this hook has a bug
    sys.exit(0)
