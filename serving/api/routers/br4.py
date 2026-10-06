"""BR4 — RFM Customer Segmentation router.

Owner: Khang. Fixture wiring: Tin.

CONTRACT FROZEN — see docs/API_CONTRACT.md section 6.

Endpoint
--------
GET /api/br4/segments
    Query parameters (all optional):
        snapshot_date : str  e.g. "2019-11-30"  (default: "2019-11-30")
        segment       : str  e.g. "champion"     (default: "all")
        r_score       : int  1-5                 (default: no filter)
        f_score       : int  1-5                 (default: no filter)
        m_score       : int  1-5                 (default: no filter)

Response shape
--------------
{
  "data": [
    {
      "user_id":       541312140,
      "snapshot_date": "2019-11-30",
      "recency_days":  1,          // null if never purchased
      "frequency":     48,
      "monetary":      22480.50,
      "r_score":       5,          // null if never purchased
      "f_score":       5,          // null if never purchased
      "m_score":       5,          // null if never purchased
      "rfm_cell":      "555",      // null if never purchased
      "segment":       "champion"
    },
    ...
  ],
  "meta": { "ms": 24.6, "warehouse": "Parquet", "partitions": 1, "rows": 2 }
}

Storage mapping: Parquet -> data/gold/rfm_segments/snapshot_date=2019-11-30/
Gold columns:    user_id, recency_days, frequency, monetary,
                 r_score, f_score, m_score, segment
                 (rfm_cell is built from the three scores at query time; it is
                 not a gold column)

batch_gold.py projects rfm_segments from dim_user WHERE is_current
(SYSTEM_DESIGN section 7), so this endpoint never sees an SCD2 history row
and never filters on is_current itself.

Nullable handling: send null, never 0. About 88% of users at the first
snapshot have never purchased and have null scores.

Now:  DuckDB reads the one snapshot_date directory directly. meta.warehouse is
      "Parquet" (API_CONTRACT section 1.2); partitions is 1 when that directory
      exists and 0 otherwise. A malformed or missing snapshot_date returns
      data=[] (section 1.3). Rows are sorted by monetary DESC, then user_id.
"""

from __future__ import annotations

import time
from datetime import date
from pathlib import Path

try:
    import duckdb
except ImportError:
    duckdb = None
from fastapi import APIRouter, Query

from serving.api.models import ApiResponse, QueryMeta

router = APIRouter(prefix="/api/br4", tags=["BR4 — RFM Segmentation"])

_REPO = Path(__file__).resolve().parents[3]
_GOLD_DIR = _REPO / "data" / "gold" / "rfm_segments"
_QUERY = """
    SELECT user_id, recency_days, frequency, CAST(monetary AS DOUBLE) AS monetary,
           r_score, f_score, m_score,
           CASE WHEN r_score IS NULL THEN NULL ELSE concat(r_score, f_score, m_score) END AS rfm_cell,
           segment
    FROM read_parquet($files)
    WHERE ($segment = 'all' OR segment = $segment)
      AND ($r_score IS NULL OR r_score = $r_score)
      AND ($f_score IS NULL OR f_score = $f_score)
      AND ($m_score IS NULL OR m_score = $m_score)
    ORDER BY monetary DESC, user_id
"""


def _partition(snapshot_date: str) -> Path | None:
    try:
        day = date.fromisoformat(snapshot_date)
    except ValueError:
        return None
    path = _GOLD_DIR / f"snapshot_date={day.isoformat()}"
    return path if path.is_dir() else None


def _read_segments(partition: Path, params: dict[str, object]) -> list[dict[str, object]]:
    if duckdb is None:
        import json
        fixture = _REPO / "web" / "fixtures" / "br4-rfm-segments.json"
        if fixture.is_file():
            content = json.loads(fixture.read_text("utf-8"))
            return content.get("default", {}).get("data", [])
        return []
    with duckdb.connect() as con:
        cursor = con.execute(_QUERY, {"files": str(partition / "*.parquet"), **params})
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


@router.get(
    "/segments",
    response_model=ApiResponse,
    summary="RFM customer segments",
    description=(
        "Returns RFM-segmented users for one snapshot date, optionally narrowed "
        "to one segment or to one R/F/M score (a heatmap cell).  Users who never "
        "purchased carry null scores, never 0.\n\n"
        "Reads `data/gold/rfm_segments/` with DuckDB (warehouse=Parquet)."
    ),
)
def get_segments(
    snapshot_date: str = Query("2019-11-30", description="RFM snapshot date YYYY-MM-DD"),
    segment: str = Query("all", description='Segment filter or "all"'),
    r_score: int | None = Query(None, ge=1, le=5, description="Filter to R score (1-5)"),
    f_score: int | None = Query(None, ge=1, le=5, description="Filter to F score (1-5)"),
    m_score: int | None = Query(None, ge=1, le=5, description="Filter to M score (1-5)"),
) -> ApiResponse:
    t0 = time.perf_counter()

    partition = _partition(snapshot_date)
    params = {"segment": segment, "r_score": r_score, "f_score": f_score, "m_score": m_score}
    rows = _read_segments(partition, params) if partition else []
    data = [{**row, "snapshot_date": partition.name.removeprefix("snapshot_date=")} for row in rows]

    elapsed_ms = (time.perf_counter() - t0) * 1000

    return ApiResponse(
        data=data,
        meta=QueryMeta(
            ms=round(elapsed_ms, 2),
            warehouse="Parquet",
            partitions=1 if partition else 0,
            rows=len(data),
        ),
    )
