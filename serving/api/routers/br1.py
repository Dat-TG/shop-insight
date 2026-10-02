"""BR1 — Real-time Operations router.

Owner: Dat.

CONTRACT FROZEN — see docs/API_CONTRACT.md section 3.

Endpoint
--------
GET /api/br1/realtime
    Query parameters (all optional):
        event_date  : str  e.g. "2019-11-17"  (default: today, Vietnam time)
        category_l1 : str  e.g. "electronics" (default: "all")

Reads Cassandra gmv_by_minute, written by processing/streaming_gold.py, with
one query on one partition, (event_date, category_l1). Rows are stored
window_start DESC, so the newest 120 minutes are the first 120 rows of the
partition: no sort, no scan. The screen charts the newest 60 minutes and
compares them with the 60 before.

category_l1 = "all" is a real partition, not a sum made here: the stream
writes a total row for every window (start_br1), so the default filter reads
one partition instead of 14.

The default date follows the contract, today in Vietnam time. On the 2019
data that is an empty 200. The screen always sends a date (2019-11-17, the
demo replay day).
"""

import functools
import time
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Query

from serving.api.cassandra import session
from serving.api.models import ApiResponse, GmvRow, QueryMeta

router = APIRouter(prefix="/api/br1", tags=["BR1 — Real-time Operations"])

VIETNAM = timezone(timedelta(hours=7))
# Two hours: 60 minutes on screen plus the 60 the "vs previous" card compares against.
MINUTES = 120


@functools.cache
def _select():
    """Prepared once, on the first request: Cassandra parses it once, not per call."""
    return session().prepare(
        "SELECT window_start, gmv, order_count FROM gmv_by_minute "
        f"WHERE event_date = ? AND category_l1 = ? LIMIT {MINUTES}"
    )


@router.get(
    "/realtime",
    response_model=ApiResponse,
    summary="GMV and order count per minute, last 120 minutes",
    description=(
        "One partition of `gmv_by_minute`, newest minute first. "
        '`category_l1="all"` is the stored total over every category.'
    ),
)
def get_realtime(
    event_date: date | None = Query(None, description="Date YYYY-MM-DD (default: today, Vietnam time)"),
    category_l1: str = Query("all", description='Top-level category or "all"'),
) -> ApiResponse:
    event_date = event_date or datetime.now(VIETNAM).date()
    statement = _select()  # connects on the first request; 503 if Cassandra is down

    started = time.perf_counter()
    rows = list(session().execute(statement, (event_date, category_l1)))
    elapsed_ms = (time.perf_counter() - started) * 1000

    # 120 rows is 120 minutes only where every minute had an event. A sparse
    # category (stationery: about 1,000 events in the month) would reach back
    # to the morning, so keep only the two hours before its newest minute.
    if rows:
        oldest = rows[0].window_start - timedelta(minutes=MINUTES)
        rows = [row for row in rows if row.window_start > oldest]

    # Cassandra holds the Vietnam wall clock labelled UTC (silver's convention,
    # docs/STREAMING_PATTERN.md Block 5), and the driver hands it back as a naive
    # datetime, whatever the laptop's time zone. So the offset is appended, never
    # converted.
    data = [
        GmvRow(
            event_date=event_date.isoformat(),
            category_l1=category_l1,
            window_start=row.window_start.strftime("%Y-%m-%dT%H:%M:%S") + "+07:00",
            gmv=float(row.gmv),
            order_count=row.order_count,
        )
        for row in rows
    ]
    return ApiResponse(
        data=data,
        meta=QueryMeta(ms=elapsed_ms, warehouse="Cassandra", partitions=1, rows=len(data)),
    )
