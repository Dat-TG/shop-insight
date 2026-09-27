"""BR2 — Conversion Funnel router.

Owner: Dat. W38 skeleton and fixture wiring: Tin.

CONTRACT FROZEN — see docs/API_CONTRACT.md.

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
      "step":             "view" | "cart" | "purchase",
      "count":            97489,
      "session_count":    67320,
      "conversion_rate":  1.0    // rate relative to first step (view)
    },
    ...
  ],
  "meta": {
    "ms":         18.3,
    "warehouse":  "Parquet",
    "partitions": 30,
    "rows":       3
  }
}

Storage mapping: Parquet -> data/gold/funnel_daily/
Gold columns:    event_date, category_l1, views, carts, purchases,
                 cr_view_to_cart, cr_cart_to_purchase

funnel_stage source values (fact_session_funnel):
    0 = session has no recorded events (not surfaced in API)
    1 = furthest milestone is view
    2 = furthest milestone is cart
    3 = furthest milestone is purchase (= conversion)

Now:  returns fixture data from web/fixtures/br2-funnel-daily.json -> "default",
      with meta.warehouse "Fixture" and partitions 0, because nothing was read
      from storage (docs/API_CONTRACT.md section 1.2). The fixture file itself
      carries the production meta shown above.
Next: replace _load_fixture() with DuckDB over data/gold/funnel_daily/, then
      set meta.warehouse to "Parquet" (API_CONTRACT section 2). Postgres never
      serves a screen (SYSTEM_DESIGN section 12).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query

from serving.api.models import ApiResponse, QueryMeta

router = APIRouter(prefix="/api/br2", tags=["BR2 — Conversion Funnel"])

# Path to the canonical fixture bundle (relative to the repository root).
_REPO = Path(__file__).resolve().parents[3]
_FIXTURE_PATH = _REPO / "web" / "fixtures" / "br2-funnel-daily.json"


def _load_fixture(empty: bool = False) -> list[dict[str, Any]]:
    """Return fixture data rows from the canonical bundle.

    Reads the "empty" scenario when empty=True, otherwise "default".
    Next: swap this function body for DuckDB over data/gold/funnel_daily/.
    """
    with open(_FIXTURE_PATH) as fh:
        bundle = json.load(fh)
    scenario = "empty" if empty else "default"
    return bundle[scenario]["data"]


@router.get(
    "/funnel",
    response_model=ApiResponse,
    summary="Conversion funnel: view → cart → purchase",
    description=(
        "Returns the three-step funnel aggregated over the requested date range "
        "and optional category filter.  Each row carries the raw event count, the "
        "session count, and the conversion rate relative to the view step.\n\n"
        "**Now**: returns fixture data (warehouse=Fixture, partitions=0).  "
        "**Next**: DuckDB over `data/gold/funnel_daily/`, then warehouse=Parquet."
    ),
)
def get_funnel(
    start_date: str = Query("2019-11-01", description="Inclusive start date YYYY-MM-DD"),
    end_date: str = Query("2019-11-30", description="Inclusive end date YYYY-MM-DD"),
    category_l1: str = Query("all", description='Top-level category or "all"'),
) -> ApiResponse:
    t0 = time.perf_counter()

    # Fixture for now.  Next: DuckDB over data/gold/funnel_daily/.
    data = _load_fixture(empty=False)

    elapsed_ms = (time.perf_counter() - t0) * 1000

    return ApiResponse(
        data=data,
        meta=QueryMeta(
            ms=round(elapsed_ms, 2),
            warehouse="Fixture",  # "Parquet" once DuckDB reads data/gold/funnel_daily/
            partitions=0,
            rows=len(data),
        ),
    )
