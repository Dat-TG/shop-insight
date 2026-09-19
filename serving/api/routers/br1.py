"""BR1 — Real-time Operations router.

Owner: Dat (W40).

Endpoint (placeholder):
    GET /api/br1/realtime

W38 status: returns empty data with a note.
W40 plan:   read Cassandra table ``gmv_by_minute`` using cassandra-driver.
"""

from fastapi import APIRouter

from serving.api.models import ApiResponse, QueryMeta

router = APIRouter(prefix="/api/br1", tags=["BR1 — Real-time Operations"])


@router.get("/realtime", response_model=ApiResponse, summary="GMV per minute (placeholder)")
def get_realtime() -> ApiResponse:
    """Placeholder — to be implemented in W40 by Dat.

    W40 plan: query Cassandra ``gmv_by_minute`` partitioned by
    ``(event_date, category_l1)`` and clustered by ``window_start DESC``
    to return the last 60 minutes.
    """
    return ApiResponse(
        data=[],
        meta=QueryMeta(ms=0.0, warehouse="fixture", partitions=0, rows=0),
    )
