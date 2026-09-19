"""BR4 — RFM Customer Segmentation router.

Owner: Khang (W39).

Endpoint (placeholder):
    GET /api/br4/segments

W38 status: returns empty data.
W39 plan:   read gold/rfm_segments/snapshot_date=2019-11-30/ via DuckDB.
            Response rows: user_id, recency_days, frequency, monetary, segment.
"""

from fastapi import APIRouter

from serving.api.models import ApiResponse, QueryMeta

router = APIRouter(prefix="/api/br4", tags=["BR4 — RFM Segmentation"])


@router.get("/segments", response_model=ApiResponse, summary="RFM customer segments (placeholder)")
def get_segments() -> ApiResponse:
    """Placeholder — to be implemented in W39 by Khang."""
    return ApiResponse(
        data=[],
        meta=QueryMeta(ms=0.0, warehouse="fixture", partitions=0, rows=0),
    )
