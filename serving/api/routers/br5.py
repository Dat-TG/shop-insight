"""BR5 — Abandoned Carts router.

Owner: Nguyen (W41).

Endpoint (placeholder):
    GET /api/br5/carts

W38 status: returns empty data.
W41 plan:   read Cassandra table ``abandoned_carts`` partitioned by
            ``event_date``.  Key: ((event_date), user_session).
            No DELETE needed — upsert is idempotent (see SYSTEM_DESIGN.md 6.1).
"""

from fastapi import APIRouter

from serving.api.models import ApiResponse, QueryMeta

router = APIRouter(prefix="/api/br5", tags=["BR5 — Abandoned Carts"])


@router.get("/carts", response_model=ApiResponse, summary="Abandoned carts (placeholder)")
def get_carts() -> ApiResponse:
    """Placeholder — to be implemented in W41 by Nguyen."""
    return ApiResponse(
        data=[],
        meta=QueryMeta(ms=0.0, warehouse="fixture", partitions=0, rows=0),
    )
