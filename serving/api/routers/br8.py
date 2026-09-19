"""BR8 — Order Velocity Alerts router.

Owner: Tin (W41).

Endpoint (placeholder):
    GET /api/br8/alerts

W38 status: returns empty data.
W41 plan:   read Cassandra table ``order_velocity_alerts`` partitioned by
            ``event_date``, clustered by ``window_start DESC``.
            severity values: "low" | "medium" | "high".
"""

from fastapi import APIRouter

from serving.api.models import ApiResponse, QueryMeta

router = APIRouter(prefix="/api/br8", tags=["BR8 — Order Velocity Alerts"])


@router.get("/alerts", response_model=ApiResponse, summary="Order velocity alerts (placeholder)")
def get_alerts() -> ApiResponse:
    """Placeholder — to be implemented in W41 by Tin."""
    return ApiResponse(
        data=[],
        meta=QueryMeta(ms=0.0, warehouse="fixture", partitions=0, rows=0),
    )
