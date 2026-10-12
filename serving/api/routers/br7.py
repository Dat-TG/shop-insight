"""BR7 — Product Affinity (Bought Together) router.

Owner: Nguyen.

    GET /api/br7/affinity?product_id=N   up to 10 products bought in the same session as N
    GET /api/br7/anchors                 ids that have enough partners to demo (empty-state helper)

Reads data/gold/product_affinity/ (written by processing/gold_br7.py) with DuckDB, and joins the
CURRENT dim_product row only to show brand, category and price.
"""

import time
from pathlib import Path

import duckdb
from fastapi import APIRouter, Query

from serving.api.models import ApiResponse, QueryMeta

REPO = Path(__file__).resolve().parents[3]
AFFINITY_DIR = REPO / "data" / "gold" / "product_affinity"
AFFINITY_GLOB = str(AFFINITY_DIR / "*.parquet")
DIM_PRODUCT_GLOB = str(REPO / "data" / "warehouse" / "dim_product" / "**" / "*.parquet")

TOP_N = 10

router = APIRouter(prefix="/api/br7", tags=["BR7 — Product Affinity"])


def run(sql: str, params: list) -> tuple[list[dict], float]:
    """One query on a fresh in-memory connection; returns (rows, milliseconds)."""
    con = duckdb.connect()
    try:
        start = time.perf_counter()
        cur = con.execute(sql, params)
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return rows, round((time.perf_counter() - start) * 1000, 1)
    finally:
        con.close()


def response(rows: list[dict], ms: float) -> ApiResponse:
    # partitions = gold Parquet files DuckDB opened. API_CONTRACT section 2: warehouse "Parquet".
    files = len(list(AFFINITY_DIR.glob("*.parquet")))
    return ApiResponse(data=rows, meta=QueryMeta(ms=ms, warehouse="Parquet", partitions=files, rows=len(rows)))


@router.get("/affinity", response_model=ApiResponse, summary="Frequently bought together")
def get_affinity(product_id: int = Query(..., ge=0)) -> ApiResponse:
    # co_count first: a pair seen 40 times beats a pair seen 3 times with a bigger lift.
    sql = f"""
        SELECT a.product_a, a.product_b, a.co_count, a.support, a.lift,
               p.brand, p.category_l1, p.price
        FROM read_parquet(?) a
        LEFT JOIN (SELECT product_id, brand, category_l1, price
                   FROM read_parquet(?, union_by_name = true)
                   WHERE is_current) p ON p.product_id = a.product_b
        WHERE a.product_a = ?
        ORDER BY a.co_count DESC, a.lift DESC
        LIMIT {TOP_N}
    """
    rows, ms = run(sql, [AFFINITY_GLOB, DIM_PRODUCT_GLOB, product_id])
    for r in rows:
        r["price"] = float(r["price"]) if r["price"] is not None else None
    return response(rows, ms)


@router.get("/anchors", response_model=ApiResponse, summary="Products with enough partners to demo")
def get_anchors(limit: int = Query(12, ge=1, le=50)) -> ApiResponse:
    sql = """
        SELECT product_a AS product_id, count(*) AS partners
        FROM read_parquet(?)
        GROUP BY product_a
        HAVING count(*) >= ?
        ORDER BY partners DESC, sum(co_count) DESC
        LIMIT ?
    """
    rows, ms = run(sql, [AFFINITY_GLOB, TOP_N, limit])
    return response(rows, ms)