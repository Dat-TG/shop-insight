"""BR3 — Trending Products router.

Owner: Khang (W41).

Endpoint (placeholder):
    GET /api/br3/trending

W38 status: returns empty data.
W41 plan:   read Cassandra table ``trending_products`` partitioned by
            ``window_start``.  Top-N cut happens inside foreachBatch in
            streaming_gold.py, so this endpoint just reads the latest partition.
"""

from fastapi import APIRouter

from serving.api.models import ApiResponse, QueryMeta

router = APIRouter(prefix="/api/br3", tags=["BR3 — Trending Products"])


@router.get("/trending", response_model=ApiResponse, summary="Top-20 trending products (placeholder)")
def get_trending() -> ApiResponse:
    """Placeholder — to be implemented in W41 by Khang."""
    return ApiResponse(
        data=[],
        meta=QueryMeta(ms=0.0, warehouse="fixture", partitions=0, rows=0),
    )
