"""BR1 — Real-time Operations router.

Owner: Dat.

Endpoint (placeholder):
    GET /api/br1/realtime

Now:  returns no rows, with meta.warehouse "Fixture" and partitions 0
      (docs/API_CONTRACT.md section 1.2).
Next: read Cassandra table ``gmv_by_minute`` using cassandra-driver, then
      set meta.warehouse to "Cassandra" (API_CONTRACT section 2).
"""

from fastapi import APIRouter

from serving.api.models import ApiResponse, QueryMeta

router = APIRouter(prefix="/api/br1", tags=["BR1 — Real-time Operations"])


@router.get("/realtime", response_model=ApiResponse, summary="GMV per minute (placeholder)")
def get_realtime() -> ApiResponse:
    """Placeholder: returns no rows.

    Next: query Cassandra ``gmv_by_minute`` partitioned by
    ``(event_date, category_l1)`` and clustered by ``window_start DESC``
    to return the last 60 minutes.
    """
    return ApiResponse(
        data=[],
        meta=QueryMeta(ms=0.0, warehouse="Fixture", partitions=0, rows=0),
    )
