"""BR2 — Conversion Funnel router.

Owner: Tin (W38 skeleton; W39 connects to star schema fact_session_funnel).

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
    {
      "step":                   "view" | "cart" | "purchase",
      "funnel_stage":           1 | 2 | 3,
      "count":                  97489,
      "session_count":          67320,
      "conversion_rate":        1.0,
      "avg_view_to_cart_sec":   null | 842.6,
      "avg_cart_to_purchase_sec": null | 1243.8,
      "abandoned_sessions":     0,
      "is_abandoned":           false | true
    },
    ...
  ],
  "meta": {
    "ms":         0.3,
    "warehouse":  "Postgres",
    "partitions": 30,
    "rows":       3
  }
}

Source (W39+):  fact_session_funnel
Required cols:  funnel_stage, view_to_cart_sec, cart_to_purchase_sec, is_abandoned

W38 status: returns fixture data from web/fixtures/br2-funnel-daily.json.
W40 plan:   replace _load_fixture() with Postgres query over fact_session_funnel.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query

from serving.api.models import ApiResponse, QueryMeta

router = APIRouter(prefix="/api/br2", tags=["BR2 — Conversion Funnel"])

# Path to the fixture file, relative to the repository root.
_REPO = Path(__file__).resolve().parents[3]
_FIXTURE = _REPO / "web" / "fixtures" / "br2-funnel-daily.json"


def _load_fixture(empty: bool = False) -> list[dict[str, Any]]:
    """Return fixture data rows.

    W39: source = fact_session_funnel (star schema).
    W40: replace this with a Postgres query:
        SELECT
            CASE funnel_stage
                WHEN 1 THEN 'view'
                WHEN 2 THEN 'cart'
                WHEN 3 THEN 'purchase'
            END                                     AS step,
            funnel_stage,
            COUNT(*)                                AS session_count,
            AVG(view_to_cart_sec)                   AS avg_view_to_cart_sec,
            AVG(cart_to_purchase_sec)               AS avg_cart_to_purchase_sec,
            COUNT(*) FILTER (WHERE is_abandoned)    AS abandoned_sessions,
            BOOL_OR(is_abandoned)                   AS is_abandoned
        FROM fact_session_funnel
        WHERE session_date BETWEEN :start_date AND :end_date
        GROUP BY funnel_stage
        ORDER BY funnel_stage
    """
    with open(_FIXTURE) as fh:
        payload = json.load(fh)
    key = "empty" if empty else "default"
    return payload[key]["data"]


@router.get(
    "/funnel",
    response_model=ApiResponse,
    summary="Conversion funnel: view → cart → purchase (fact_session_funnel)",
    description=(
        "Returns the three-step funnel aggregated over the requested date range "
        "and optional category filter. Each row carries the raw event count, the "
        "session count, conversion rate, timing between stages, and abandonment "
        "flag.\n\n"
        "**Source (W39+)**: `fact_session_funnel`  \n"
        "**Required columns**: `funnel_stage`, `view_to_cart_sec`, "
        "`cart_to_purchase_sec`, `is_abandoned`  \n\n"
        "**W38**: returns fixture data.  \n"
        "**W40**: will query `fact_session_funnel` in Postgres."
    ),
)
def get_funnel(
    start_date: str = Query("2019-11-01", description="Inclusive start date YYYY-MM-DD"),
    end_date: str = Query("2019-11-30", description="Inclusive end date YYYY-MM-DD"),
    category_l1: str = Query("all", description='Top-level category or "all"'),
) -> ApiResponse:
    t0 = time.perf_counter()

    # W38/W39 fixture. W40: replace with fact_session_funnel Postgres query.
    data = _load_fixture(empty=False)

    elapsed_ms = (time.perf_counter() - t0) * 1000

    return ApiResponse(
        data=data,
        meta=QueryMeta(
            ms=round(elapsed_ms, 2),
            warehouse="Postgres",
            partitions=30,
            rows=len(data),
        ),
    )
