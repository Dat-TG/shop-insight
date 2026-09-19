"""Shared response models for the ShopInsight API.

Every endpoint returns ApiResponse so React's QueryMeta component works
identically on all 8 screens without per-screen wiring.

Shape (TypeScript equivalent in web/src/types/api.ts):
    {
      "data": [...],          // list of result rows — type varies per BR
      "meta": {
        "ms": 42,             // server-side wall time in milliseconds
        "warehouse": "parquet | cassandra | fixture",
        "partitions": 30,     // partitions / rows read at the storage layer
        "rows": 1234          // rows returned in data[]
      }
    }
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class QueryMeta(BaseModel):
    """Metadata about how a query was executed.

    Displayed verbatim in the footer of every React screen:
        "{ms} ms · {warehouse} · {partitions} partitions · {rows} rows"
    """

    ms: float = Field(..., description="Wall time in milliseconds (server side)")
    warehouse: str = Field(
        ...,
        description='Data source: "parquet", "cassandra", or "fixture"',
        examples=["parquet", "cassandra", "fixture"],
    )
    partitions: int = Field(..., description="Partitions or shards touched")
    rows: int = Field(..., description="Rows returned in data[]")


class ApiResponse(BaseModel):
    """Universal response envelope.  All BR endpoints use this shape.

    Keeping a single envelope means:
    - The React QueryMeta component needs no per-screen logic.
    - Error handling is uniform: check ``data`` length before rendering.
    - Fixture files can be validated with the same schema as real responses.
    """

    data: list[Any] = Field(default_factory=list)
    meta: QueryMeta
