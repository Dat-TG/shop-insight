"""BR3 — Trending Products router.

Owner: Khang.

CONTRACT FROZEN — see docs/API_CONTRACT.md section 5.

Endpoint
--------
GET /api/br3/trending
    Query parameter (optional):
        window_start : ISO 8601, e.g. "2019-11-17T15:00:00+07:00"
                       (default: the newest window). Without an offset it is
                       read as Vietnam time.

Reads Cassandra trending_products, written by start_br3 in
processing/streaming_gold.py. One window is one partition and its rows are
stored by rank, so a window's top 20 is one partition read with no sort.

"Which window is the newest" is not a question the key can answer. Cassandra
orders rows inside a partition, never partitions against each other. So
without window_start the endpoint first lists the partition keys (SELECT
DISTINCT window_start reads keys, no rows) and takes the largest.
meta.partitions counts that scan as well: one per window written since the
last --fresh, plus the partition read. The screen draws its arrows from the
window one minute earlier and asks for it by window_start, so that call reads
one partition.
"""

import functools
import time
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query

from serving.api.cassandra import session
from serving.api.models import ApiResponse, QueryMeta, TrendingProductRow

router = APIRouter(prefix="/api/br3", tags=["BR3 — Trending Products"])

VIETNAM = timezone(timedelta(hours=7))


@functools.cache
def _windows():
    """Prepared once, on the first request: Cassandra parses it once, not per call."""
    return session().prepare("SELECT DISTINCT window_start FROM trending_products")


@functools.cache
def _select():
    return session().prepare(
        "SELECT window_start, rank, product_id, brand, category_l1, view_count, cart_count "
        "FROM trending_products WHERE window_start = ?"
    )


@router.get(
    "/trending",
    response_model=ApiResponse,
    summary="Top 20 products by views in one 15-minute window",
    description=(
        "One partition of `trending_products`, rank 1 first. Without `window_start`, "
        "the newest window, found by listing the partition keys first."
    ),
)
def get_trending(
    window_start: datetime | None = Query(
        None, description='ISO 8601, e.g. "2019-11-17T15:00:00+07:00" (default: the newest window)'
    ),
) -> ApiResponse:
    # Both prepared before the clock starts: connects on the first request, 503 if Cassandra is down.
    list_windows, select = _windows(), _select()

    started = time.perf_counter()
    partitions = 0
    if window_start is None:
        keys = list(session().execute(list_windows))
        partitions = len(keys)
        window_start = max((row.window_start for row in keys), default=None)
    elif window_start.tzinfo is not None:
        # Cassandra holds the Vietnam wall clock labelled UTC (silver's
        # convention, docs/STREAMING_PATTERN.md Block 5), so a time with an
        # offset is moved to Vietnam time and the offset dropped.
        window_start = window_start.astimezone(VIETNAM).replace(tzinfo=None)
    rows = []
    if window_start is not None:
        rows = list(session().execute(select, (window_start,)))
        partitions += 1
    elapsed_ms = (time.perf_counter() - started) * 1000

    data = [
        TrendingProductRow(
            window_start=row.window_start.strftime("%Y-%m-%dT%H:%M:%S") + "+07:00",
            rank=row.rank,
            product_id=row.product_id,
            brand=row.brand,
            category_l1=row.category_l1,
            view_count=row.view_count,
            cart_count=row.cart_count,
        )
        for row in rows
    ]
    return ApiResponse(
        data=data,
        meta=QueryMeta(ms=elapsed_ms, warehouse="Cassandra", partitions=partitions, rows=len(data)),
    )
