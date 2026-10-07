# ShopInsight API Contract

**Status: FROZEN**

This document is the single source of truth for the eight BR API contracts.
It was frozen on 2026-09-20 and must be kept in sync with:

- `serving/api/models.py` — Pydantic row models
- `web/src/types/api.ts` — TypeScript row interfaces
- `web/fixtures/<br>-*.json` — canonical fixture bundles
- `tests/test_fixtures.py` — automated fixture validation

> **There are exactly eight BR contracts — BR1 through BR8.
> BR9 was removed from project scope and does not exist.**

---

## Change rule

Any field rename, type change, or addition requires **simultaneous** updates to
every item in the list above **plus** the relevant Spark schema or Cassandra DDL.
Changes must be agreed by all team members before merging.

---

## 1. Common Response Envelope

All eight BR endpoints return the same JSON shape:

```json
{
  "data": [ ... ],
  "meta": {
    "ms": 12.5,
    "warehouse": "Parquet",
    "partitions": 1,
    "rows": 3
  }
}
```

### 1.1 QueryMeta fields

| Field | Type | Constraints | Semantics |
|---|---|---|---|
| `ms` | `number` | ≥ 0 | Server-side wall time in milliseconds, measured around the actual storage query only. Does **not** include browser round-trip or React render time. |
| `warehouse` | `string` (enum) | See below | Storage engine that served the response. |
| `partitions` | `integer` | ≥ 0 | Cassandra: number of partition keys queried. Parquet: number of `event_date` or relevant partition directories read. |
| `rows` | `integer` | ≥ 0 | Number of records in `data[]`. **Must equal `data.length`**. |

### 1.2 Allowed `warehouse` values

| Value | When used |
|---|---|
| `"Cassandra"` | BR1, BR3, BR5, BR6, BR8 (streaming-path Cassandra gold tables) |
| `"Parquet"` | BR2, BR4, BR7 (batch-path Parquet gold files) |
| `"Postgres"` | Reserved; no BR endpoint reads Postgres, which is the benchmark tier (SYSTEM_DESIGN 12) |
| `"DuckDB"` | Reserved; BR2/BR4/BR7 may migrate to DuckDB over Parquet |
| `"Fixture"` | Transitional only: an endpoint returning fixture or empty placeholder data instead of querying its §2 store; `partitions` is `0`. Fixture files carry the production value. |

### 1.3 Empty-result semantics

Empty results are **HTTP 200** with `data: []` — never a 404 or error.

```json
{ "data": [], "meta": { "ms": 2.3, "warehouse": "Cassandra", "partitions": 1, "rows": 0 } }
```

`rows` must be `0`. `partitions` may still be > 0 if partitions were queried
but no records matched.

---

## 2. Storage Mapping (frozen)

```
BR1 -> Cassandra  -> gmv_by_minute               (streaming: streaming_gold.py)
BR2 -> Parquet    -> funnel_daily                 (batch:    batch_gold.py)
BR3 -> Cassandra  -> trending_products            (streaming: streaming_gold.py)
BR4 -> Parquet    -> rfm_segments                 (batch:    batch_gold.py)
BR5 -> Cassandra  -> abandoned_carts              (streaming: streaming_gold.py)
BR6 -> Cassandra  -> stockout_risk                (batch:    batch_gold.py)
BR7 -> Parquet    -> product_affinity             (batch:    batch_gold.py)
BR8 -> Cassandra  -> order_velocity_alerts        (streaming: streaming_gold.py)
```

BR2, BR4, and BR7 may later be served through DuckDB reading the same Parquet
files, but their production `warehouse` value remains `"Parquet"` until that
migration is completed.

---

## 3. BR1 — Real-time GMV

