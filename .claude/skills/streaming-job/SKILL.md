---
name: streaming-job
description: Trap list and checklist for writing or changing a Structured Streaming query in ShopInsight — processing/streaming_gold.py, BR1/BR3/BR5/BR8, the replayer, micro-batch cleaning, watermarks, checkpoints, and Cassandra writes from foreachBatch including the three different stale-row fixes.
when_to_use: Triggers on readStream, writeStream, foreachBatch, micro-batch, watermark, checkpointLocation, stream_landing, replayer, trigger interval, or any work on BR1, BR3, BR5, BR8. Do NOT use for batch scripts (use spark-job) or for wiring an endpoint and screen (use br-slice).
---

# Structured Streaming — the densest trap list in the project

BR1 (Dat, W40) is the reference. BR3, BR5 and BR8 (W41) copy its frame. No streaming code
exists yet in W38; the first job sets the pattern the other three inherit.

## 1. Starting the stream

- [ ] Pass the schema explicitly. Structured Streaming **cannot infer schema**:
      `readStream.format("json").schema(EVENT_SCHEMA).load("data/stream_landing/")`.
      Without it the query never starts. `EVENT_SCHEMA` is imported from
      `processing/schema.py`, never re-declared inline.
- [ ] Every `writeStream` sets `checkpointLocation` at `data/checkpoints/<job_name>/`.
      Without it all state is lost on restart and the job reprocesses from zero.
- [ ] One checkpoint directory per query. Four aggregations means four checkpoints.
- [ ] **Start the streaming job BEFORE the replayer.** Start it after and the files
      already sitting in `data/stream_landing/` collapse into one huge micro-batch, which
      looks nothing like real time during a demo. Terminal 1:
      `python processing/streaming_gold.py`, let it wait. Terminal 2:
      `python ingestion/replayer.py --speed 60`.
- [ ] The replayer reads `data/bronze/` (Parquet), never the raw CSV: raw holds all
      3,696,117 users, bronze only the 258,088 in the 7% bucket, so pointing at raw feeds
      a 14x larger population and the >=99% correctness gate becomes unreachable.

## 2. Inside the micro-batch

- [ ] Apply **the same six silver cleaning rules**, UTC+7 shift included, and recompute
      `event_date` from the shifted time. The shift is easy to omit because the rules were
      written for `batch_silver.py`; omit it and `gmv_by_minute.event_date` is UTC while
      `funnel_daily.event_date` is UTC+7, so two screens disagree about which day a
      17:00-24:00 UTC event belongs to.
- [ ] Rule 4 matters most here: fill `category_l1/l2/l3` with `'unknown'`. It is half the
      partition key of `gmv_by_minute`, and 32.4% of source rows have an empty
      `category_code` — without the fill one BR1 insert in three fails.
- [ ] `withWatermark("event_time", "10 minutes")` before any windowed aggregation, so old
      state can be dropped. No watermark means state grows until the JVM dies.
- [ ] Windows per BR: 1 minute (BR1), 15 minutes sliding every minute (BR3), 30-minute
      no-purchase-after-cart threshold (BR5), 5 minutes (BR8).
- [ ] **Structured Streaming cannot rank a streaming DataFrame.** BR3's ordering and
      top-N cut happen inside `foreachBatch`, where the micro-batch is an ordinary static
      DataFrame — not with a window function on the stream.

## 3. Writing to Cassandra

- [ ] Write from `foreachBatch` using the plain Python `cassandra-driver`. The
      Spark-Cassandra connector is banned (hard rule 2) — it drags in the Scala and jar
      version matching this project exists to sidestep.
- [ ] Use prepared statements and a batch per partition key. Every write names the full
      partition key, because that is the only thing Cassandra can filter on.
- [ ] Keys are designed backwards from the screen's question. All five live in one
      place — the `cassandra-table` skill's table, copied from SYSTEM_DESIGN section 6.
      Read the key there and copy it; do not retype one from memory, and never fold a
      clustering direction into the `PRIMARY KEY` expression — `DESC`/`ASC` belong to the
      separate `WITH CLUSTERING ORDER BY` clause, which only BR1 and BR8 have.

