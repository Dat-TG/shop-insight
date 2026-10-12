"""BR5 — Abandoned Carts router.

Owner: Nguyen.

CONTRACT FROZEN — see docs/API_CONTRACT.md section 7.

Endpoint
--------
GET /api/br5/carts
    Query parameters (all optional):
        event_date : str    e.g. "2019-11-17"  (default: the latest date in the table)
        min_value  : float  e.g. 100           (default: 0)

Reads Cassandra abandoned_carts, written by processing/streaming_gold.py
(start_br5), with one query on one partition, (event_date). The key is
((event_date), user_session): cart_value is a plain column, which is what makes
the stream's upsert idempotent, so Cassandra cannot order by it. This endpoint
reads the day's whole partition and sorts by cart_value DESC itself. Measured on
silver with the stream's 30-minute rule: at most 3,965 carts for the demo replay
(17 Nov from 15:00), 8,774 for all of 17 Nov, about 18,300 on 15 Nov, the
busiest day.

Without event_date the latest date is found by listing the partition keys. That
is one extra query over a handful of keys, and it is counted in meta.partitions.
"""

import functools
import time
from datetime import date

from fastapi import APIRouter, Query

from serving.api.cassandra import session
from serving.api.models import AbandonedCartRow, ApiResponse, QueryMeta

router = APIRouter(prefix="/api/br5", tags=["BR5 — Abandoned Carts"])


@functools.cache
def _select():
    """Prepared once, on the first request: Cassandra parses it once, not per call."""
    return session().prepare(
        "SELECT user_session, cart_value, user_id, item_count, last_event_at "
        "FROM abandoned_carts WHERE event_date = ?"
    )


@router.get(
    "/carts",
    response_model=ApiResponse,
    summary="Abandoned carts of one day, highest value first",
    description=(
        "One partition of `abandoned_carts`, sorted by `cart_value` descending in the API "
        "(the table key has no `cart_value`). Without `event_date`: the latest date."
    ),
)
def get_carts(
    event_date: date | None = Query(None, description="Date YYYY-MM-DD (default: latest date)"),
    min_value: float = Query(0, ge=0, description="Minimum cart value"),
) -> ApiResponse:
    statement = _select()  # connects on the first request; 503 if Cassandra is down

    started = time.perf_counter()
    partitions = 1
    if event_date is None:
        days = [row.event_date.date() for row in session().execute("SELECT DISTINCT event_date FROM abandoned_carts")]
        partitions = len(days) + 1
        if not days:
            return ApiResponse(
                data=[],
                meta=QueryMeta(ms=(time.perf_counter() - started) * 1000,
                               warehouse="Cassandra", partitions=0, rows=0),
            )
        event_date = max(days)
    rows = list(session().execute(statement, (event_date,)))
    elapsed_ms = (time.perf_counter() - started) * 1000

    # Cassandra holds the Vietnam wall clock labelled UTC (silver's convention,
    # docs/STREAMING_PATTERN.md Block 5), handed back as a naive datetime. So the
    # offset is appended, never converted.
    data = [
        AbandonedCartRow(
            event_date=event_date.isoformat(),
            user_session=row.user_session,
            cart_value=float(row.cart_value),
            user_id=row.user_id,
            item_count=row.item_count,
            last_event_at=row.last_event_at.strftime("%Y-%m-%dT%H:%M:%S") + "+07:00",
        )
        for row in rows
        if float(row.cart_value) >= min_value
    ]
    data.sort(key=lambda cart: cart.cart_value, reverse=True)
    return ApiResponse(
        data=data,
        meta=QueryMeta(ms=elapsed_ms, warehouse="Cassandra", partitions=partitions, rows=len(data)),
    )
