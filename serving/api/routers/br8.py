"""BR8 — Order Velocity Alerts router.

Owner: Tin.

CONTRACT FROZEN — see docs/API_CONTRACT.md section 10.

Endpoint
--------
GET /api/br8/alerts
    Query parameters (all optional):
        event_date : str  e.g. "2019-11-17"  (default: latest date in table)
        severity   : str  "low" | "medium" | "high" | "all"  (default: "all")

Reads Cassandra order_velocity_alerts, written by processing/streaming_gold.py
start_br8(). One partition per event_date, clustered window_start DESC so the
newest windows are at the head — no sort step. Severity filter applied in Python
after fetching (not CQL ALLOW FILTERING) to keep the query a clean partition read.

The table key: PRIMARY KEY ((event_date), window_start, user_id)
CLUSTERING ORDER BY (window_start DESC, user_id ASC)
"""

import functools
import json
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Query

from serving.api.cassandra import session
from serving.api.models import ApiResponse, QueryMeta, VelocityAlertRow

router = APIRouter(prefix="/api/br8", tags=["BR8 — Order Velocity Alerts"])

VIETNAM = timezone(timedelta(hours=7))
# Maximum rows fetched per request. A full day at demo speed (60x) produces at
# most a few thousand (window, user) pairs; 5000 covers any realistic day.
_LIMIT = 5000
_SEVERITY_VALUES = {"low", "medium", "high", "all"}
_REPO = Path(__file__).resolve().parents[3]
_FIXTURE_PATH = _REPO / "web" / "fixtures" / "br8-order-velocity-alerts.json"


@functools.cache
def _select():
    """Prepared once on the first request: Cassandra parses it once, not per call."""
    return session().prepare(
        f"SELECT event_date, window_start, user_id, order_count, total_value, severity "
        f"FROM order_velocity_alerts WHERE event_date = ? LIMIT {_LIMIT}"
    )


def _latest_date() -> date:
    """Scan the first partition key to find the most recent event_date in the table.

    Called only when event_date is omitted. Falls back to today (Vietnam time) if
    the table is empty — which gives an empty 200, matching the contract.
    """
    try:
        # system_schema.columns doesn't help here; we need the actual data.
        # A token-range scan of one token range would be expensive; instead, let
        # the caller pass a date whenever possible. This path fires only for the
        # default case in a browser that hasn't set event_date.
        rows = list(session().execute(
            "SELECT DISTINCT event_date FROM order_velocity_alerts LIMIT 30"
        ))
        if rows:
            return max(row.event_date for row in rows)
    except Exception:
        pass
    return datetime.now(VIETNAM).date()


@router.get(
    "/alerts",
    response_model=ApiResponse,
    summary="Order velocity alerts — unusual purchase bursts per user",
    description=(
        "One partition of `order_velocity_alerts`, newest window first. "
        "Rows are pre-sorted `window_start DESC, user_id ASC` by Cassandra. "
        "`severity` values: `low` (1 order), `medium` (2–3), `high` (≥4). "
        "Omit `event_date` to get the latest date available in the table."
    ),
)
def get_alerts(
    event_date: date | None = Query(None, description="Date YYYY-MM-DD (default: latest in table)"),
    severity: str = Query("all", description='"low" | "medium" | "high" | "all"'),
) -> ApiResponse:
    if severity not in _SEVERITY_VALUES:
        severity = "all"
    event_date = event_date or _latest_date()

    statement = _select()
    started = time.perf_counter()
    raw = list(session().execute(statement, (event_date,)))
    elapsed_ms = (time.perf_counter() - started) * 1000

    if severity != "all":
        raw = [row for row in raw if row.severity == severity]

    data = [
        VelocityAlertRow(
            event_date=event_date.isoformat(),
            window_start=row.window_start.strftime("%Y-%m-%dT%H:%M:%S") + "+07:00",
            user_id=row.user_id,
            order_count=row.order_count,
            total_value=float(row.total_value),
            severity=row.severity,
        )
        for row in raw
    ]
    return ApiResponse(
        data=data,
        meta=QueryMeta(ms=round(elapsed_ms, 2), warehouse="Cassandra", partitions=1, rows=len(data)),
    )
