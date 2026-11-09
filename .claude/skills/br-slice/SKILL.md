---
name: br-slice
description: Build one ShopInsight business requirement end to end — one Spark query, one API endpoint, one React screen, finished before the next BR starts. Use whenever a request names BR1..BR9, asks to start, finish, hand over or check a BR, or asks which store, table, route and screen a BR needs.
when_to_use: Triggers on "build BR4", "finish BR6", "is BR2 done", "what does BR7's screen show", "whose BR is BR8", "add the endpoint for BR3". Do NOT use for a generic batch Spark edit (use spark-job) or for Structured Streaming mechanics (use streaming-job).
---

# One BR = one slice, finished before the next starts

CLAUDE.md hard rule 6. A slice is **Spark query + API endpoint + React screen**, all
three done, for one BR. Never build all queries, then all endpoints. Grading counts
demonstrated BRs (~1 point each inside Application Implementation 8/10), and half a BR
in three layers counts zero.

As of W38 no application code exists. The first slice creates the files it needs;
do not assume any `processing/`, `serving/` or `web/` file is already there.

## 0. Whose BR is this

| BR | Question | Layer | Sink table | Owner | Screen |
|---|---|---|---|---|---|
| BR1 | GMV + order count per minute by category | streaming | `gmv_by_minute` (Cassandra) | Dat | Executive |
| BR2 | Funnel view -> cart -> purchase per session | batch | `gold/funnel_daily/` (Parquet) | Dat | Funnel |
| BR3 | Top-N trending products, 15-min sliding | streaming | `trending_products` (Cassandra) | Khang | Trending |
| BR4 | RFM customer segmentation | batch | `gold/rfm_segments/` (Parquet) | Khang | Segments |
| BR5 | Abandoned cart detection | streaming | `abandoned_carts` (Cassandra) | Nguyen | Abandoned carts |
| BR6 | Stock-out risk per SKU and warehouse | **batch** | `stockout_risk` (Cassandra) | Tin | Inventory alerts |
| BR7 | Frequently bought together | batch | `gold/product_affinity/` (Parquet) | Nguyen | Affinity |
| BR8 | Order velocity anomaly detection | streaming | `order_velocity_alerts` (Cassandra) | Tin | Anomalies |
| BR9 | Ad-hoc product lookup (bonus, **cut**) | batch | Parquet star | — | Ad-hoc lookup |

BR6 is batch even though it sinks to Cassandra. If the BR is not yours, do not build it.

**No week numbers here on purpose.** `PLAN.md` is the schedule of record — check the week
table and the tracker there, not a skill. Week data drifted across five copies once
already.

**BR9 is cut** (PLAN.md and CLAUDE.md agree since 2026-09-16). Do not build it unless the
team reinstates it in PLAN.md first.

## 1. Copy the right reference

- Streaming BR (BR1, BR3, BR5, BR8): copy Dat's BR1 pattern. BR1 is built a full week
  before the other three specifically so they copy its frame. Read the `streaming-job`
  skill before touching `readStream`, `foreachBatch` or a Cassandra write.
- Batch BR (BR2, BR4, BR6, BR7, BR9): read the `spark-job` skill. Batch gold reads the
  **star** in `data/warehouse/`, never silver.

## 2. Spark query

Batch BR, in order:
1. Read the star from `data/warehouse/`: `fact_session_funnel` for BR2 (its category rows through `fact_event` + `dim_product`
   on `product_sk`), `dim_user`
   where `is_current` for BR4, `fact_inventory_daily` + `dim_warehouse` for BR6,
   `fact_event` for BR7 (self-join purchases grouped by `user_session`).
2. Aggregate to exactly the columns the screen prints — nothing wider.
3. Write Parquet gold (BR2/BR4/BR7/BR9) or, for BR6 only, project to Cassandra:
   `when(velocity_7d > 0, stock_on_hand/velocity_7d).otherwise(9999.0)`, then
   `DELETE FROM stockout_risk WHERE warehouse_id = ?` before inserting each warehouse
   (stale-row table below; the reasoning is in `streaming-job` section 4).
4. Print the output row count. That number goes in the group chat.

Streaming BR, in order:
1. Read silver-shaped events from `data/stream_landing/` with `EVENT_SCHEMA` passed
   explicitly. Streaming BRs do **not** read the star — a micro-batch cannot range-join
   an SCD2 dimension rebuilt nightly.
