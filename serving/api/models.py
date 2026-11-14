"""Shared response models for the ShopInsight API.

CONTRACT FROZEN — see docs/API_CONTRACT.md.
Any field change requires simultaneous updates to:
  - This file (producer schema)
  - web/src/types/api.ts (TypeScript types)
  - web/fixtures/<br>.json (fixture)
  - tests/test_fixtures.py (validation)
  - docs/API_CONTRACT.md

Every endpoint returns ApiResponse so React's QueryMeta component works
identically on all 8 screens without per-screen wiring.

Shape (TypeScript equivalent in web/src/types/api.ts):
    {
      "data": [...],          // list of result rows — type varies per BR
      "meta": {
        "ms": 42.5,           // server-side wall time in milliseconds
        "warehouse": "Cassandra",
        "partitions": 1,      // partition keys queried / directories read
        "rows": 3             // == len(data)
      }
    }

Storage mapping (frozen):
    BR1 -> Cassandra  -> gmv_by_minute
    BR2 -> Parquet    -> funnel_daily  (fact_session_funnel; category rows via fact_event + dim_product)
    BR3 -> Cassandra  -> trending_products
    BR4 -> Parquet    -> rfm_segments  (projection of dim_user WHERE is_current)
    BR5 -> Cassandra  -> abandoned_carts
    BR6 -> Cassandra  -> stockout_risk (derived from fact_inventory_daily)
    BR7 -> Parquet    -> product_affinity (derived from fact_event)
    BR8 -> Cassandra  -> order_velocity_alerts

There is no BR9.  BR9 was removed from project scope.
"""

from __future__ import annotations

from typing import Any, Generic, Literal, Optional, TypeVar

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Warehouse enum (frozen)
# ---------------------------------------------------------------------------
# "Fixture" is a transitional value used by placeholder endpoints before the
# real storage backend is wired up.  In production, every endpoint must use
# one of the four real warehouse strings.
Warehouse = Literal["Cassandra", "Parquet", "Postgres", "DuckDB", "Fixture"]

T = TypeVar("T")


# ---------------------------------------------------------------------------
# QueryMeta — appears in the footer of every React screen
# ---------------------------------------------------------------------------
class QueryMeta(BaseModel):
    """Metadata about how a query was executed.

    Displayed verbatim in the footer of every React screen:
        "{ms} ms · {warehouse} · {partitions} partitions · {rows} rows"

    Semantics:
        ms          -- server-side wall time around the storage query only.
                       Does not include browser round-trip or React render.
        warehouse   -- engine that served the response.
        partitions  -- count of partition keys queried (Cassandra) or
                       partition directories read (Parquet).
        rows        -- number of records in data[].  Must equal len(data).
    """

    ms: float = Field(..., ge=0.0, description="Wall time in milliseconds (server side)")
    warehouse: Warehouse = Field(
        ...,
        description='Storage engine: "Cassandra" | "Parquet" | "Postgres" | "DuckDB" | "Fixture"',
    )
    partitions: int = Field(
        ..., ge=0, description="Partition keys queried or directories read"
    )
    rows: int = Field(..., ge=0, description="Rows returned in data[]")

    @field_validator("ms")
    @classmethod
    def ms_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("ms must be >= 0")
        return round(v, 3)


# ---------------------------------------------------------------------------
# ApiResponse — universal response envelope
# ---------------------------------------------------------------------------
class ApiResponse(BaseModel):
    """Universal response envelope.  All BR endpoints use this shape.

    Keeping a single envelope means:
    - The React QueryMeta component needs no per-screen logic.
    - Error handling is uniform: check ``data`` length before rendering.
    - Fixture files can be validated with the same schema as real responses.
    - Empty results are HTTP 200 with data=[] and rows=0, never an error.
    """

    data: list[Any] = Field(default_factory=list)
    meta: QueryMeta


# ===========================================================================
# Per-BR row models
# Frozen field names match the gold-table columns exactly.
# ===========================================================================

# ---------------------------------------------------------------------------
# BR1 — Real-time GMV (Cassandra: gmv_by_minute)
# PRIMARY KEY ((event_date, category_l1), window_start)
# ---------------------------------------------------------------------------
class GmvRow(BaseModel):
    """One row from gmv_by_minute.

    Note: category_l1 = "unknown" is valid and expected for ~32.4% of events
    because source category_code is null in that fraction of rows.
    category_l1 = "all" is the stored total over every category, one row per
    window, written by the stream (start_br1), not summed by the API.
    """

    event_date: str = Field(..., description="Date YYYY-MM-DD")
    category_l1: str = Field(
        ...,
        description='Top-level category, "unknown" when source is null, "all" for the total row',
    )
    window_start: str = Field(..., description="ISO 8601 timestamp with timezone")
    gmv: float = Field(..., description="Gross merchandise value in the window")
    order_count: int = Field(..., description="Number of purchase events in the window")


