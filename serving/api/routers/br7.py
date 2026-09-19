"""BR7 — Product Affinity (Bought Together) router.

Owner: Nguyen (W39).

Endpoint (placeholder):
    GET /api/br7/affinity

W38 status: returns empty data.
W39 plan:   read gold/product_affinity/ via DuckDB.
            Response rows: product_a, product_b, co_count, support, lift.
            Filter by anchor product_id query param.
"""

from fastapi import APIRouter

from serving.api.models import ApiResponse, QueryMeta

router = APIRouter(prefix="/api/br7", tags=["BR7 — Product Affinity"])


@router.get("/affinity", response_model=ApiResponse, summary="Frequently bought together (placeholder)")
def get_affinity() -> ApiResponse:
    """Placeholder — to be implemented in W39 by Nguyen."""
    return ApiResponse(
        data=[],
        meta=QueryMeta(ms=0.0, warehouse="fixture", partitions=0, rows=0),
    )
