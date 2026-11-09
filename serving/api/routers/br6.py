"""BR6 — Stockout Risk router.

Owner: Tin.

CONTRACT FROZEN — see docs/API_CONTRACT.md section 8.

Endpoint
--------
GET /api/br6/stockout
    Query parameters (all optional):
        warehouse_id : int    1-5  (default: all five warehouses)
        max_days     : float  > 0  only SKUs with days_to_stockout <= max_days
                                   (default: no filter)

Response shape
--------------
{
  "data": [
    {
      "warehouse_id":     2,
      "days_to_stockout": 1.0,     // 9999.0 = zero velocity, never null
      "product_id":       5770048,
      "stock_on_hand":    4,
      "velocity_7d":      4.0
    },
    ...
  ],
  "meta": { "ms": 9.4, "warehouse": "Cassandra", "partitions": 2, "rows": 3 }
}

Storage mapping: Cassandra -> stockout_risk
    PRIMARY KEY ((warehouse_id), days_to_stockout, product_id)
    One partition per warehouse, clustered by days_to_stockout ascending, so
    the most urgent SKUs sit at the head of each partition (SYSTEM_DESIGN
    section 6). Written by batch_gold.py from fact_inventory_daily.

Sentinel: days_to_stockout = 9999.0 means velocity_7d = 0 (no recent sales).
    Cassandra clustering columns cannot be null, so the projection substitutes
    9999.0 for the NULL that fact_inventory_daily stores. Any max_days below
    9999 therefore drops the SKUs that are not moving.

Semi-additive: stock_on_hand is a point-in-time snapshot. batch_gold.py
    deletes and rewrites each warehouse partition on every run, so the table
    holds exactly one snapshot. Summing stock_on_hand across warehouses is
    valid (total network stock); summing it across dates never is.
"""

from __future__ import annotations

import functools
import time

from fastapi import APIRouter, Query

from serving.api.cassandra import session
from serving.api.models import ApiResponse, QueryMeta, StockoutRow

router = APIRouter(prefix="/api/br6", tags=["BR6 — Stockout Risk"])

_LIMIT_PER_WAREHOUSE = 100


@functools.cache
def _select_with_max_days():
    return session().prepare(
        f"SELECT warehouse_id, days_to_stockout, product_id, stock_on_hand, velocity_7d "
        f"FROM stockout_risk WHERE warehouse_id = ? AND days_to_stockout <= ? LIMIT {_LIMIT_PER_WAREHOUSE}"
    )


@functools.cache
def _select_all_days():
    return session().prepare(
        f"SELECT warehouse_id, days_to_stockout, product_id, stock_on_hand, velocity_7d "
        f"FROM stockout_risk WHERE warehouse_id = ? LIMIT {_LIMIT_PER_WAREHOUSE}"
    )


@router.get(
    "/stockout",
    response_model=ApiResponse,
    summary="Stockout risk per SKU and warehouse",
    description=(
        "Returns SKUs ordered by days until stockout, most urgent first, for one "
        "warehouse or all five.  `days_to_stockout = 9999.0` means no sales in the "
        "last 7 days.  The table holds one snapshot: summing `stock_on_hand` across "
        "warehouses is valid, across dates never."
    ),
)
def get_stockout(
    warehouse_id: int | None = Query(
        None, ge=1, le=5, description="Warehouse 1-5; omit for all five"
    ),
    max_days: float | None = Query(
        None, gt=0, description="Only SKUs with days_to_stockout <= max_days; omit for all"
    ),
) -> ApiResponse:
    warehouses = [warehouse_id] if warehouse_id is not None else [1, 2, 3, 4, 5]
    all_rows = []
    started = time.perf_counter()

    if max_days is not None:
        stmt = _select_with_max_days()
        for wh in warehouses:
            rows = session().execute(stmt, (wh, float(max_days)))
            all_rows.extend(rows)
    else:
        stmt = _select_all_days()
        for wh in warehouses:
            rows = session().execute(stmt, (wh,))
            all_rows.extend(rows)

    # Sort merged rows: days_to_stockout ascending (most urgent first), then product_id
    all_rows.sort(key=lambda r: (r.days_to_stockout, r.product_id))
    elapsed_ms = (time.perf_counter() - started) * 1000

    data = [
        StockoutRow(
            warehouse_id=row.warehouse_id,
            days_to_stockout=round(float(row.days_to_stockout), 1),
            product_id=row.product_id,
            stock_on_hand=row.stock_on_hand,
            velocity_7d=round(float(row.velocity_7d), 2),
        )
        for row in all_rows
    ]

    return ApiResponse(
        data=data,
        meta=QueryMeta(
            ms=round(elapsed_ms, 2),
            warehouse="Cassandra",
            partitions=len(warehouses),
            rows=len(data),
        ),
    )
