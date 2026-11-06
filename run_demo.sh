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
# Logs:     logs/stream_YYYYMMDD_HHMMSS.log, logs/api_YYYYMMDD_HHMMSS.log

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$REPO_DIR/.venv/bin/python"
LOG_DIR="$REPO_DIR/logs"
PID_FILE="$LOG_DIR/.demo_pids"

export JAVA_HOME="${JAVA_HOME:-/Library/Java/JavaVirtualMachines/jdk-21.jdk/Contents/Home}"
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

    info "Applying Postgres DDL..."
    docker compose exec -T postgres psql -U shopinsight -d shopinsight \
        -v ON_ERROR_STOP=1 < warehouse/ddl.sql
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
    nohup "$VENV" processing/streaming_gold.py --fresh \
        > "$STREAM_LOG" 2>&1 &
    STREAM_PID=$!
    echo "stream:$STREAM_PID" >> "$PID_FILE"
    info "  PID $STREAM_PID — waiting for READY signal (up to 120 s)..."

    # Wait for READY marker in log
    READY=0
    for i in $(seq 1 120); do
        sleep 1
        if grep -q "^READY:" "$STREAM_LOG" 2>/dev/null; then
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
    nohup "$VENV" ingestion/replayer.py --speed 60 --start "2019-11-17 08:00:00" \
        > "$REPLAYER_LOG" 2>&1 &
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

    # Wait for API to be ready
    for i in $(seq 1 30); do
        sleep 1
        curl -s http://localhost:8000/healthz > /dev/null 2>&1 && break
        kill -0 "$API_PID" 2>/dev/null || die "uvicorn died. Check $API_LOG"
    done
    ok "API server running (PID $API_PID) — http://localhost:8000"

    info "Starting React dev server on http://localhost:5173 ..."
    info "  Log: $WEB_LOG"
    cd web
    nohup npm run dev > "$WEB_LOG" 2>&1 &
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
