---
name: cassandra-table
description: Design, create or change a Cassandra gold table in ShopInsight — choosing the partition and clustering key backwards from the screen's question, editing the CQL schema, and diagnosing a screen that shows duplicates or empties itself mid-demo.
when_to_use: Picking a PRIMARY KEY for a BR that sinks to Cassandra (BR1, BR3, BR5, BR6, BR8); adding or editing a CREATE TABLE in the Cassandra schema; a query the driver refuses because it does not go through the partition key; duplicated SKUs or duplicated products on a screen; a list that empties itself between micro-batches; a null partition-key or clustering-key error on insert; writing the report paragraph that contrasts Cassandra keys with the star schema.
---

## The governing idea

Cassandra cannot filter arbitrarily. Every read goes through the partition key,
so the key is designed **backwards from the question the screen asks**, never
forwards from the data. One table answers exactly one question. A second
question costs a new table and a new write path, not a new `WHERE` clause.
A key designed forwards produces a query that cannot be expressed at all.

The star schema is the opposite, and the report has to make exactly this
contrast (SYSTEM_DESIGN 5.2):

| | Star (Parquet / Postgres) | Cassandra gold |
|---|---|---|
| Design driven by | the grain of the business process | the query the screen issues |
| One table answers | many questions, by joining whichever dimensions it needs | exactly one |
| Adding a question costs | a new query | a new table and a new write path |

## The five current tables

Both columns are CQL, copied verbatim from SYSTEM_DESIGN section 6. The key
expression goes inside the table body; the clustering clause goes after the
closing `)`.

| Table | BR | PRIMARY KEY (inside the body) | Clause after the body | Why this key |
|---|---|---|---|---|
| `gmv_by_minute` | BR1 | `PRIMARY KEY ((event_date, category_l1), window_start)` | `WITH CLUSTERING ORDER BY (window_start DESC)` | The screen always filters date + category; DESC clustering makes "the last 60 minutes" 60 adjacent rows at the head of one partition, with no sort step |
| `trending_products` | BR3 | `PRIMARY KEY (window_start, rank)` | none — default ASC | One window is one partition; reading a top-20 is one partition scan already in rank order |
| `abandoned_carts` | BR5 | `PRIMARY KEY ((event_date), user_session)` | none — default ASC | Session is the identity of the row, so the upsert is idempotent; `cart_value` is a plain column |
| `stockout_risk` | BR6 | `PRIMARY KEY ((warehouse_id), days_to_stockout, product_id)` | none — default ASC | The screen picks one warehouse; `days_to_stockout` ascending puts the most urgent SKU first |
| `order_velocity_alerts` | BR8 | `PRIMARY KEY ((event_date), window_start, user_id)` | `WITH CLUSTERING ORDER BY (window_start DESC, user_id ASC)` | One day per partition, newest alerts first |

**Clustering direction is never part of the key expression.** `PRIMARY KEY
((event_date, category_l1), window_start DESC)` does not parse — CQL rejects it
at `DESC`. Direction lives only in the separate `WITH CLUSTERING ORDER BY (...)`
clause, and only two of the five tables have one. Three take the default ASC and
must not be given a clause they do not have in section 6.

## Checklist for a new or changed table

1. **Which single screen question does this answer?** If the answer is "two
   questions", it is two tables.
2. **What does the screen filter on?** That is the partition key. Nothing else
   can be filtered without a full-cluster scan.
3. **What order does the screen want?** That is the clustering key — column
   names in the PRIMARY KEY, direction in `WITH CLUSTERING ORDER BY` if the
   default ASC is wrong.
4. **Is any key column ever null in the source?** Cassandra rejects a null
   partition-key part outright, and rejects null clustering keys.
   `category_l1` is empty in 32.4% of raw rows — silver fills `'unknown'`, and
   without it one BR1 insert in three fails.
   `stock_on_hand / velocity_7d` is null whenever `velocity_7d` is 0, ~90% of
   SKUs — use `when(velocity_7d > 0, ...).otherwise(9999.0)`. If a sentinel is
   substituted, the report must say so and say what it excludes.
5. **Does a clustering value change between runs?** Then the upsert writes a
   second live row instead of replacing the first. Three tables do
   (`stockout_risk`, `trending_products`, `abandoned_carts`), each with a different
   fix — and why `cart_value` left the BR5 key — in the `streaming-job` skill,
   section 4, and SYSTEM_DESIGN 6.1. Not restated here: it may be revised in
   W40-W41, and one copy is the point.
6. **Is the write idempotent across a second demo run?** Run the pipeline twice
   and read the screen. Same rows, not double.

Writes go through `foreachBatch` plus the plain Python `cassandra-driver`. The
Spark-Cassandra connector is banned (CLAUDE.md rule 2).

## Where the CQL file is

`serving/cassandra_schema.cql` (all five `CREATE TABLE`s) and
`serving/apply_schema.py` are **W38 deliverables, owner Nguyen** — PLAN.md gives
him the Cassandra schema, and its W39 row "photograph the 5 Cassandra tables"
is priced assuming the `.cql` was paid for in W38.

Checked 2026-09-16: `serving/` does not exist. Until it does, new CQL goes into
SYSTEM_DESIGN section 6 and the files stay with their owner. Do not create a
partial `serving/` tree as a side effect of another task.
