#!/usr/bin/env bash
# run_demo.sh — ShopInsight demo launcher
#
# Usage:
#   ./run_demo.sh infra    # 1. Start Docker, apply schemas, load static data
#   ./run_demo.sh stream   # 2. Start streaming job + replayer (run AFTER infra)
#   ./run_demo.sh app      # 3. Start API server + React dev server (run AFTER stream)
#   ./run_demo.sh stop     # Stop all background processes started by this script
#
# Recommended order for a fresh demo:
#   ./run_demo.sh infra
#   ./run_demo.sh stream
#   ./run_demo.sh app
#
# PID file: logs/.demo_pids  (stream + app background processes)
# Logs:     logs/stream_YYYYMMDD_HHMMSS.log, logs/replayer_YYYYMMDD_HHMMSS.log,
#           logs/api_YYYYMMDD_HHMMSS.log, logs/web_YYYYMMDD_HHMMSS.log
#           Every line of the stream and replayer logs starts with the wall-clock
#           time to the millisecond (2026-11-10 20:01:02.345 ...), so events/s
#           can be computed from the log alone.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$REPO_DIR/.venv/bin/python"
LOG_DIR="$REPO_DIR/logs"
PID_FILE="$LOG_DIR/.demo_pids"

export SPARK_CONF_DIR="$REPO_DIR/conf"

mkdir -p "$LOG_DIR"

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
info()  { echo -e "\033[1;34m[INFO]\033[0m  $*"; }
ok()    { echo -e "\033[1;32m[ OK ]\033[0m  $*"; }
warn()  { echo -e "\033[1;33m[WARN]\033[0m  $*"; }
die()   { echo -e "\033[1;31m[ERR ]\033[0m  $*" >&2; exit 1; }

check_venv() {
    [[ -x "$VENV" ]] || die ".venv not found. Run: python -m venv .venv && .venv/bin/pip install -r requirements.txt"
}

# Spark needs JAVA_HOME to point at a JDK 21. Keep it when it is set. Otherwise
# derive it from the java on PATH: on Ubuntu /usr/bin/java resolves to
# /usr/lib/jvm/java-21-openjdk-amd64/bin/java, so JAVA_HOME is that minus /bin/java.
# Otherwise, on macOS, ask /usr/libexec/java_home (macOS's /usr/bin/java is a
# launcher stub, not a symlink, so the PATH rule would give /usr). Otherwise stop.
check_java() {
    if [[ -z "${JAVA_HOME:-}" ]]; then
        if command -v java > /dev/null 2>&1; then
            local java_bin
            java_bin="$(readlink -f "$(command -v java)" || true)"
            JAVA_HOME="${java_bin%/bin/java}"
        fi
        if [[ ( -z "${JAVA_HOME:-}" || "${JAVA_HOME:-}" == /usr ) && -x /usr/libexec/java_home ]]; then
            JAVA_HOME="$(/usr/libexec/java_home -v 21 || true)"
        fi
    fi
    [[ -n "${JAVA_HOME:-}" && -x "$JAVA_HOME/bin/java" ]] \
        || die "No JDK found (JAVA_HOME='${JAVA_HOME:-}'). Install OpenJDK 21 (docs/SETUP_SPARK.md steps 2-3) or export JAVA_HOME=<the JDK 21 directory>."
    export JAVA_HOME
    info "JAVA_HOME=$JAVA_HOME"
}

# Copy stdin to stdout, each line prefixed with the wall-clock time to the
# millisecond: "2026-11-10 20:01:02.345 <line>". Used as
#   cmd > >(stamp_lines >> "$LOG") 2>&1 &
# so $! is still cmd's PID: `stop` kills python, and this loop then ends on EOF.
# $EPOCHREALTIME is seconds.microseconds (bash 5); a comma locale writes it with
# a comma, hence [.,].
stamp_lines() {
    trap '' HUP  # survive the terminal closing, like the nohup'd python it reads from
    local line now micros
    while IFS= read -r line || [[ -n "$line" ]]; do
        now="$EPOCHREALTIME"
        micros="${now#*[.,]}"
        printf '%(%Y-%m-%d %H:%M:%S)T.%s %s\n' "${now%[.,]*}" "${micros:0:3}" "$line"
    done
}

