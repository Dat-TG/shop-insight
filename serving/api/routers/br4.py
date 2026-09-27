"""BR4 — RFM Customer Segmentation router.

Owner: Khang. Fixture wiring: Tin.

CONTRACT FROZEN — see docs/API_CONTRACT.md section 6.

Endpoint
--------
GET /api/br4/segments
    Query parameters (all optional):
        snapshot_date : str  e.g. "2019-11-30"  (default: "2019-11-30")
        segment       : str  e.g. "champion"     (default: "all")
        r_score       : int  1-5                 (default: no filter)
        f_score       : int  1-5                 (default: no filter)
        m_score       : int  1-5                 (default: no filter)

Response shape
--------------
{
  "data": [
    {
      "user_id":       541312140,
      "snapshot_date": "2019-11-30",
      "recency_days":  1,          // null if never purchased
      "frequency":     48,
      "monetary":      22480.50,
      "r_score":       5,          // null if never purchased
      "f_score":       5,          // null if never purchased
      "m_score":       5,          // null if never purchased
      "rfm_cell":      "555",      // null if never purchased
      "segment":       "champion"
    },
    ...
  ],
  "meta": { "ms": 24.6, "warehouse": "Parquet", "partitions": 1, "rows": 2 }
}

Storage mapping: Parquet -> data/gold/rfm_segments/snapshot_date=2019-11-30/
Gold columns:    user_id, recency_days, frequency, monetary,
                 r_score, f_score, m_score, segment
                 (rfm_cell is in the response but not a gold column yet)

batch_gold.py projects rfm_segments from dim_user WHERE is_current
(SYSTEM_DESIGN section 7), so this endpoint never sees an SCD2 history row
and never filters on is_current itself.

Nullable handling: send null, never 0. About 88% of users at the first
snapshot have never purchased and have null scores.

Now:  returns fixture data from web/fixtures/br4-rfm-segments.json -> "default",
      with meta.warehouse "Fixture" and partitions 0, because nothing was read
      from storage (docs/API_CONTRACT.md section 1.2). The fixture file itself
      carries the production meta shown above.
Next: replace _load_fixture() with DuckDB over data/gold/rfm_segments/, then
      set meta.warehouse to "Parquet" (API_CONTRACT section 2).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query

from serving.api.models import ApiResponse, QueryMeta

router = APIRouter(prefix="/api/br4", tags=["BR4 — RFM Segmentation"])

# Path to the canonical fixture bundle (relative to the repository root).
_REPO = Path(__file__).resolve().parents[3]
_FIXTURE_PATH = _REPO / "web" / "fixtures" / "br4-rfm-segments.json"


def _load_fixture(empty: bool = False) -> list[dict[str, Any]]:
    """Return fixture data rows from the canonical bundle.

    Reads the "empty" scenario when empty=True, otherwise "default".
    Next: swap this function body for DuckDB over data/gold/rfm_segments/.
    """
    with open(_FIXTURE_PATH) as fh:
        bundle = json.load(fh)
    scenario = "empty" if empty else "default"
    return bundle[scenario]["data"]


@router.get(
    "/segments",
    response_model=ApiResponse,
    summary="RFM customer segments",
    description=(
        "Returns RFM-segmented users for one snapshot date, optionally narrowed "
        "to one segment or to one R/F/M score (a heatmap cell).  Users who never "
        "purchased carry null scores, never 0.\n\n"
        "**Now**: returns fixture data (warehouse=Fixture, partitions=0).  "
        "**Next**: DuckDB over `data/gold/rfm_segments/`, then warehouse=Parquet."
    ),
)
def get_segments(
    snapshot_date: str = Query("2019-11-30", description="RFM snapshot date YYYY-MM-DD"),
    segment: str = Query("all", description='Segment filter or "all"'),
    r_score: int | None = Query(None, ge=1, le=5, description="Filter to R score (1-5)"),
    f_score: int | None = Query(None, ge=1, le=5, description="Filter to F score (1-5)"),
    m_score: int | None = Query(None, ge=1, le=5, description="Filter to M score (1-5)"),
) -> ApiResponse:
    t0 = time.perf_counter()

    # Fixture for now.  Next: DuckDB over data/gold/rfm_segments/.
    data = _load_fixture(empty=False)

    elapsed_ms = (time.perf_counter() - t0) * 1000

    return ApiResponse(
        data=data,
        meta=QueryMeta(
            ms=round(elapsed_ms, 2),
            warehouse="Fixture",  # "Parquet" once DuckDB reads data/gold/rfm_segments/
            partitions=0,
            rows=len(data),
        ),
    )
