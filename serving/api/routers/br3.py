"""BR3 — Trending Products router.

Owner: Khang.

Endpoint (placeholder):
    GET /api/br3/trending

Now:  returns no rows, with meta.warehouse "Fixture" and partitions 0
      (docs/API_CONTRACT.md section 1.2).
Next: read Cassandra table ``trending_products`` partitioned by
      ``window_start``.  Top-N cut happens inside foreachBatch in
      streaming_gold.py, so this endpoint just reads the latest partition,
      then sets meta.warehouse to "Cassandra" (API_CONTRACT section 2).
"""

from fastapi import APIRouter

from serving.api.models import ApiResponse, QueryMeta

router = APIRouter(prefix="/api/br3", tags=["BR3 — Trending Products"])


@router.get("/trending", response_model=ApiResponse, summary="Top-20 trending products (placeholder)")
def get_trending() -> ApiResponse:
    """Placeholder: returns no rows."""
    return ApiResponse(
        data=[],
        meta=QueryMeta(ms=0.0, warehouse="Fixture", partitions=0, rows=0),
    )