# ---------------------------------------------------------------------------
# infra: Docker + schemas + static Postgres load
# ---------------------------------------------------------------------------
cmd_infra() {
    check_venv
    cd "$REPO_DIR"

    info "Starting Docker containers..."
    docker compose up -d --wait
    ok "Containers healthy."

    info "Verifying infra (Cassandra + Postgres)..."
    "$VENV" serving/check_infra.py || die "Infra check failed — see output above."

    info "Applying Cassandra schema..."
    "$VENV" serving/apply_schema.py

    # warehouse/ddl.sql applies once, to an empty database: it has no IF NOT EXISTS
    # on purpose (its header says why), so a second run exits 3 and set -e would
    # stop here. Apply it only when the star schema is not there yet.
    HAS_STAR=$(docker compose exec -T postgres psql -U shopinsight -d shopinsight -tAc \
        "SELECT to_regclass('public.dim_date') IS NOT NULL")
    if [[ "$HAS_STAR" == "t" ]]; then
        ok "Postgres star schema already exists; skipping warehouse/ddl.sql."
    else
        info "Applying Postgres DDL..."
        docker compose exec -T postgres psql -U shopinsight -d shopinsight \
            -v ON_ERROR_STOP=1 < warehouse/ddl.sql
    fi
    ok "Schemas applied."

    # Check if static data already loaded (avoid re-running expensive pipeline)
    PG_ROW_COUNT=$(docker compose exec -T postgres psql -U shopinsight -d shopinsight -tAc \
        "SELECT COUNT(*) FROM fact_event LIMIT 1" 2>/dev/null || echo "0")
    if [[ "$PG_ROW_COUNT" -gt "0" ]]; then
        ok "Postgres star schema already has data ($PG_ROW_COUNT rows in fact_event). Skipping load."
    else
        warn "Postgres fact_event is empty. Run the full batch pipeline:"
        warn "  SPARK_CONF_DIR=conf .venv/bin/python ingestion/load_bronze.py"
        warn "  SPARK_CONF_DIR=conf .venv/bin/python processing/batch_silver.py"
        warn "  .venv/bin/python ingestion/gen_catalog.py"
        warn "  .venv/bin/python ingestion/gen_inventory.py"
        warn "  SPARK_CONF_DIR=conf .venv/bin/python processing/batch_warehouse.py"
        warn "  .venv/bin/python serving/load_star_postgres.py"
        warn "  .venv/bin/python processing/batch_gold.py"
        warn "  .venv/bin/python processing/gold_br7.py"
        warn "Then re-run: ./run_demo.sh infra"
    fi

    ok "Infra step complete."
}

# ---------------------------------------------------------------------------
# stream: streaming_gold.py (--fresh) + replayer
# ---------------------------------------------------------------------------
cmd_stream() {
    check_venv
    check_java
    cd "$REPO_DIR"

    # Verify containers are up
    docker compose ps --services --filter status=running | grep -q cassandra \
        || die "Cassandra not running. Run: ./run_demo.sh infra"
    docker compose ps --services --filter status=running | grep -q postgres \
        || die "Postgres not running. Run: ./run_demo.sh infra"

    TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
    STREAM_LOG="$LOG_DIR/stream_${TIMESTAMP}.log"
    REPLAYER_LOG="$LOG_DIR/replayer_${TIMESTAMP}.log"

    info "Starting streaming_gold.py --fresh ..."
    info "  Log: $STREAM_LOG"
    # PYTHONUNBUFFERED: each line reaches stamp_lines when it is printed, so its
    # timestamp is the time the line was written, not when a buffer filled.
    PYTHONUNBUFFERED=1 nohup "$VENV" processing/streaming_gold.py --fresh \
        > >(stamp_lines >> "$STREAM_LOG") 2>&1 &
    STREAM_PID=$!
    echo "stream:$STREAM_PID" >> "$PID_FILE"
    info "  PID $STREAM_PID — waiting for READY signal (up to 120 s)..."

    # Wait for READY marker in log, after its "YYYY-MM-DD HH:MM:SS.mmm " stamp
    READY=0
    for i in $(seq 1 120); do
        sleep 1
        if grep -Eq '^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3} READY:' "$STREAM_LOG" 2>/dev/null; then
            READY=1
            break
        fi
        # Check process still alive
        kill -0 "$STREAM_PID" 2>/dev/null || die "streaming_gold.py died. Check $STREAM_LOG"
    done

    if [[ "$READY" -eq 0 ]]; then
        warn "READY not seen after 120 s — check $STREAM_LOG"
        warn "Attempting to start replayer anyway..."
    else
        ok "Streaming job READY."
    fi

    info "Starting replayer --speed 60 --start '2019-11-17 08:00:00' ..."
    info "  Log: $REPLAYER_LOG"
    PYTHONUNBUFFERED=1 nohup "$VENV" ingestion/replayer.py --speed 60 --start "2019-11-17 08:00:00" \
        > >(stamp_lines >> "$REPLAYER_LOG") 2>&1 &
    REPLAYER_PID=$!
    echo "replayer:$REPLAYER_PID" >> "$PID_FILE"

    ok "Replayer started (PID $REPLAYER_PID). Data flows at 60x speed."
    info "Stream log:    $STREAM_LOG"
    info "Replayer log:  $REPLAYER_LOG"
    info "Next step:     ./run_demo.sh app"
}

