"""BR4 — RFM Customer Segmentation router.

Owner: Khang (W39: connects to star schema dim_user).

Endpoint
--------
GET /api/br4/segments
    Query parameters (all optional):
        snapshot_date : str  e.g. "2019-11-30"  (default: "2019-11-30")
        segment       : str  e.g. "champion"     (default: "all")
        limit         : int  (default: 100)

Response shape
--------------
{
  "data": [
    {
      "user_id":       541312140,
      "snapshot_date": "2019-11-30",
      "recency_days":  1,
      "frequency":     48,
      "monetary":      22480.50,
      "r_score":       5,
      "f_score":       5,
      "m_score":       5,
      "rfm_cell":      "555",
      "segment":       "champion",
      "is_current":    true
    },
    ...
  ],
  "meta": { "ms": 24.6, "warehouse": "Postgres", "partitions": 1, "rows": 8 }
}

Source (W39+):  dim_user WHERE is_current = TRUE
Required cols:  rfm_cell, segment, is_current

W38 status: returns empty data.
W39: update to return fixture data from web/fixtures/br4-rfm-segments.json.
W40 plan:   replace _load_fixture() with Postgres query over dim_user.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query

from serving.api.models import ApiResponse, QueryMeta

router = APIRouter(prefix="/api/br4", tags=["BR4 — RFM Segmentation"])

_REPO = Path(__file__).resolve().parents[3]
_FIXTURE = _REPO / "web" / "fixtures" / "br4-rfm-segments.json"


def _load_fixture(empty: bool = False) -> list[dict[str, Any]]:
    """Return fixture data rows.

    W39: source = dim_user (SCD2 star schema).
    W40: replace this with a Postgres query:
        SELECT
            u.user_id,
            u.snapshot_date,
            u.recency_days,
            u.frequency,
            u.monetary,
            u.r_score,
            u.f_score,
            u.m_score,
            u.rfm_cell,
            u.segment,
            u.is_current
        FROM dim_user u
        WHERE u.is_current = TRUE          -- SCD2: always filter current rows only
          AND (:segment = 'all' OR u.segment = :segment)
        ORDER BY u.monetary DESC NULLS LAST
        LIMIT :limit
    """
    with open(_FIXTURE) as fh:
        payload = json.load(fh)
    key = "empty" if empty else "default"
    return payload[key]["data"]


@router.get(
    "/segments",
    response_model=ApiResponse,
    summary="RFM customer segments (dim_user star schema)",
    description=(
        "Returns RFM-segmented users from the star schema dimension table.  \n\n"
        "**Source (W39+)**: `dim_user WHERE is_current = TRUE`  \n"
        "**Required columns**: `rfm_cell`, `segment`, `is_current`  \n\n"
        "⚠️ **Always filter `WHERE is_current = TRUE`** — dim_user is SCD Type 2: "
        "each user may have historical rows with is_current = FALSE.  \n\n"
        "**W38**: returns empty data.  \n"
        "**W39**: returns fixture data.  \n"
        "**W40**: will query `dim_user` in Postgres."
    ),
)
def get_segments(
    snapshot_date: str = Query("2019-11-30", description="RFM snapshot date YYYY-MM-DD"),
    segment: str = Query("all", description='Segment filter or "all"'),
    limit: int = Query(100, ge=1, le=10000, description="Max rows to return"),
) -> ApiResponse:
    t0 = time.perf_counter()

    # W39: fixture. W40: replace with dim_user Postgres query (filter is_current=TRUE).
    data = _load_fixture(empty=False)

    elapsed_ms = (time.perf_counter() - t0) * 1000

    return ApiResponse(
        data=data,
        meta=QueryMeta(
            ms=round(elapsed_ms, 2),
            warehouse="Postgres",
            partitions=1,
            rows=len(data),
        ),
    )
