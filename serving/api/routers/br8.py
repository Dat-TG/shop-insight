"""BR8 — Order Velocity Alerts router.

Owner: Tin.

Endpoint (placeholder):
    GET /api/br8/alerts

Now:  returns no rows, with meta.warehouse "Fixture" and partitions 0
      (docs/API_CONTRACT.md section 1.2).
Next: read Cassandra table ``order_velocity_alerts`` partitioned by
      ``event_date``, clustered by ``window_start DESC``.
      severity values: "low" | "medium" | "high".
      Then set meta.warehouse to "Cassandra" (API_CONTRACT section 2).
"""

from fastapi import APIRouter

from serving.api.models import ApiResponse, QueryMeta

router = APIRouter(prefix="/api/br8", tags=["BR8 — Order Velocity Alerts"])


@router.get("/alerts", response_model=ApiResponse, summary="Order velocity alerts (placeholder)")
def get_alerts() -> ApiResponse:
    """Placeholder: returns no rows."""
    return ApiResponse(
        data=[],
        meta=QueryMeta(ms=0.0, warehouse="Fixture", partitions=0, rows=0),
    )