## 4. Three tables leave stale rows. Three different fixes.

**This section is the single full home of the three strategies.** SYSTEM_DESIGN 6.1 is
the design-side source; every other file in `.claude/` carries only a one-line pointer
here, so a revision in W40-W41 is one edit, not seven. Keep it that way.
`.claude/hooks/check_python.py` warns (advisory, never blocks) when an insert into
`trending_products` or `stockout_risk` has no matching DELETE, or anything deletes from
`abandoned_carts`. A warning is a prompt to check, not proof of correctness.

A table that clusters on a value which changes between runs gets a *new* row from an
upsert instead of replacing the old one — on screen, duplicates or a self-emptying list.

| Table | Written by | Fix |
|---|---|---|
| `stockout_risk` | batch (BR6), full rewrite of every warehouse | `DELETE FROM stockout_risk WHERE warehouse_id = ?` then insert |
| `trending_products` | streaming (BR3), re-emits each window | `DELETE FROM trending_products WHERE window_start = ?` then insert the new top-N |
| `abandoned_carts` | streaming (BR5), accumulates through the day | **no delete at all** |

Why each differs:

- `stockout_risk` clusters on `days_to_stockout`, which changes every run, so an old row
  survives beside the new one. The batch rewrites a whole warehouse, so deleting that
  partition first is exactly right.
- `trending_products` has the same bug: a product at rank 3 in one emission and rank 5 in
  the next leaves two live rows and `LIMIT 20` returns it twice. Here the partition *is*
  one window, so deleting the partition is exactly right too.
- `abandoned_carts` is the opposite case. It is streaming and accumulates all day, so
  `DELETE WHERE event_date = ?` inside `foreachBatch` would erase every cart found in
  earlier micro-batches — the BR5 screen would show only the last micro-batch and would
  visibly empty itself mid-demo. Deleting one session's row is not expressible against
  `((event_date), cart_value, user_session)` either: Cassandra deletes by a clustering
  prefix, so it would need the session's *previous* `cart_value` — exactly the value that
  changed. Hence `((event_date), user_session)` with `cart_value` as a plain column, which
  makes the upsert idempotent and needs no delete. Accepted cost: rows are no longer
  sorted by cart value, so "the 50 highest-value carts today" is a partition read plus an
  in-API sort of at most a few thousand rows. State the trade in the report.

## 5. Nulls Cassandra rejects

- [ ] `days_to_stockout` is a clustering column and must never be null.
      `stock_on_hand / velocity_7d` is null whenever `velocity_7d` is 0, which is ~90% of
      SKUs, so use `when(velocity_7d > 0, stock_on_hand/velocity_7d).otherwise(9999.0)`.
      Without the sentinel nine inserts in ten fail. The star stores the honest NULL; only
      the Cassandra projection substitutes the sentinel.
- [ ] `category_l1` is half a partition key and cannot be null — see rule 4 above.

## 6. The streaming job writes NOTHING to silver

Its only outputs are the Cassandra gold tables.

- A Parquet file sink on silver creates `data/silver/_spark_metadata/`, after which
  `spark.read.parquet("data/silver")` reads only files listed in that log — every file
  `batch_silver.py` wrote goes invisible to Spark while DuckDB and the Postgres loader
  still glob the whole directory, so the two disagree and the correctness gate is void.
- Writing silver through `foreachBatch` is no better: the replayer replays bronze, which
  `batch_silver.py` has already turned into silver, so a second demo run duplicates rows —
  inflating BR2's funnel and BR7's co-occurrence counts and shifting BR4's recency.

## 7. Before calling it done

- [ ] Screenshot of the micro-batch log plus rows in the target Cassandra table, posted
      to the group chat. That is the Gate 1 artefact; no one claims "it works" without it.
- [ ] Restart the job once and confirm it resumes from the checkpoint instead of replaying.
- [ ] Run the demo twice end to end and confirm the screen does not duplicate or empty.
