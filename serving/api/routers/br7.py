"""BR7 — Product Affinity (Bought Together) router.

Owner: Nguyen.

Endpoint (placeholder):
    GET /api/br7/affinity

Now:  returns no rows, with meta.warehouse "Fixture" and partitions 0
      (docs/API_CONTRACT.md section 1.2).
Next: read gold/product_affinity/ via DuckDB.
      Response rows: product_a, product_b, co_count, support, lift.
      Filter by anchor product_id query param.
      Then set meta.warehouse to "Parquet" (API_CONTRACT section 2).
"""

from fastapi import APIRouter

from serving.api.models import ApiResponse, QueryMeta

router = APIRouter(prefix="/api/br7", tags=["BR7 — Product Affinity"])


@router.get("/affinity", response_model=ApiResponse, summary="Frequently bought together (placeholder)")
def get_affinity() -> ApiResponse:
    """Placeholder: returns no rows."""
    return ApiResponse(
        data=[],
        meta=QueryMeta(ms=0.0, warehouse="Fixture", partitions=0, rows=0),
    )
