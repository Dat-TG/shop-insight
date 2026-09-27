"""BR5 — Abandoned Carts router.

Owner: Nguyen.

Endpoint (placeholder):
    GET /api/br5/carts

Now:  returns no rows, with meta.warehouse "Fixture" and partitions 0
      (docs/API_CONTRACT.md section 1.2).
Next: read Cassandra table ``abandoned_carts`` partitioned by
      ``event_date``.  Key: ((event_date), user_session).
      No DELETE needed — upsert is idempotent (see SYSTEM_DESIGN.md 6.1).
      Then set meta.warehouse to "Cassandra" (API_CONTRACT section 2).
"""

from fastapi import APIRouter

from serving.api.models import ApiResponse, QueryMeta

router = APIRouter(prefix="/api/br5", tags=["BR5 — Abandoned Carts"])


@router.get("/carts", response_model=ApiResponse, summary="Abandoned carts (placeholder)")
def get_carts() -> ApiResponse:
    """Placeholder: returns no rows."""
    return ApiResponse(
        data=[],
        meta=QueryMeta(ms=0.0, warehouse="Fixture", partitions=0, rows=0),
    )
