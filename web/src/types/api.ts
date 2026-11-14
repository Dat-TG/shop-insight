/**
 * Shared API types — web/src/types/api.ts
 *
 * CONTRACT FROZEN — see docs/API_CONTRACT.md.
 * Any field change requires simultaneous updates to:
 *   - This file (TypeScript types)
 *   - serving/api/models.py (Pydantic models)
 *   - web/fixtures/<br>-*.json (fixture files)
 *   - tests/test_fixtures.py (validation)
 *   - docs/API_CONTRACT.md
 *
 * Mirror of the Pydantic models in serving/api/models.py.
 * Every endpoint returns ApiResponse<T> so QueryMeta works on all 8 screens.
 *
 * Storage mapping (frozen):
 *   BR1 -> Cassandra -> gmv_by_minute
 *   BR2 -> Parquet   -> funnel_daily
 *   BR3 -> Cassandra -> trending_products
 *   BR4 -> Parquet   -> rfm_segments
 *   BR5 -> Cassandra -> abandoned_carts
 *   BR6 -> Cassandra -> stockout_risk
 *   BR7 -> Parquet   -> product_affinity
 *   BR8 -> Cassandra -> order_velocity_alerts
 *
 * There is no BR9. BR9 was removed from project scope.
 */

// ── Warehouse enum (frozen) ───────────────────────────────────────────────────
/** Storage engine identifier. "Fixture" is transitional only. */
export type Warehouse = "Cassandra" | "Parquet" | "Postgres" | "DuckDB" | "Fixture";

// ── QueryMeta — appears in the footer of every screen ────────────────────────
/**
 * Metadata about how a query was executed.
 *
 * Semantics:
 *   ms         — server-side wall time around the storage query only.
 *                Does not include browser round-trip or React render time.
 *   warehouse  — engine that served the response.
 *   partitions — count of partition keys queried (Cassandra) or
 *                partition directories read (Parquet).
 *   rows       — number of records in data[]. Must equal data.length.
 */
export interface QueryMeta {
  /** Server-side wall time in milliseconds (>= 0) */
  ms: number;
  /** Storage engine that served the response */
  warehouse: Warehouse;
  /** Partition keys queried or directories read (>= 0) */
  partitions: number;
  /** Rows returned in data[] — must equal data.length (>= 0) */
  rows: number;
}

// ── Universal response envelope ───────────────────────────────────────────────
/**
 * Every BR endpoint returns this shape.
 * Empty results are HTTP 200 with data=[] and meta.rows=0, never an error.
 */
export interface ApiResponse<T = unknown> {
  data: T[];
  meta: QueryMeta;
}

// ── Fixture bundle format (web/fixtures/*.json) ───────────────────────────────
/** A fixture file wraps two scenarios so both can live in one file. */
export interface FixtureBundle<T = unknown> {
  default: ApiResponse<T>;
  empty: ApiResponse<T>;
}

// =============================================================================
// BR1 — Real-time GMV  (Cassandra: gmv_by_minute)
// PRIMARY KEY ((event_date, category_l1), window_start)
// =============================================================================
/**
 * One row from gmv_by_minute.
 * category_l1 = "unknown" is valid (~32.4% of source events have no category_code).
 * category_l1 = "all" is the stored total over every category, written by the stream.
 */
export interface GmvRow {
  /** Date YYYY-MM-DD */
  event_date: string;
  /** Top-level category; "unknown" when source category_code is null; "all" for the total row */
  category_l1: string;
  /** ISO 8601 timestamp with timezone */
  window_start: string;
  /** Gross merchandise value in the window */
  gmv: number;
  /** Number of purchase events in the window */
  order_count: number;
}

// =============================================================================
// BR2 — Conversion Funnel  (Parquet: funnel_daily)
// Gold columns: event_date, category_l1, views, carts, purchases,
//               cr_view_to_cart, cr_cart_to_purchase,
//               view_events, cart_events, purchase_events
// views/carts/purchases count sessions, *_events count raw events (contract 4).
// =============================================================================
/**
 * One row of the three-stage conversion funnel API response.
 *
 * funnel_stage source values (from fact_session_funnel):
 *   0 = no recorded events (not surfaced in API)
 *   1 = furthest stage is view
 *   2 = furthest stage is cart
 *   3 = furthest stage is purchase (= conversion)
 *
 * The API returns exactly 3 rows per request, one per funnel step.
 * count is the *_events sum, session_count the views/carts/purchases sum,
 * over the requested days. conversion_rate is session_count relative to the
 * "view" step (view = 1.0), recomputed from those sums, never averaged.
 */
export interface FunnelRow {
  /** Funnel stage: "view" | "cart" | "purchase" */
  step: "view" | "cart" | "purchase";
  /** Raw event count at this stage */
  count: number;
  /** Distinct sessions that reached this stage */
  session_count: number;
  /** Fraction relative to view step (view = 1.0) */
  conversion_rate: number;
}

/** Supplementary by-category breakdown row (category filter table). */
export interface FunnelCategoryRow {
  category_l1: string;
  views: number;
  carts: number;
  purchases: number;
  cr_view_to_cart: number;
  cr_cart_to_purchase: number;
}

// =============================================================================
// BR3 — Trending Products  (Cassandra: trending_products)
// PRIMARY KEY (window_start, rank)
// =============================================================================
/**
 * One row from trending_products.
 * category_l1 / brand may be "unknown" for the same null reasons as BR1.
 */
export interface TrendingProductRow {
  /** ISO 8601 timestamp of the 15-minute sliding window */
  window_start: string;
  /** 1-based rank within the window */
  rank: number;
  /** REES46 product identifier */
  product_id: number;
  /** Brand name; "unknown" when source brand is null */
  brand: string;
  /** Top-level category; "unknown" when source category_code is null */
  category_l1: string;
  /** View events in the window */
  view_count: number;
  /** Cart events in the window */
  cart_count: number;
}