# ---------------------------------------------------------------------------
# app: API server + React dev server
# ---------------------------------------------------------------------------
cmd_app() {
    check_venv
    cd "$REPO_DIR"

    TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
    API_LOG="$LOG_DIR/api_${TIMESTAMP}.log"
    WEB_LOG="$LOG_DIR/web_${TIMESTAMP}.log"

    info "Starting FastAPI (uvicorn) on http://localhost:8000 ..."
    info "  Log: $API_LOG"
    nohup "$VENV" -m uvicorn serving.api.main:app --host 0.0.0.0 --port 8000 --reload \
        > "$API_LOG" 2>&1 &
    API_PID=$!
    echo "api:$API_PID" >> "$PID_FILE"

    # Wait for API to be ready (-f: a 404 or 500 does not count as up)
    API_UP=0
    for i in $(seq 1 30); do
        sleep 1
        if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
            API_UP=1
            break
        fi
        kill -0 "$API_PID" 2>/dev/null || die "uvicorn died. Check $API_LOG"
    done
    if [[ "$API_UP" -eq 1 ]]; then
        ok "API server running (PID $API_PID) — http://localhost:8000"
    else
        warn "API did not answer /health within 30 s — check $API_LOG"
    fi

    info "Starting React dev server on http://localhost:5173 ..."
    info "  Log: $WEB_LOG"
    cd web
    [[ -x node_modules/.bin/vite ]] || die "web/node_modules is missing. Run: cd web && npm ci"
    # vite directly, not `npm run dev` (whose "dev" script is just "vite"): npm runs
    # vite as a child, so `stop` killed npm and left vite holding :5173.
    nohup node_modules/.bin/vite > "$WEB_LOG" 2>&1 &
    WEB_PID=$!
    echo "web:$WEB_PID" >> "$PID_FILE"
    cd "$REPO_DIR"

    ok "Web server starting (PID $WEB_PID) — http://localhost:5173"
    info ""
    ok "=== ShopInsight is running ==="
    info "  API:  http://localhost:8000/docs"
    info "  UI:   http://localhost:5173"
    info "  Stop: ./run_demo.sh stop"
}

# ---------------------------------------------------------------------------
# stop: kill all demo background processes
# ---------------------------------------------------------------------------
cmd_stop() {
    if [[ ! -f "$PID_FILE" ]]; then
        warn "No PID file found at $PID_FILE. Nothing to stop."
        return
    fi

    while IFS=: read -r name pid; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" && ok "Stopped $name (PID $pid)"
        else
            warn "$name (PID $pid) already stopped."
        fi
    done < "$PID_FILE"

    rm -f "$PID_FILE"
    ok "All demo processes stopped."
}

# ---------------------------------------------------------------------------
# dispatch
# ---------------------------------------------------------------------------
COMMAND="${1:-help}"
case "$COMMAND" in
    infra)   cmd_infra  ;;
    stream)  cmd_stream ;;
    app)     cmd_app    ;;
    stop)    cmd_stop   ;;
    *)
        echo "ShopInsight Demo Launcher"
        echo ""
        echo "Usage: ./run_demo.sh <command>"
        echo ""
        echo "Commands:"
        echo "  infra   Start Docker, apply schemas (run once per machine reset)"
        echo "  stream  Start streaming_gold.py --fresh + replayer (run after infra)"
        echo "  app     Start API + React dev server (run after stream is READY)"
        echo "  stop    Stop all background demo processes"
        echo ""
        echo "Recommended order: infra → stream → app"
        ;;
esac