**Business purpose:** Executive screen showing gross merchandise value per
one-minute window, for all categories or one top-level product category. The
endpoint returns up to the last 120 one-minute windows of one partition; the
screen charts the newest 60 and compares them with the 60 before ("vs previous
60 min"). Refreshes every 10 seconds.

**Endpoint:** `GET /api/br1/realtime`

**Query parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `event_date` | `string` | No | Today's date | Filter date `YYYY-MM-DD` |
| `category_l1` | `string` | No | `"all"` | Category filter or `"all"` |

"Today" is the date in Vietnam time. On the November 2019 data that returns an
empty 200, so the screen always sends a date: `2019-11-17`, the demo replay day.

**Storage engine:** Cassandra

**Gold table:** `gmv_by_minute`

**`category_l1 = "all"` is a stored partition, not a sum made by the API.** The
stream (`start_br1` in `processing/streaming_gold.py`) writes one extra row per
window under `"all"`, summed over every category by the same aggregation. The
default filter therefore reads one partition, not 14.

**Cassandra DDL:**
```cql
CREATE TABLE gmv_by_minute (
  event_date    date,
  category_l1   text,
  window_start  timestamp,
  gmv           decimal,
  order_count   int,
  PRIMARY KEY ((event_date, category_l1), window_start)
) WITH CLUSTERING ORDER BY (window_start DESC);
```

**Response row fields:**

| Field | Type | Nullable | Units | Notes |
|---|---|---|---|---|
| `event_date` | `string` | No | — | `YYYY-MM-DD` |
| `category_l1` | `string` | No | — | The requested partition: a category, `"unknown"` for ~32.4% of events (no source `category_code`), or `"all"` |
| `window_start` | `string` | No | — | ISO 8601 with `+07:00` |
| `gmv` | `number` | No | Currency | Gross merchandise value |
| `order_count` | `integer` | No | Events | Purchase events in the window |

**Sorting:** `window_start DESC` (Cassandra cluster order).

**Rows:** at most 120 (`LIMIT 120`), and only those within 120 minutes of the
partition's newest window, so a sparse category never reaches back to the morning.

**Edge cases:** `category_l1 = "unknown"` is mandatory — it carries ~32.4% of all
revenue and must not be hidden. `gmv = 0` and `order_count = 0` rows may appear.
A minute with no row had no event at all; the screen draws it as 0.

**Empty result:** HTTP 200, `data: []`.

**Example response:**
```json
{
  "data": [
    { "event_date": "2019-11-17", "category_l1": "all", "window_start": "2019-11-17T20:29:00+07:00", "gmv": 5196.94, "order_count": 17 },
    { "event_date": "2019-11-17", "category_l1": "all", "window_start": "2019-11-17T20:28:00+07:00", "gmv": 4338.14, "order_count": 18 }
  ],
  "meta": { "ms": 6.5, "warehouse": "Cassandra", "partitions": 1, "rows": 2 }
}
```

---

## 4. BR2 — Conversion Funnel

**Business purpose:** Three-stage (View → Cart → Purchase) funnel showing where
customers drop off, with conversion rates. Supports date-range and category filters.

**Endpoint:** `GET /api/br2/funnel`

**Query parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `start_date` | `string` | No | `"2019-11-01"` | Inclusive start `YYYY-MM-DD` |
| `end_date` | `string` | No | `"2019-11-30"` | Inclusive end `YYYY-MM-DD` |
| `category_l1` | `string` | No | `"all"` | Category filter or `"all"` |

**Storage engine:** Parquet, read by DuckDB (`warehouse` stays `"Parquet"`, §2)

**Gold table:** `funnel_daily`, partitioned `event_date=YYYY-MM-DD/`, built by `batch_gold.py`

**Gold columns:**
```
event_date, category_l1, views, carts, purchases, cr_view_to_cart, cr_cart_to_purchase,
view_events, cart_events, purchase_events
```

The three `*_events` columns were added in W41 (Dat) so that gold carries both
measures the response needs: `views`/`carts`/`purchases` count **sessions** and
feed `session_count`; `*_events` count **raw events** and feed `count`. The
response fields did not change.

**Source:** `fact_session_funnel` for the `"all"` rows; for the category rows,
`fact_event` joined to `dim_product` by equality on the `product_sk` the fact
already carries (never a range join on the SCD2 validity dates).

**Source `funnel_stage` values:**
| Value | Meaning |
|---|---|
| `0` | Session has no recorded events (internal; not exposed in API; 0 rows measured) |
| `1` | Furthest milestone is `view` |
| `2` | Furthest milestone is `cart` |
| `3` | Furthest milestone is `purchase` (= conversion) |

**Definitions:**
- `event_date` is the day the **session started**, in Vietnam time (UTC+7).
- A session **reaches** a step when its `funnel_stage` is at least that step:
  view = `funnel_stage >= 1`, cart = `>= 2`, purchase = `= 3`. A purchase with no
  cart event therefore counts as reaching the cart, so session counts always
  decrease across the three steps. Event counts do not: on 1-7 Nov the source has
  more purchase events than cart events.
- For a category, the stage is the furthest step the session reached **on that
  category's products alone**. A session that touches two categories counts in
  both, so the category rows do not add up to `"all"`. `"all"` is a stored row per
  date, never a sum made by the API (as BR1's `"all"`).
- Over a date range the API **sums the counts** and recomputes the rates from the
  sums. It never averages `cr_view_to_cart` or `cr_cart_to_purchase`. Those two
  are per-day, per-category ratios kept for ad-hoc reads, `NULL` when the
  denominator is 0.
- `partitions` is the number of `event_date` directories inside the requested range.

**Response row fields** (3 rows per request, one per stage):

| Field | Type | Nullable | Notes |
|---|---|---|---|
| `step` | `"view" \| "cart" \| "purchase"` | No | Funnel stage |
| `count` | `integer` | No | Raw event count at this stage (`view_events` / `cart_events` / `purchase_events`) |
| `session_count` | `integer` | No | Sessions reaching this stage (`views` / `carts` / `purchases`) |
| `conversion_rate` | `number` | No | `session_count` / view `session_count`, rounded to 4 places (view = 1.0) |

**Sorting:** Fixed order: view, cart, purchase.

**Empty result:** HTTP 200, `data: []`. Also for a malformed date, `start_date`
after `end_date`, a range with no stored date, or an unknown `category_l1`.

**Example response** (the default request, measured 2026-10-07):
```json
{
  "data": [
    { "step": "view",     "count": 4451411, "session_count": 966143, "conversion_rate": 1.0 },
    { "step": "cart",     "count": 213486,  "session_count": 131498, "conversion_rate": 0.1361 },
    { "step": "purchase", "count": 64883,   "session_count": 54676,  "conversion_rate": 0.0566 }
  ],
  "meta": { "ms": 16.1, "warehouse": "Parquet", "partitions": 30, "rows": 3 }
}
```

---

## 5. BR3 — Trending Products

**Business purpose:** Top-20 products by view count in the current 15-minute
sliding window, ranked with arrows showing movement from the previous window.

**Endpoint:** `GET /api/br3/trending`

**Query parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `window_start` | `string` | No | Latest window | ISO 8601 timestamp |

**Storage engine:** Cassandra

**Gold table:** `trending_products`

**Cassandra DDL:**
```cql
CREATE TABLE trending_products (
  window_start  timestamp,
  rank          int,
  product_id    bigint,
  brand         text,
  category_l1   text,
  view_count    int,
  cart_count    int,
  PRIMARY KEY (window_start, rank)
);
```

**Note:** A `DELETE FROM trending_products WHERE window_start = ?` must precede
each insert to prevent stale rows (products may change rank between windows).

**Response row fields:**

| Field | Type | Nullable | Notes |
|---|---|---|---|
| `window_start` | `string` | No | ISO 8601 with `+07:00` |
| `rank` | `integer` | No | 1-based |
| `product_id` | `integer` | No | REES46 product identifier |
| `brand` | `string` | No | `"unknown"` when source brand is null (13.7% of rows) |
| `category_l1` | `string` | No | `"unknown"` when source `category_code` is null (32.4%) |
| `view_count` | `integer` | No | View events in the window |
| `cart_count` | `integer` | No | Cart events in the window |

**Sorting:** `rank ASC`.

**Empty result:** HTTP 200, `data: []`.

**Example response:**
```json
{
  "data": [
    { "window_start": "2019-11-29T14:00:00+07:00", "rank": 1, "product_id": 1005115, "brand": "samsung", "category_l1": "electronics", "view_count": 4821, "cart_count": 612 },
    { "window_start": "2019-11-29T14:00:00+07:00", "rank": 5, "product_id": 12714075, "brand": "unknown", "category_l1": "unknown", "view_count": 1876, "cart_count": 241 }
  ],
  "meta": { "ms": 8.7, "warehouse": "Cassandra", "partitions": 1, "rows": 2 }
}
```

---

## 6. BR4 — RFM Segmentation

**Business purpose:** 5×5 RFM heatmap of customer segments for marketing
prioritisation. Supports snapshot-date and segment filtering. Selecting a
cell shows the customers in that cell.

**Endpoint:** `GET /api/br4/segments`

**Query parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `snapshot_date` | `string` | No | `"2019-11-30"` | RFM snapshot date `YYYY-MM-DD` |
| `segment` | `string` | No | `"all"` | Segment filter or `"all"` |
| `r_score` | `integer` | No | — | Filter to R score (1–5) |
| `f_score` | `integer` | No | — | Filter to F score (1–5) |
| `m_score` | `integer` | No | — | Filter to M score (1–5) |

**Storage engine:** Parquet (future: DuckDB over Parquet)

**Gold table:** `rfm_segments`

**Gold columns:**
```
user_id, recency_days, frequency, monetary, r_score, f_score, m_score, segment
```
(partition column: `snapshot_date`)

**Source:** `dim_user WHERE is_current = true` (current SCD2 rows only)

**Response row fields:**

| Field | Type | Nullable | Notes |
|---|---|---|---|
| `user_id` | `integer` | No | REES46 user identifier |
| `snapshot_date` | `string` | No | `YYYY-MM-DD` |
| `recency_days` | `integer` | **Yes** | Days since last purchase; `null` if never purchased |
| `frequency` | `integer` | No | Total purchase event count |
| `monetary` | `number` | No | Total spend |
| `r_score` | `integer` | **Yes** | 1–5; `null` if never purchased |
| `f_score` | `integer` | **Yes** | 1–5; `null` if never purchased |
| `m_score` | `integer` | **Yes** | 1–5; `null` if never purchased |
| `rfm_cell` | `string` | **Yes** | 3-char e.g. `"545"`; `null` if never purchased |
| `segment` | `string` | No | See segment vocabulary below |

**Segment vocabulary (frozen):**
`champion`, `loyal`, `promising`, `needs_attention`, `at_risk`, `hibernating`, `no_purchase`

**Nullable handling:** Do NOT substitute `0` for `null`. ~88% of users at the first
snapshot have never purchased and have `null` RFM scores.

**Sorting:** `monetary DESC` (recommended).

**Empty result:** HTTP 200, `data: []`.

**Example response:**
```json
{
  "data": [
    { "user_id": 541312140, "snapshot_date": "2019-11-30", "recency_days": 1, "frequency": 48, "monetary": 22480.50, "r_score": 5, "f_score": 5, "m_score": 5, "rfm_cell": "555", "segment": "champion" },
    { "user_id": 609319077, "snapshot_date": "2019-11-30", "recency_days": null, "frequency": 0, "monetary": 0.0, "r_score": null, "f_score": null, "m_score": null, "rfm_cell": null, "segment": "no_purchase" }
  ],
  "meta": { "ms": 24.6, "warehouse": "Parquet", "partitions": 1, "rows": 2 }
}
```

---

## 7. BR5 — Abandoned Carts

**Business purpose:** CRM list of sessions that added items to cart but did not
purchase, sorted by cart value descending. Supports a simulated "create campaign"
action.

**Endpoint:** `GET /api/br5/carts`

**Query parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `event_date` | `string` | No | Latest date | Filter date `YYYY-MM-DD` |
| `min_value` | `number` | No | `0` | Minimum cart value filter |

**Storage engine:** Cassandra

**Gold table:** `abandoned_carts`

**Cassandra DDL:**
```cql
CREATE TABLE abandoned_carts (
  event_date    date,
  user_session  text,
  cart_value    decimal,
  user_id       bigint,
  item_count    int,
  last_event_at timestamp,
  PRIMARY KEY ((event_date), user_session)
);
```

**Key design note:** `cart_value` is intentionally *not* in the primary key.
This makes upserts idempotent — the same session always writes to the same row
regardless of how the cart value changes. The API layer sorts by `cart_value DESC`
because Cassandra cannot (the row is keyed only by `user_session`).

**Response row fields:**

| Field | Type | Nullable | Notes |
|---|---|---|---|
| `event_date` | `string` | No | `YYYY-MM-DD` |
| `user_session` | `string` | No | Session UUID |
| `cart_value` | `number` | No | Total cart value at last event |
| `user_id` | `integer` | No | REES46 user identifier |
| `item_count` | `integer` | No | Distinct items in cart |
| `last_event_at` | `string` | No | ISO 8601 with `+07:00` |

**Sorting:** `cart_value DESC` (API-layer sort, not Cassandra ordering).

**Empty result:** HTTP 200, `data: []`.

**Example response:**
```json
{
  "data": [
    { "event_date": "2019-11-29", "user_session": "9333dfbd-b87a-4708-9857-6336556a0fcc", "cart_value": 2489.07, "user_id": 541312140, "item_count": 3, "last_event_at": "2019-11-29T14:23:45+07:00" }
  ],
  "meta": { "ms": 11.2, "warehouse": "Cassandra", "partitions": 1, "rows": 1 }
}
```

---

## 8. BR6 — Stockout Risk

**Business purpose:** Inventory alert table showing SKUs ordered by days until
stockout, coloured red when < 3 days. Supports warehouse and threshold filtering.

**Endpoint:** `GET /api/br6/stockout`

**Query parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `warehouse_id` | `integer` | No | All warehouses | Filter to one warehouse (1–5) |
| `max_days` | `number` | No | — | Show only SKUs with `days_to_stockout ≤ max_days` |

**Storage engine:** Cassandra

**Gold table:** `stockout_risk`

**Source:** `fact_inventory_daily`

**Cassandra DDL:**
```cql
CREATE TABLE stockout_risk (
  warehouse_id      int,
  days_to_stockout  float,
  product_id        bigint,
  stock_on_hand     int,
  velocity_7d       float,
  PRIMARY KEY ((warehouse_id), days_to_stockout, product_id)
);
```

**Sentinel:** `days_to_stockout = 9999.0` means `velocity_7d = 0` (no recent sales).
Cassandra clustering columns cannot be null, so this sentinel substitutes for
the `NULL` that the star schema (`fact_inventory_daily`) stores honestly.

> ⚠️ **Semi-additivity warning** — `stock_on_hand` is semi-additive:
> - **Valid:** sum across warehouses on **one** date = total stock.
> - **Invalid:** sum across multiple dates = nonsense.
>
> BR6 must filter to a single snapshot date and may then aggregate across
> warehouses, but must **never** sum `stock_on_hand` across multiple dates.

**Response row fields:**

| Field | Type | Nullable | Notes |
|---|---|---|---|
| `warehouse_id` | `integer` | No | Natural key, 1–5 |
| `days_to_stockout` | `number` | No | `9999.0` = zero velocity (sentinel, **never** null) |
| `product_id` | `integer` | No | REES46 product identifier |
| `stock_on_hand` | `integer` | No | Units on hand (semi-additive) |
| `velocity_7d` | `number` | No | Avg daily units sold over 7 days; `0.0` when no sales |

**Sorting:** `days_to_stockout ASC` (Cassandra cluster order — most urgent first).

**Empty result:** HTTP 200, `data: []`.

**Example response:**
```json
{
  "data": [
    { "warehouse_id": 2, "days_to_stockout": 1.0,   "product_id": 5770048, "stock_on_hand": 4,   "velocity_7d": 4.0 },
    { "warehouse_id": 1, "days_to_stockout": 1.5,   "product_id": 1005115, "stock_on_hand": 3,   "velocity_7d": 2.0 },
    { "warehouse_id": 1, "days_to_stockout": 9999.0,"product_id": 12714075,"stock_on_hand": 250,  "velocity_7d": 0.0 }
  ],
  "meta": { "ms": 9.4, "warehouse": "Cassandra", "partitions": 2, "rows": 3 }
}
```

---

## 9. BR7 — Product Affinity

**Business purpose:** Given an anchor product, return up to 10 frequently
co-purchased products with their association statistics.

**Endpoint:** `GET /api/br7/affinity`

**Query parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `product_id` | `integer` | **Yes** | — | Anchor product identifier |
| `limit` | `integer` | No | `10` | Maximum related products to return (max 10) |

**Storage engine:** Parquet (future: DuckDB over Parquet)

**Gold table:** `product_affinity`

**Gold columns:**
```
product_a, product_b, co_count, support, lift
```

**Source:** `fact_event` (self-join over purchase sessions by `user_session`)

**Response row fields:**

| Field | Type | Nullable | Notes |
|---|---|---|---|
| `product_a` | `integer` | No | Anchor product identifier |
| `product_b` | `integer` | No | Related product identifier |
| `co_count` | `integer` | No | Sessions where both were purchased |
| `support` | `number` | No | Fraction of all purchase sessions containing both |
| `lift` | `number` | No | `co_count / (freq_a × freq_b / total_sessions)`. > 1 = positively associated. |

**Sorting:** `lift DESC`.

**Empty result:** HTTP 200, `data: []` (e.g. if anchor product has no co-purchases).

**Example response:**
```json
{
  "data": [
    { "product_a": 1005115, "product_b": 4804056, "co_count": 1243, "support": 0.0082, "lift": 4.72 },
    { "product_a": 1005115, "product_b": 5770048, "co_count": 987,  "support": 0.0065, "lift": 3.91 }
  ],
  "meta": { "ms": 31.7, "warehouse": "Parquet", "partitions": 1, "rows": 2 }
}
```

---

## 10. BR8 — Order Velocity Alerts

**Business purpose:** Risk alerts for users placing an abnormally high number
of orders within a 5-minute window. Timeline sorted newest first, expandable
to individual orders.

**Endpoint:** `GET /api/br8/alerts`

**Query parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `event_date` | `string` | No | Latest date | Filter date `YYYY-MM-DD` |
| `severity` | `string` | No | `"all"` | `"low"` \| `"medium"` \| `"high"` \| `"all"` |

**Storage engine:** Cassandra

**Gold table:** `order_velocity_alerts`

**Cassandra DDL:**
```cql
CREATE TABLE order_velocity_alerts (
  event_date    date,
  window_start  timestamp,
  user_id       bigint,
  order_count   int,
  total_value   decimal,
  severity      text,
  PRIMARY KEY ((event_date), window_start, user_id)
) WITH CLUSTERING ORDER BY (window_start DESC, user_id ASC);
```

**Severity vocabulary (frozen):**

| Value | Meaning |
|---|---|
| `"low"` | Within expected range |
| `"medium"` | Moderately above baseline |
| `"high"` | Flagged for manual review |

**Response row fields:**

| Field | Type | Nullable | Notes |
|---|---|---|---|
| `event_date` | `string` | No | `YYYY-MM-DD` |
| `window_start` | `string` | No | ISO 8601 with `+07:00` |
| `user_id` | `integer` | No | REES46 user identifier |
| `order_count` | `integer` | No | Purchase events in the 5-minute window |
| `total_value` | `number` | No | Sum of purchase values in the window |
| `severity` | `string` | No | `"low"` \| `"medium"` \| `"high"` |

**Sorting:** `window_start DESC, user_id ASC` (Cassandra cluster order).

**Empty result:** HTTP 200, `data: []`.

**Example response:**
```json
{
  "data": [
    { "event_date": "2019-11-29", "window_start": "2019-11-29T14:10:00+07:00", "user_id": 541312140, "order_count": 18, "total_value": 8920.50, "severity": "high" },
    { "event_date": "2019-11-29", "window_start": "2019-11-29T14:05:00+07:00", "user_id": 530253200, "order_count": 7,  "total_value": 3240.00, "severity": "medium" },
    { "event_date": "2019-11-29", "window_start": "2019-11-29T14:00:00+07:00", "user_id": 572756958, "order_count": 2,  "total_value": 640.50,  "severity": "low" }
  ],
  "meta": { "ms": 7.8, "warehouse": "Cassandra", "partitions": 1, "rows": 3 }
}
```

---

## 11. Fixture file locations

All eight canonical fixture bundles live in `web/fixtures/`:

```
web/fixtures/
├── br1-gmv-by-minute.json
├── br2-funnel-daily.json
├── br3-trending-products.json
├── br4-rfm-segments.json
├── br5-abandoned-carts.json
├── br6-stockout-risk.json
├── br7-product-affinity.json
└── br8-order-velocity-alerts.json
```

Each file contains two scenarios:

```json
{
  "default": { "data": [ ... ], "meta": { ... } },
  "empty":   { "data": [],      "meta": { ..., "rows": 0 } }
}
```

Run fixture validation:

```bash
python tests/test_fixtures.py
```

Besides the envelope, it checks the exact field set of each BR's default rows,
that each fixture's `meta.warehouse` is its §2 engine, and that each router's
`warehouse="..."` literal is `"Fixture"` or that engine.

---

## 12. How to implement a new BR screen

1. Identify your BR number (1–8) from this document.
2. Read the endpoint path, query parameters, and row field table.
3. Import the TypeScript row type from `web/src/types/api.ts`
   (e.g. `import type { ApiResponse, GmvRow } from '../types/api'`).
4. Load the fixture's `"default"` scenario in your page component for local development.
5. In the FastAPI router, import the Pydantic row model from `serving/api/models.py`.
6. Return `ApiResponse(data=..., meta=QueryMeta(...))` — never deviate from the envelope.
   While the router still serves fixture or placeholder data, `meta` is `warehouse="Fixture", partitions=0`;
   it becomes the §2 engine when the router queries its §2 store (§1.2).
7. Run `python tests/test_fixtures.py` to confirm your fixture is valid.
8. Run `cd web && npx tsc -b` (or `npm run build`) to confirm type-checking passes.

---

## 13. Discrepancies recorded during contract freeze (2026-09-20)

| # | Location | Documented | Actual | Resolution |
|---|---|---|---|---|
| 1 | `warehouse` casing | `"Cassandra"`, `"Parquet"` (task spec, capitals) | `"cassandra"`, `"parquet"`, `"fixture"` (lowercase) | Adopted capitalised enum; `"Fixture"` added as transitional value |
| 2 | BR2 fixture format | Bundled `{default, empty}` (task spec) | Two separate flat files (`br2-funnel.json`, `br2-funnel-empty.json`) | New bundled file `br2-funnel-daily.json`; BR2 router updated |
| 3 | `serving/cassandra_schema.cql` | Listed in SYSTEM_DESIGN.md §10 | File not present in repository | Not blocking; DDL reproduced in this document from §6 |
