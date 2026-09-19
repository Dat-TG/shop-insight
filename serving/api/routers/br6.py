"""BR6 — Stockout Risk router.

Owner: Tin (W39).

Endpoint (placeholder):
    GET /api/br6/stockout

W38 status: returns empty data.
W39 plan:   read Cassandra table ``stockout_risk`` partitioned by
            ``warehouse_id``, clustered by ``days_to_stockout ASC``.
            sentinel: days_to_stockout = 9999.0 means no movement (velocity = 0).
"""

from fastapi import APIRouter

from serving.api.models import ApiResponse, QueryMeta

router = APIRouter(prefix="/api/br6", tags=["BR6 — Stockout Risk"])


@router.get("/stockout", response_model=ApiResponse, summary="Stockout risk per SKU (placeholder)")
def get_stockout() -> ApiResponse:
    """Placeholder — to be implemented in W39 by Tin."""
    return ApiResponse(
        data=[],
        meta=QueryMeta(ms=0.0, warehouse="fixture", partitions=0, rows=0),
    )
