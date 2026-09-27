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

Now:  returns fixture data from web/fixtures/br6-stockout-risk.json -> "default",
      with meta.warehouse "Fixture" and partitions 0, because nothing was read
      from storage (docs/API_CONTRACT.md section 1.2). The fixture file itself
      carries the production meta shown above.
Next: replace _load_fixture() with cassandra-driver, one query per warehouse:
          SELECT warehouse_id, days_to_stockout, product_id,
                 stock_on_hand, velocity_7d
          FROM stockout_risk
          WHERE warehouse_id = ? [AND days_to_stockout <= ?]
      warehouse_id given -> one query; omitted -> five. meta.partitions is the
      number of warehouses queried. Merge the results by days_to_stockout
      ascending and set meta.warehouse to "Cassandra".
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query

from serving.api.models import ApiResponse, QueryMeta

router = APIRouter(prefix="/api/br6", tags=["BR6 — Stockout Risk"])

# Path to the canonical fixture bundle (relative to the repository root).
_REPO = Path(__file__).resolve().parents[3]
_FIXTURE_PATH = _REPO / "web" / "fixtures" / "br6-stockout-risk.json"


def _load_fixture(empty: bool = False) -> list[dict[str, Any]]:
    """Return fixture data rows from the canonical bundle.

    Reads the "empty" scenario when empty=True, otherwise "default".
    Next: swap this function body for one cassandra-driver query per warehouse.
    """
    with open(_FIXTURE_PATH) as fh:
        bundle = json.load(fh)
    scenario = "empty" if empty else "default"
    return bundle[scenario]["data"]


@router.get(
    "/stockout",
    response_model=ApiResponse,
    summary="Stockout risk per SKU and warehouse",
    description=(
        "Returns SKUs ordered by days until stockout, most urgent first, for one "
        "warehouse or all five.  `days_to_stockout = 9999.0` means no sales in the "
        "last 7 days.  The table holds one snapshot: summing `stock_on_hand` across "
        "warehouses is valid, across dates never.\n\n"
        "**Now**: returns fixture data (warehouse=Fixture, partitions=0).  "
        "**Next**: one Cassandra query per warehouse on `stockout_risk`, then "
        "warehouse=Cassandra."
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

    # Fixture for now.  Next: one query per warehouse on stockout_risk.
    data = _load_fixture(empty=False)

    elapsed_ms = (time.perf_counter() - t0) * 1000

    return ApiResponse(
        data=data,
        meta=QueryMeta(
            ms=round(elapsed_ms, 2),
            warehouse="Fixture",  # "Cassandra" once the driver reads stockout_risk
            partitions=0,
            rows=len(data),
        ),
    )