# ---------------------------------------------------------------------------
# BR2 — Conversion Funnel (Parquet: funnel_daily)
# Gold table columns: event_date, category_l1, views, carts, purchases,
#                     cr_view_to_cart, cr_cart_to_purchase,
#                     view_events, cart_events, purchase_events
# views/carts/purchases count sessions, *_events count raw events (contract 4).
# API row shape — three rows per request, one per funnel step.
# ---------------------------------------------------------------------------
class FunnelRow(BaseModel):
    """One row of the three-stage conversion funnel API response.

    The funnel_stage source values are:
        0 = session has no recorded events (internal; not surfaced in API)
        1 = furthest stage is view
        2 = furthest stage is cart
        3 = furthest stage is purchase (= conversion)

    The API returns exactly three rows in ascending stage order:
        step="view"     -> funnel_stage IN (1, 2, 3)
        step="cart"     -> funnel_stage IN (2, 3)
        step="purchase" -> funnel_stage = 3

    count is the *_events sum, session_count the views/carts/purchases sum,
    over the requested days. conversion_rate is session_count relative to the
    "view" step (view = 1.0), recomputed from those sums, never averaged.
    """

    step: Literal["view", "cart", "purchase"] = Field(
        ..., description="Funnel stage identifier"
    )
    count: int = Field(..., description="Raw event count at this stage")
    session_count: int = Field(
        ..., description="Distinct sessions that reached this stage"
    )
    conversion_rate: float = Field(
        ..., description="Fraction relative to view step (view = 1.0)"
    )


class FunnelCategoryRow(BaseModel):
    """One row of the by-category conversion table (supplementary endpoint)."""

    category_l1: str
    views: int
    carts: int
    purchases: int
    cr_view_to_cart: float
    cr_cart_to_purchase: float


# ---------------------------------------------------------------------------
# BR3 — Trending Products (Cassandra: trending_products)
# PRIMARY KEY (window_start, rank)
# ---------------------------------------------------------------------------
class TrendingProductRow(BaseModel):
    """One row from trending_products.

    Note: category_l1 = "unknown" is valid (same reason as BR1).
    brand may be "unknown" when the source brand field is null.
    """

    window_start: str = Field(..., description="ISO 8601 timestamp of the window")
    rank: int = Field(..., description="1-based rank within the window")
    product_id: int = Field(..., description="REES46 product identifier")
    brand: str = Field(..., description='"unknown" when source brand is null')
    category_l1: str = Field(
        ..., description='"unknown" when source category_code is null'
    )
    view_count: int = Field(..., description="View events in the window")
    cart_count: int = Field(..., description="Cart events in the window")


# ---------------------------------------------------------------------------
# BR4 — RFM Segmentation (Parquet: rfm_segments, from dim_user WHERE is_current)
# Gold: user_id, recency_days, frequency, monetary, r_score, f_score, m_score, segment
# Only current dimension rows (is_current=true, snapshot_date=latest) are used.
# ---------------------------------------------------------------------------
class RfmRow(BaseModel):
    """One user row from rfm_segments.

    Nullable RFM scores (r_score, f_score, m_score, rfm_cell, recency_days)
    are preserved from the source schema.  They are null for users who have
    never purchased (the 'no_purchase' segment, ~88% at the first snapshot).
    Do not substitute 0 or a fabricated score for null.
    """

    user_id: int = Field(..., description="REES46 user identifier")
    snapshot_date: str = Field(..., description="Date YYYY-MM-DD of the RFM snapshot")
    recency_days: Optional[int] = Field(
        None, description="Days since last purchase; null if never purchased"
    )
    frequency: int = Field(..., description="Total purchase event count")
    monetary: float = Field(..., description="Total spend")
    r_score: Optional[int] = Field(
        None, description="Recency score 1-5; null if never purchased"
    )
    f_score: Optional[int] = Field(None, description="Frequency score 1-5")
    m_score: Optional[int] = Field(None, description="Monetary score 1-5")
    rfm_cell: Optional[str] = Field(
        None, description='3-char string e.g. "545"; null if never purchased'
    )
    segment: Literal[
        "champion",
        "loyal",
        "promising",
        "needs_attention",
        "at_risk",
        "hibernating",
        "no_purchase",
    ] = Field(..., description="RFM segment label")