2. Apply the same seven silver cleaning rules inside the micro-batch, UTC+7 shift included:
   import `clean()` from `processing/batch_silver.py`.
3. `withWatermark("event_time", "10 minutes")`, then the window: 1-minute (BR1),
   15-minute sliding every minute (BR3), 30-minute cart threshold (BR5), 5-minute (BR8).
4. Write from `foreachBatch` with the plain `cassandra-driver`, checkpoint under
   `data/checkpoints/<job_name>/`, and apply that table's stale-row rule — the
   `streaming-job` skill, section 4 (SYSTEM_DESIGN 6.1).

## 3. API endpoint

One router per BR under `serving/api/`. Route shape: `/api/br<N>/<noun>` with the
screen's filters as query parameters, returning `{ "rows": [...], "meta": {...} }`.
The API contract that freezes the gold column names and ships JSON fixtures — so a
screen can be built before its query exists — is a **W38 deliverable, owner Tin**.
Checked 2026-09-16: `serving/` does not exist yet, so there is no contract and no
fixture to read. Until Tin lands it, take column names from SYSTEM_DESIGN section 7
(Parquet gold) or section 6 (Cassandra) and do not invent your own; once it exists, use it and do not rename columns.

- **BR1, BR3, BR5, BR6, BR8 hit Cassandra on the partition key.** Every query names the
  full partition key: `(event_date, category_l1)` for BR1, `window_start` for BR3,
  `event_date` for BR5 and BR8, `warehouse_id` for BR6. A filter that is not the
  partition key is not expressible — redesign the key backwards from the screen instead.
  One deliberate exception, BR3's default view: no key says which window is newest,
  because Cassandra orders rows inside a partition, never partitions. So without
  `window_start` the endpoint lists the keys (`SELECT DISTINCT window_start`, keys only)
  and reads the largest, and `meta.partitions` counts every key listed. Measured at a
  full month of windows: 346 ms (#19).
  BR5 sorts by `cart_value` **in the API**, because the key change to
  `((event_date), user_session)` gave up on-disk ordering to get idempotent upserts.
- **BR2, BR4, BR7, BR9 let DuckDB read Parquet directly** from `data/gold/` (BR9 from
  `data/warehouse/`). No load step, no Postgres — Postgres is the benchmark tier only.
- The response `meta` carries `elapsed_ms`, `store` (`cassandra` | `duckdb`),
  `partitions_read` and `row_count`. The endpoint measures these; the screen only prints.

## 4. React screen

| BR | Components | Filters |
|---|---|---|
| BR1 | four metric cards + GMV line chart, last 60 minutes, refresh every 10s | date, category |
| BR2 | three-stage funnel chart + conversion rate table by category | date range, category |
| BR3 | top 20 table with rank-change arrows vs the previous window | time window |
| BR4 | 5x5 RFM heatmap + customer list for the selected cell | snapshot date, segment |
| BR5 | list sorted by cart value descending + simulated "create campaign" action | date, value threshold |
| BR6 | SKU table coloured by days remaining, red under 3 days | warehouse, day threshold |
| BR7 | product search box, then 10 related products with lift scores | anchor product |
| BR8 | alert timeline by severity, expandable to the underlying orders | date, severity |

BR6's screen aggregates across warehouses and **filters** to one day. `stock_on_hand` is
semi-additive: summing it over a date range is nonsense.

## 5. Last step, non-negotiable

Every screen renders its own footer, exactly like the executive sketch:

```
Query: 43 ms · Cassandra · 1 partition · 60 rows
```

This is not decoration. It is the live evidence the report's evaluation section and the
Gate 2b "<2s per screen" measurement both rely on, and a grader reads it without opening
the report. A screen without the QueryMeta footer is not finished.

## Done when

A different person can check all five, with no help from the owner:

- [ ] the Spark query runs standalone and prints its output row count
- [ ] the endpoint returns rows for the screen's default filters (Cassandra on the
      partition key, or DuckDB over Parquet — never a full-table scan)
- [ ] the React screen renders those rows with its filters working
- [ ] the QueryMeta footer shows query time, store, partitions read and row count
- [ ] the owner has posted the row count (and a screenshot for the gate) to the group chat
