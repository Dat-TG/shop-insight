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

    Two reads per warehouse partition: the 100 most urgent SKUs (cluster
    order), then up to 5 SKUs with no sales (days_to_stockout = 9999.0), which
    sort last and would otherwise never make the first 100.  The second read is
    skipped when max_days is below 9999; a product the first read already
    returned is not repeated.  So at most 105 rows per warehouse.

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

QueryMeta: ms covers every read; partitions = warehouse partitions read (one
    per warehouse, though each is read twice); rows = rows returned.

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
_NO_SALES = 9999.0           # the days_to_stockout sentinel for velocity_7d = 0
_NO_SALES_PER_WAREHOUSE = 5  # no-sales SKUs shown per warehouse, after the urgent ones


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


@functools.cache
def _select_no_sales():
    return session().prepare(
        f"SELECT warehouse_id, days_to_stockout, product_id, stock_on_hand, velocity_7d "
        f"FROM stockout_risk WHERE warehouse_id = ? AND days_to_stockout >= {_NO_SALES} "
        f"LIMIT {_NO_SALES_PER_WAREHOUSE}"
    )


@router.get(
    "/stockout",
    response_model=ApiResponse,
    summary="Stockout risk per SKU and warehouse",
    description=(
        "Returns SKUs ordered by days until stockout, most urgent first, for one "
        "warehouse or all five: per warehouse the 100 most urgent, then up to 5 with "
        "no sales (`days_to_stockout = 9999.0`, no sales in the last 7 days), which "
        "a `max_days` below 9999 leaves out.  The table holds one snapshot: summing "
        "`stock_on_hand` across warehouses is valid, across dates never."
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

    with_no_sales = max_days is None or max_days >= _NO_SALES
    for wh in warehouses:
        if max_days is not None:
            urgent = list(session().execute(_select_with_max_days(), (wh, float(max_days))))
        else:
            urgent = list(session().execute(_select_all_days(), (wh,)))
        all_rows.extend(urgent)
        if with_no_sales:
            # The first read stops at 100 rows, and 9999.0 sorts last, so a warehouse
            # with 100 moving SKUs would never show one that is not moving.
            seen = {row.product_id for row in urgent}
            no_sales = session().execute(_select_no_sales(), (wh,))
            all_rows.extend(row for row in no_sales if row.product_id not in seen)

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