# ---------------------------------------------------------------------------
# BR5 — Abandoned Carts (Cassandra: abandoned_carts)
# PRIMARY KEY ((event_date), user_session)
# ---------------------------------------------------------------------------
class AbandonedCartRow(BaseModel):
    """One row from abandoned_carts.

    The key design drops cart_value from the primary key so that upserts are
    idempotent (same session, new value replaces old row).  The API sorts by
    cart_value DESC in the API layer, not in Cassandra.
    """

    event_date: str = Field(..., description="Date YYYY-MM-DD")
    user_session: str = Field(..., description="Session UUID string")
    cart_value: float = Field(
        ..., description="Total value of items in cart at last event"
    )
    user_id: int = Field(..., description="REES46 user identifier")
    item_count: int = Field(..., description="Number of distinct items in cart")
    last_event_at: str = Field(
        ..., description="ISO 8601 timestamp of the last cart event"
    )


# ---------------------------------------------------------------------------
# BR6 — Stockout Risk (Cassandra: stockout_risk, from fact_inventory_daily)
# PRIMARY KEY ((warehouse_id), days_to_stockout, product_id)
# ---------------------------------------------------------------------------
class StockoutRow(BaseModel):
    """One row from stockout_risk.

    SENTINEL: days_to_stockout = 9999.0 means velocity_7d = 0 (no recent sales).
    Cassandra clustering columns cannot be null, so the sentinel substitutes for
    the NULL that the star schema stores honestly.

    WARNING — stock_on_hand is semi-additive:
        sum across warehouses on ONE date = total stock.
        sum across multiple dates = nonsense.
    BR6 must filter to one snapshot_date and may aggregate across warehouses,
    but must NEVER sum stock_on_hand across multiple dates.

    The screen colours rows red when days_to_stockout < 3.
    """

    warehouse_id: int = Field(..., description="Natural key, 1-5")
    days_to_stockout: float = Field(
        ...,
        description=(
            "Days until stockout at current velocity. "
            "9999.0 = velocity is zero (sentinel, never null in Cassandra)."
        ),
    )
    product_id: int = Field(..., description="REES46 product identifier")
    stock_on_hand: int = Field(
        ..., description="Units on hand. Semi-additive — never sum across dates."
    )
    velocity_7d: float = Field(
        ..., description="Average daily units sold over last 7 days. 0.0 when no sales."
    )


class StockoutSummary(BaseModel):
    """Counts over every SKU in the selected warehouses, for BR6's summary cards.

    The list endpoint returns only the 100 most urgent SKUs per warehouse, so counting
    its rows would miss most of the table. These counts read the whole slice.
    """

    critical: int = Field(..., description="days_to_stockout < 3")
    low_stock: int = Field(..., description="3 <= days_to_stockout < 7")
    no_sales: int = Field(..., description="days_to_stockout = 9999.0 (no sales in 7 days)")
    total: int = Field(..., description="Every SKU in the selected warehouses")


# ---------------------------------------------------------------------------
# BR7 — Product Affinity (Parquet: product_affinity, from fact_event)
# Gold: product_a, product_b, co_count, support, lift
# ---------------------------------------------------------------------------
class AffinityRow(BaseModel):
    """One related-product row from product_affinity.

    Returns up to 10 rows for a given anchor (product_a).
    lift > 1 means the pair co-occurs more than chance.
    """

    product_a: int = Field(..., description="Anchor product identifier")
    product_b: int = Field(..., description="Related product identifier")
    co_count: int = Field(
        ..., description="Number of sessions where both products were purchased"
    )
    support: float = Field(
        ...,
        description="Fraction of all sessions containing both products",
    )
    lift: float = Field(
        ...,
        description=(
            "co_count / (freq_a * freq_b / total_sessions). "
            ">1 = positively associated."
        ),
    )


# ---------------------------------------------------------------------------
# BR8 — Order Velocity Alerts (Cassandra: order_velocity_alerts)
# PRIMARY KEY ((event_date), window_start, user_id)
# CLUSTERING ORDER BY (window_start DESC, user_id ASC)
# ---------------------------------------------------------------------------
class VelocityAlertRow(BaseModel):
    """One row from order_velocity_alerts.

    Severity vocabulary (frozen):
        low    -- within expected range
        medium -- moderately above baseline
        high   -- flagged for manual review
    """

    event_date: str = Field(..., description="Date YYYY-MM-DD")
    window_start: str = Field(
        ..., description="ISO 8601 timestamp of the 5-minute window start"
    )
    user_id: int = Field(..., description="REES46 user identifier")
    order_count: int = Field(..., description="Purchase events in the window")
    total_value: float = Field(..., description="Sum of purchase values in the window")
    severity: Literal["low", "medium", "high"] = Field(
        ..., description="Alert severity level"
    )
