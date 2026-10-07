"""BR2 — Conversion Funnel router.

Owner: Dat. W38 skeleton and fixture wiring: Tin.

CONTRACT FROZEN — see docs/API_CONTRACT.md section 4.

Endpoint
--------
GET /api/br2/funnel
    Query parameters (all optional):
        start_date  : str  e.g. "2019-11-01"  (default: "2019-11-01")
        end_date    : str  e.g. "2019-11-30"  (default: "2019-11-30")
        category_l1 : str  e.g. "electronics" (default: "all")

Response shape
--------------
{
  "data": [
    { "step": "view",     "count": 4451411, "session_count": 966143, "conversion_rate": 1.0 },
    { "step": "cart",     "count": 213486,  "session_count": 131498, "conversion_rate": 0.1361 },
    { "step": "purchase", "count": 64883,   "session_count": 54676,  "conversion_rate": 0.0566 }
  ],
  "meta": { "ms": 16.1, "warehouse": "Parquet", "partitions": 30, "rows": 3 }
}

Storage mapping: Parquet -> data/gold/funnel_daily/event_date=YYYY-MM-DD/
Gold columns:    event_date, category_l1, views, carts, purchases,
                 cr_view_to_cart, cr_cart_to_purchase,
                 view_events, cart_events, purchase_events

batch_gold.py builds funnel_daily from fact_session_funnel. event_date is the
day the session started, in Vietnam time. views/carts/purchases count sessions
whose funnel_stage reached the step (>= 1, >= 2, = 3); the *_events columns
count raw events. category_l1 = "all" is a stored row, not a sum of the
categories, because a session that touches two categories counts in both.

For a date range the router SUMS the counts over the days and recomputes the
rates from the sums. It never averages cr_view_to_cart or cr_cart_to_purchase:
the mean of daily rates is not the rate of the range.

    count           = *_events          (raw events at the step)
    session_count   = views/carts/purchases
    conversion_rate = session_count / view session_count, view = 1.0

partitions is the number of event_date directories read. A malformed date,
start_date after end_date, a range outside the data, or an unknown category
returns HTTP 200 with data=[] (API_CONTRACT section 1.3).
"""

from __future__ import annotations

import time
from datetime import date
from pathlib import Path

import duckdb
from fastapi import APIRouter, Query

from serving.api.models import ApiResponse, QueryMeta

router = APIRouter(prefix="/api/br2", tags=["BR2 — Conversion Funnel"])

_REPO = Path(__file__).resolve().parents[3]
_GOLD_DIR = _REPO / "data" / "gold" / "funnel_daily"
# Rates are recomputed from the summed counts below; cr_* is never averaged.
_QUERY = """
    SELECT sum(views) AS views, sum(carts) AS carts, sum(purchases) AS purchases,
           sum(view_events) AS view_events, sum(cart_events) AS cart_events,
           sum(purchase_events) AS purchase_events
    FROM read_parquet($files)
    WHERE category_l1 = $category_l1
"""


def _partitions(start_date: str, end_date: str) -> list[Path]:
    """The event_date directories inside [start_date, end_date], or [] for bad input."""
    try:
        start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
    except ValueError:
        return []
    return [
        path
        for path in sorted(_GOLD_DIR.glob("event_date=*"))
        if start <= date.fromisoformat(path.name.removeprefix("event_date=")) <= end
    ]


def _read_funnel(partitions: list[Path], category_l1: str) -> list[dict[str, object]]:
    files = [str(path / "*.parquet") for path in partitions]
    with duckdb.connect() as con:
        cursor = con.execute(_QUERY, {"files": files, "category_l1": category_l1})
        columns = [column[0] for column in cursor.description]
        sums = dict(zip(columns, cursor.fetchone()))
    views = sums["views"]
    if not views:  # no row matched: an unknown category
        return []
    steps = [
        ("view", "view_events", "views"),
        ("cart", "cart_events", "carts"),
        ("purchase", "purchase_events", "purchases"),
    ]
    return [
        {
            "step": step,
            "count": sums[events],
            "session_count": sums[sessions],
            "conversion_rate": round(sums[sessions] / views, 4),
        }
        for step, events, sessions in steps
    ]


@router.get(
    "/funnel",
    response_model=ApiResponse,
    summary="Conversion funnel: view → cart → purchase",
    description=(
        "Returns the three-step funnel aggregated over the requested date range "
        "and optional category filter.  Each row carries the raw event count, the "
        "number of sessions that reached the step, and the session conversion rate "
        "relative to the view step.\n\n"
        "Reads `data/gold/funnel_daily/` with DuckDB (warehouse=Parquet)."
    ),
)
def get_funnel(
    start_date: str = Query("2019-11-01", description="Inclusive start date YYYY-MM-DD"),
    end_date: str = Query("2019-11-30", description="Inclusive end date YYYY-MM-DD"),
    category_l1: str = Query("all", description='Top-level category or "all"'),
) -> ApiResponse:
    t0 = time.perf_counter()

    partitions = _partitions(start_date, end_date)
    data = _read_funnel(partitions, category_l1) if partitions else []  # read_parquet([]) raises

    elapsed_ms = (time.perf_counter() - t0) * 1000

    return ApiResponse(
        data=data,
        meta=QueryMeta(
            ms=round(elapsed_ms, 2),
            warehouse="Parquet",
            partitions=len(partitions),
            rows=len(data),
        ),
    )
