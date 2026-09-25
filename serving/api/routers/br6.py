"""BR6 — Stockout Risk router.

Owner: Tin (W39: connects to star schema fact_inventory_daily).

Endpoint
--------
GET /api/br6/stockout
    Query parameters (all optional):
        inventory_date : str  e.g. "2019-11-30"  (default: "2019-11-30")
        warehouse_id   : int  1–5 or 0 for all   (default: 0)
        max_days       : float max days_to_stockout to include (default: 30)

Response shape
--------------
{
  "data": [
    {
      "warehouse_id":    1,
      "inventory_date":  "2019-11-30",
      "product_id":      1005115,
      "stock_on_hand":   3,
      "velocity_7d":     2.0,
      "days_to_stockout": 1.5,
      "reorder_point":   14,
      "is_below_reorder": true
    },
    ...
  ],
  "meta": { "ms": 9.4, "warehouse": "Postgres", "partitions": 2, "rows": 6 }
}

Source (W39+):  fact_inventory_daily
Required cols:  days_to_stockout, is_below_reorder

⚠️ SEMI-ADDITIVE WARNINGS (must be enforced in every implementation):
  1. This endpoint MUST filter on exactly ONE inventory_date. Do not leave the
     date filter open or accept date ranges — summing stock across dates
     double-counts (a product with 10 units on day 1 and 10 units on day 2
     is NOT 20 units; it is still 10).
  2. SUM(stock_on_hand) across warehouse_id on the SAME date is valid and
     represents total network stock for a given SKU on that day.
  3. Never SUM(stock_on_hand) across multiple dates.

W38 status: returns empty data.
W39: update to return fixture data from web/fixtures/br6-stockout-risk.json.
W40 plan:   replace _load_fixture() with Postgres query over fact_inventory_daily.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query

from serving.api.models import ApiResponse, QueryMeta

router = APIRouter(prefix="/api/br6", tags=["BR6 — Stockout Risk"])

_REPO = Path(__file__).resolve().parents[3]
_FIXTURE = _REPO / "web" / "fixtures" / "br6-stockout-risk.json"


def _load_fixture(empty: bool = False) -> list[dict[str, Any]]:
    """Return fixture data rows.

    W39: source = fact_inventory_daily (star schema, LIST-partitioned by warehouse_id).
    W40: replace this with a Postgres query:
        SELECT
            f.warehouse_id,
            f.inventory_date,
            f.product_id,
            f.stock_on_hand,
            f.velocity_7d,
            f.days_to_stockout,
            f.reorder_point,
            f.is_below_reorder
        FROM fact_inventory_daily f
        WHERE f.inventory_date = :inventory_date    -- EXACTLY ONE DATE: semi-additive!
          AND (:warehouse_id = 0 OR f.warehouse_id = :warehouse_id)
          AND f.days_to_stockout <= :max_days
        ORDER BY f.days_to_stockout ASC, f.warehouse_id
        -- To get total network stock per SKU on one date:
        -- SELECT product_id, SUM(stock_on_hand) FROM fact_inventory_daily
        -- WHERE inventory_date = :inventory_date  GROUP BY product_id
        -- (SUM across warehouses on ONE date is valid)
    """
    with open(_FIXTURE) as fh:
        payload = json.load(fh)
    key = "empty" if empty else "default"
    return payload[key]["data"]


@router.get(
    "/stockout",
    response_model=ApiResponse,
    summary="Stockout risk per SKU/warehouse (fact_inventory_daily)",
    description=(
        "Returns inventory snapshot with stockout risk metrics.  \n\n"
        "**Source (W39+)**: `fact_inventory_daily`  \n"
        "**Required columns**: `days_to_stockout`, `is_below_reorder`  \n\n"
        "⚠️ **Semi-additive constraint**: Always filter on **exactly one** "
        "`inventory_date`. Stock on hand is a point-in-time snapshot — summing "
        "across multiple dates produces meaningless double-counts.  \n\n"
        "✅ **Summing across warehouses on the same date is valid** — this gives "
        "total network stock for a SKU on that day.  \n\n"
        "**W38**: returns empty data.  \n"
        "**W39**: returns fixture data.  \n"
        "**W40**: will query `fact_inventory_daily` in Postgres."
    ),
)
def get_stockout(
    inventory_date: str = Query(
        "2019-11-30",
        description="Snapshot date YYYY-MM-DD. EXACTLY ONE DATE — semi-additive column."
    ),
    warehouse_id: int = Query(0, ge=0, le=5, description="Warehouse 1-5 or 0 for all"),
    max_days: float = Query(30.0, gt=0, description="Max days_to_stockout (< 9999 excludes no-movement SKUs)"),
) -> ApiResponse:
    t0 = time.perf_counter()

    # W39: fixture. W40: replace with fact_inventory_daily Postgres query.
    # ENFORCE: filter on exactly ONE inventory_date. Never range.
    data = _load_fixture(empty=False)

    elapsed_ms = (time.perf_counter() - t0) * 1000

    return ApiResponse(
        data=data,
        meta=QueryMeta(
            ms=round(elapsed_ms, 2),
            warehouse="Postgres",
            partitions=2,
            rows=len(data),
        ),
    )