// =============================================================================
// BR4 — RFM Segmentation  (Parquet: rfm_segments, projection of dim_user)
// Gold: user_id, recency_days, frequency, monetary, r_score, f_score, m_score, segment
// Only is_current=true rows contribute.
// =============================================================================
/** RFM segment labels (matches dim_user.segment CHECK constraint). */
export type RfmSegment =
  | "champion"
  | "loyal"
  | "promising"
  | "needs_attention"
  | "at_risk"
  | "hibernating"
  | "no_purchase";

/**
 * One user row from rfm_segments.
 *
 * Nullable fields (recency_days, r_score, f_score, m_score, rfm_cell) are null
 * for users who have never purchased.  Do NOT substitute 0 for null.
 */
export interface RfmRow {
  /** REES46 user identifier */
  user_id: number;
  /** Date YYYY-MM-DD of the RFM snapshot */
  snapshot_date: string;
  /** Days since last purchase; null if never purchased */
  recency_days: number | null;
  /** Total purchase event count */
  frequency: number;
  /** Total spend */
  monetary: number;
  /** Recency score 1–5; null if never purchased */
  r_score: number | null;
  /** Frequency score 1–5; null if never purchased */
  f_score: number | null;
  /** Monetary score 1–5; null if never purchased */
  m_score: number | null;
  /** 3-char string e.g. "545"; null if never purchased */
  rfm_cell: string | null;
  /** RFM segment label */
  segment: RfmSegment;
}

// =============================================================================
// BR5 — Abandoned Carts  (Cassandra: abandoned_carts)
// PRIMARY KEY ((event_date), user_session)
// =============================================================================
/**
 * One row from abandoned_carts.
 * API sorts by cart_value DESC (Cassandra does not, by key design).
 */
export interface AbandonedCartRow {
  /** Date YYYY-MM-DD */
  event_date: string;
  /** Session UUID string */
  user_session: string;
  /** Total value of items in cart at last event */
  cart_value: number;
  /** REES46 user identifier */
  user_id: number;
  /** Number of distinct items in cart */
  item_count: number;
  /** ISO 8601 timestamp of the last cart event */
  last_event_at: string;
}

// =============================================================================
// BR6 — Stockout Risk  (Cassandra: stockout_risk, from fact_inventory_daily)
// PRIMARY KEY ((warehouse_id), days_to_stockout, product_id)
// =============================================================================
/**
 * One row from stockout_risk.
 *
 * SENTINEL: days_to_stockout = 9999.0 means velocity_7d = 0 (no recent sales).
 * Cassandra clustering columns cannot be null, so this sentinel substitutes for
 * the NULL that the star schema stores honestly in fact_inventory_daily.
 *
 * WARNING — stock_on_hand is SEMI-ADDITIVE:
 *   Sum across warehouses on ONE date = total stock (valid).
 *   Sum across multiple dates = nonsense (invalid).
 * BR6 must filter to one snapshot date and may aggregate across warehouses,
 * but must NEVER sum stock_on_hand across multiple dates.
 *
 * Screen colours rows red when days_to_stockout < 3.
 */
export interface StockoutRow {
  /** Natural key, 1–5 */
  warehouse_id: number;
  /**
   * Days until stockout at current velocity.
   * 9999.0 = zero velocity (sentinel). Never null in API response.
   */
  days_to_stockout: number;
  /** REES46 product identifier */
  product_id: number;
  /** Units on hand. Semi-additive — never sum across dates. */
  stock_on_hand: number;
  /** Average daily units sold over last 7 days. 0.0 when no sales. */
  velocity_7d: number;
}

/**
 * BR6 summary cards — GET /api/br6/summary. Counts over every SKU in the selected
 * warehouses, not only the 100 most urgent per warehouse that /stockout returns.
 */
export interface StockoutSummary {
  /** days_to_stockout < 3 */
  critical: number;
  /** 3 <= days_to_stockout < 7 */
  low_stock: number;
  /** days_to_stockout = 9999.0 (no sales in 7 days) */
  no_sales: number;
  /** Every SKU in the selected warehouses */
  total: number;
}

// =============================================================================
// BR7 — Product Affinity  (Parquet: product_affinity, from fact_event)
// Gold: product_a, product_b, co_count, support, lift
// =============================================================================
/**
 * One related-product row from product_affinity.
 * Returns up to 10 rows for a given anchor product (product_a).
 */
export interface AffinityRow {
  /** Anchor product identifier */
  product_a: number;
  /** Related product identifier */
  product_b: number;
  /** Sessions where both products were purchased */
  co_count: number;
  /** Fraction of all sessions containing both products */
  support: number;
  /**
   * co_count / (freq_a * freq_b / total_sessions).
   * > 1 means positively associated.
   */
  lift: number;
}

// =============================================================================
// BR8 — Order Velocity Alerts  (Cassandra: order_velocity_alerts)
// PRIMARY KEY ((event_date), window_start, user_id)
// CLUSTERING ORDER BY (window_start DESC, user_id ASC)
// =============================================================================
/** Alert severity — frozen vocabulary */
export type AlertSeverity = "low" | "medium" | "high";

/** One row from order_velocity_alerts. */
export interface VelocityAlertRow {
  /** Date YYYY-MM-DD */
  event_date: string;
  /** ISO 8601 timestamp of the 5-minute window start */
  window_start: string;
  /** REES46 user identifier */
  user_id: number;
  /** Purchase events in the 5-minute window */
  order_count: number;
  /** Sum of purchase values in the window */
  total_value: number;
  /** Alert severity level */
  severity: AlertSeverity;
}
