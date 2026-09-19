/**
 * Shared API types — web/src/types/api.ts
 *
 * Mirror of the Pydantic models in serving/api/models.py.
 * Every endpoint returns ApiResponse<T> so QueryMeta works on all 8 screens.
 *
 * Adding a new BR:
 *   1. Define the row type here (e.g., `export interface Br3Row { ... }`)
 *   2. Use `ApiResponse<Br3Row>` in the page component
 */

/** Metadata about how a query was executed. Displayed in QueryMeta footer. */
export interface QueryMeta {
  /** Server-side wall time in milliseconds */
  ms: number;
  /** Data source: "parquet" | "cassandra" | "fixture" */
  warehouse: string;
  /** Partitions or shards touched */
  partitions: number;
  /** Rows returned in data[] */
  rows: number;
}

/** Universal response envelope — all BR endpoints return this shape. */
export interface ApiResponse<T = unknown> {
  data: T[];
  meta: QueryMeta;
}

// ── BR2 — Conversion Funnel ─────────────────────────────────────────────────
export interface FunnelRow {
  /** "view" | "cart" | "purchase" */
  step: string;
  /** Raw event count */
  count: number;
  /** Distinct sessions at this step */
  session_count: number;
  /** Fraction relative to the view step (view = 1.0) */
  conversion_rate: number;
}
