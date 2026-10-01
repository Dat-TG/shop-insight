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

Fallback: if Cassandra is unreachable (NoHostAvailable / HTTPException 503),
    FastAPI's exception handler in serving/api/main.py returns HTTP 503 before
    this function runs. The fixture-based fallback is retained for development
    convenience when the keyspace is absent (USE_FIXTURE=true in .env).
"""

from __future__ import annotations

import functools
import json
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query
from cassandra.cluster import NoHostAvailable

from serving.api.cassandra import session
from serving.api.models import ApiResponse, QueryMeta, StockoutRow

router = APIRouter(prefix="/api/br6", tags=["BR6 — Stockout Risk"])

# Path to the canonical fixture bundle (relative to the repository root).
_REPO = Path(__file__).resolve().parents[3]
_FIXTURE_PATH = _REPO / "web" / "fixtures" / "br6-stockout-risk.json"

# All five warehouse ids, matching DIM_WAREHOUSE_ROWS in load_star_postgres.py.
_ALL_WAREHOUSE_IDS = [1, 2, 3, 4, 5]


def _load_fixture(empty: bool = False) -> list[dict[str, Any]]:
    """Return fixture data rows from the canonical bundle (dev fallback)."""
    with open(_FIXTURE_PATH) as fh:
        bundle = json.load(fh)
    scenario = "empty" if empty else "default"
    return bundle[scenario]["data"]


@functools.cache
def _select_by_warehouse():
    """Prepared statement: all rows in one warehouse partition, most urgent first.

    Prepared once on the first request; the driver parses it once, not per call.
    Clustering order is ASC on days_to_stockout, so the most urgent SKUs are
    already at the front of the partition (no ORDER BY needed in the query).
    """
    return session().prepare(
        "SELECT warehouse_id, days_to_stockout, product_id, stock_on_hand, velocity_7d "
        "FROM stockout_risk "
        "WHERE warehouse_id = ?"
    )


@functools.cache
def _select_by_warehouse_with_max():
    """Prepared statement: rows in one warehouse with days_to_stockout <= max_days."""
    return session().prepare(
        "SELECT warehouse_id, days_to_stockout, product_id, stock_on_hand, velocity_7d "
        "FROM stockout_risk "
        "WHERE warehouse_id = ? AND days_to_stockout <= ?"
    )


def _query_warehouse(wh_id: int, max_days: float | None) -> list:
    """Execute one Cassandra query for a single warehouse partition."""
    if max_days is not None:
        stmt = _select_by_warehouse_with_max()
        return list(session().execute(stmt, (wh_id, max_days)))
    else:
        stmt = _select_by_warehouse()
        return list(session().execute(stmt, (wh_id,)))


@router.get(
    "/stockout",
    response_model=ApiResponse,
    summary="Stockout risk per SKU and warehouse",
    description=(
        "Returns SKUs ordered by days until stockout, most urgent first, for one "
        "warehouse or all five.  `days_to_stockout = 9999.0` means no sales in the "
        "last 7 days.  The table holds one snapshot: summing `stock_on_hand` across "
        "warehouses is valid, across dates never.\n\n"
        "**Storage**: Cassandra `stockout_risk`, written by `batch_gold.py`. "
        "Falls back to fixture data when Cassandra is unavailable."
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
    t0 = time.perf_counter()

    # Determine which warehouses to query.
    warehouse_ids = [warehouse_id] if warehouse_id is not None else _ALL_WAREHOUSE_IDS

    try:
        # One Cassandra query per warehouse (one partition key per query).
        all_rows: list[Any] = []
        for wh_id in warehouse_ids:
            all_rows.extend(_query_warehouse(wh_id, max_days))

        elapsed_ms = (time.perf_counter() - t0) * 1000

        # Merge and sort: most urgent (lowest days_to_stockout) first.
        all_rows.sort(key=lambda r: (r.days_to_stockout, r.warehouse_id))

        data = [
            StockoutRow(
                warehouse_id=row.warehouse_id,
                days_to_stockout=float(row.days_to_stockout),
                product_id=row.product_id,
                stock_on_hand=row.stock_on_hand,
                velocity_7d=float(row.velocity_7d),
            )
            for row in all_rows
        ]
        return ApiResponse(
            data=data,
            meta=QueryMeta(
                ms=round(elapsed_ms, 2),
                warehouse="Cassandra",
                partitions=len(warehouse_ids),
                rows=len(data),
            ),
        )

    except (NoHostAvailable, Exception) as exc:
        # Fall back to fixture data if Cassandra is down.
        # In production this should 503; during development the fixture keeps
        # the React screen alive without Docker. Log the failure for visibility.
        import logging
        logging.getLogger(__name__).warning("BR6 Cassandra unavailable, using fixture: %s", exc)

        elapsed_ms = (time.perf_counter() - t0) * 1000
        raw = _load_fixture(empty=False)

        # Apply warehouse_id and max_days filters on the fixture too.
        if warehouse_id is not None:
            raw = [r for r in raw if r.get("warehouse_id") == warehouse_id]
        if max_days is not None:
            raw = [r for r in raw if r.get("days_to_stockout", 9999.0) <= max_days]

        return ApiResponse(
            data=raw,
            meta=QueryMeta(
                ms=round(elapsed_ms, 2),
                warehouse="Fixture",
                partitions=0,
                rows=len(raw),
            ),
        )
