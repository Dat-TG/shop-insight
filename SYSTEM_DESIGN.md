# ShopInsight — System Design

## 1. Architecture

```
   REES46 event log      Product catalogue    Holiday calendar   Inventory
   2019-Nov.csv          (JSON, generated)    (CSV, committed)   (generated)
   67.5M rows, 9.0 GB          |                     |               |
           |                   |                     |               |
           v                   |                     |               |
   [1] load_bronze.py          |                     |               |
       7% user sample          |                     |               |
           |                   |                     |               |
           v                   |                     |               |
   [2] batch_silver.py         |                     |               |
       clean + UTC+7           |                     |               |
           |                   |                     |               |
           +---------+---------+---------------------+---------------+
                     |                                       |
                     v                                       |
   [3] batch_warehouse.py — STAR SCHEMA                       |
       5 conformed dimensions + 3 facts                       |
       written twice: Parquet (primary) and Postgres          |
                     |                                       |
           +---------+---------+                             |
           |                   |                             |
           v                   v                             v
   [4] batch_gold.py     Spark streaming (silver-shaped, NOT from the star)
       BR2 BR4 BR6 BR7   BR1 BR3 BR5 BR8
           |                   |
           v                   v
   [5] Parquet gold      Cassandra gold tables
           |                   |
           +---------+---------+
                     v
   [6] FastAPI — routes each BR to its store
                     |
                     v
   [7] React dashboard — 8 screens (+ BR9 bonus)

   Comparison tier (runs alongside, benchmark only):
   DuckDB on the Parquet star  vs  PostgreSQL on the same star
   plus PostgreSQL on a flat silver table (index techniques)
```

The warehouse layer at [3] is the new stage. Before it, silver went straight to
gold and every BR re-derived its own joins from raw-ish event rows. Now the
conformed dimensions are built once and every batch BR reads them.

**One thing the layer does not do.** The streaming BRs (BR1, BR3, BR5, BR8)
still read silver-shaped events, not the star. A Spark micro-batch cannot
range-join a Type 2 dimension that is rebuilt by a nightly batch without either
broadcasting the whole dimension into the stream or rewriting the streaming path
— neither fits the hour budget. Of the five Cassandra tables only `stockout_risk`
(BR6, batch) is genuinely derived from the star. `fact_event` is the *analytical*
re-materialisation of the same events: it is what the benchmark, the report and
BR9 query, and what proves the streaming numbers are right. Section 8 walks
through both paths.

## 2. User groups

| Group | Questions they ask daily | BRs |
|---|---|---|
| Executives | How is revenue tracking against the last hour? Which category is driving it? | BR1 |
| Growth & Marketing | Where do customers drop out of the funnel? Which segment deserves ad spend? Who abandoned a cart? | BR2, BR4, BR5 |
| Merchandising | Which products are rising? What sells alongside product A? | BR3, BR7, BR9 |
| Operations & Risk | Which SKUs are about to run out? Which accounts order abnormally? | BR6, BR8 |

## 3. Source data

Four sources. One is downloaded, one is committed, two are generated.

### 3.1 Event log (downloaded)

REES46 "eCommerce behavior data from multi category store" (Kaggle). Use
`2019-Nov.csv`, 67,501,979 rows covering 1–30 November, and sample it down to
~4.77M by taking **7% of `user_id` values across the whole month** — never the
first 5M rows. The first 5M rows are about two days of November, which leaves
BR4's recency meaningless and BR6's `velocity_7d` with fewer than seven days to
average over.

The sampling rule is `pmod(hash(user_id), 100) < 7`, hard-coded in
`load_bronze.py`. It must be deterministic — never a random seed — so all four
machines produce byte-identical datasets. Measured with Spark 4.1.3
(`load_bronze.py`): **4,767,012 rows, 258,390 distinct users, 129,899 distinct
products, 30 dates**. An independent Python copy of Spark's Murmur3 `hash()`
gives the same three numbers. `user_id` must be read as BIGINT: `hash()` of an
INT selects a different sample (4,713,498 rows, only 18,150 users shared).

**Counts derived from the sample elsewhere in this document were measured on an
earlier sample**, drawn with a different hash function (4,694,166 rows / 258,088
users / 127,693 products). That covers the star row counts in section 5, the SCD2
version counts, the 12,659 purchased SKUs and the range-join size, but not
`fact_event`, re-measured on Spark's sample by `batch_warehouse.py` (4,754,015 rows,
1:1 with silver). Expect the others to move slightly; each is re-measured as
`batch_warehouse.py` builds its table.

```
event_time      timestamp   2019-11-01 00:00:12 UTC
event_type      string      view | cart | purchase   (remove_from_cart: documented, 0 rows in this file)
product_id      bigint      44600062
category_id     bigint      2103807459595387724
category_code   string      electronics.smartphone      (NULL in 32.4% of rows)
brand           string      samsung                     (NULL in 14.9% of rows)
price           decimal     489.07
user_id         bigint      541312140
user_session    string      9333dfbd-b87a-4708-9857-6336556a0fcc
```

Both null rates are measured on the real file, not estimated. `category_code`
being null one row in three is load-bearing — see the silver rules in section 4.

**A 38-hour hole with no purchases.** The file has no `purchase` event from
14 Nov 18:09:37 UTC to 16 Nov 08:32:34 UTC (15 Nov 01:09 to 16 Nov 15:32 Vietnam
time), and none at all on 15 Nov UTC, while views and carts carry on at normal
volume. It is in the source, not a pipeline bug. In silver (Vietnam dates) 15 Nov
has 170 purchases against 35,812 carts. Three screens will show it: BR2's funnel
for 15 Nov converts at almost zero, BR1's GMV is flat for those hours, and BR8's
velocity detection reacts to it. Say so in the report instead of filtering it out.
Measured on the full file with
`awk -F, '$2=="purchase" && $1>="2019-11-14" && $1<"2019-11-17"'` (last before, first
after), and per Vietnam date with a `groupBy("event_date").pivot("event_type")` on
silver.

### 3.2 Holiday calendar (committed to git)

`seed/holidays_2019.csv`. This is the one new artefact that must travel through
git: it is authored, not derived, so there is no deterministic rule that
regenerates it the way `pmod(hash(user_id), 100) < 7` regenerates the sample. It
lives in `seed/` and **not** under `data/`, because `.gitignore` excludes every
child of `data/` and a teammate adding `data/raw/holidays_2019.csv` would be
silently ignored — the file would never reach the other three machines and
`dim_date.is_holiday` would differ per laptop.

```csv
holiday_date,holiday_name,holiday_type
2019-11-11,Singles Day,retail_event
2019-11-29,Black Friday,retail_event
2019-12-02,Cyber Monday,retail_event
```

`holiday_type` is one of `public_holiday`, `retail_event`, `promo_period`,
`observance`. For this dataset the retail events matter far more than national
holidays: Black Friday falls inside the November window and is the single
largest demand signal in the file. No Vietnamese public holiday falls between
1 October and 31 December 2019, so the file has none. Every date in it must fall
inside `dim_date` (2019-10-01 .. 2019-12-31); `serving/load_star_postgres.py`
checks that.

### 3.3 Product catalogue (generated)

`ingestion/gen_catalog.py` reads the distinct `product_id` values that survive
the sample and emits `data/catalog/products.json` — a synthetic specification
document per product, keyed on the real product ids. It is documented as
synthetic in the report.

```json
{"product_id": 1005115,
 "attributes": {
   "color": "space_grey",
   "weight_grams": 189,
   "warranty_months": 24,
   "dimensions": {"length_mm": 147, "width_mm": 72, "depth_mm": 8},
   "tags": ["flagship", "5g"],
   "specs": {"screen_inches": 6.1, "battery_mah": 3110}
 }}
```

The nesting is the point: it becomes a `jsonb` column with a GIN index in
Postgres and a nested `struct` in Parquet, which is the clearest side-by-side
physical-design contrast in the whole project. Generation is deterministic —
attributes are derived from `product_id` by a fixed hash, never a random seed.

### 3.4 Inventory (generated)

`ingestion/gen_inventory.py` emits a **daily series**, not a single snapshot:
one row per stocked SKU per warehouse per day. See `fact_inventory_daily` in
section 5.5 for the grain and the row count.

```
product_id      bigint
warehouse_id    int         1..5
snapshot_date   date
stock_on_hand   int
reorder_point   int
units_received  int
```

## 4. Four data tiers

| Tier | Contents | Layout |
|---|---|---|
| Bronze | Raw events, untouched. The reference copy when a number looks wrong | Parquet, partitioned by `event_date` |
| Silver | Cleaned and enriched (rules below) | Parquet, partitioned by `event_date` then `event_type` |
| **Warehouse** | **The star schema: 5 conformed dimensions, 3 facts. Built once, read by every batch BR** | **Parquet (primary) + PostgreSQL (same logical model, second physical realisation)** |
| Gold | Pre-aggregated tables, one per BR. This is what the application actually reads | Cassandra (real-time) or Parquet (analytical) |

Silver cleaning rules:

1. Drop `price <= 0`
2. Drop null `user_id`
3. Split `category_code` into `category_l1/l2/l3`
4. **Fill missing `category_l1/l2/l3` with `'unknown'`** — see below
5. Fill missing `brand` with `'unknown'`
6. Shift `event_time` to UTC+7 **and recompute `event_date` from the shifted
   time**. Keeping the old date misfiles every event between 17:00 and 24:00 UTC
   and skews BR1, BR2 and BR6.
7. Drop null `user_session`. One row in the sample (a cart event, 29 Nov 17:25 UTC) has
   none; `fact_event.user_session` is `NOT NULL` and `user_session` is the
   clustering key of BR5's `abandoned_carts`, which Cassandra rejects null.

The seven rules live in one function, `clean()` in `batch_silver.py`, which the
streaming job imports rather than copies (section 8, step 7). Measured on the
sample: 4,767,012 bronze rows become **4,754,015 silver rows** (12,996 with
`price <= 0`, none with a null `user_id`, 1 with a null `user_session`).

Rule 6 gives silver **31 date directories, 2019-11-01 .. 2019-12-01**, where bronze
has 30. The file ends at 30 Nov 23:59 UTC, which is 1 Dec 06:59 in Vietnam, so the
25,859 events of 30 Nov 17:00–24:00 UTC belong to a partial 1 Dec, just as 1 Nov
starts at 07:00. They are kept: dropping them would make silver differ from
bronze by more than the rules, and the stream, which replays bronze, would need
the same cut. In bronze, 31 directories means a wrong time zone; in silver, 30
means rule 6 is missing.

Rule 4 is not cosmetic. `category_l1` is half the partition key of
`gmv_by_minute`, and Cassandra rejects a null partition-key component outright
(`Invalid null value for partition key part category_l1`). 32.4% of source rows
have an empty `category_code`, so without rule 4 one BR1 insert in three fails
and the executive screen understates GMV by roughly a third. The consequence is
worth stating in the report rather than hiding: BR1's GMV carries an `unknown`
series holding about a third of all events.

Silver is partitioned by `event_type` because most queries care about one event
type only, so Spark skips whole directories without opening a file. That is
*partition pruning*, one of the techniques covered in the presentation.

**Silver has exactly one writer: `batch_silver.py`.** The streaming job does not
append to it. This is a change from the earlier design, and the reason is in
section 8.

## 5. The dimensional model

The report presents this at three levels. This section is the source for all
three.

### 5.1 Conceptual — entities and relationships

```
   +----------+          +-----------+          +-----------+
   |   USER   |---------<|  SESSION  |>---------|   EVENT   |
   +----------+  1    n  +-----------+  1    n  +-----------+
                                                      |  n
                                                      |
                                                      v  1
   +-----------+          +-----------+          +-----------+
   | WAREHOUSE |---------<| INVENTORY |>---------|  PRODUCT  |
   +-----------+  1    n  +-----------+  n    1  +-----------+

   A USER opens many SESSIONS. A SESSION contains many EVENTS.
   Each EVENT concerns exactly one PRODUCT.
   INVENTORY records the stock of one PRODUCT in one WAREHOUSE on one day.
```

### 5.2 Logical — the star, and the contrast with Cassandra

Three facts, one per Kimball fact type, sharing five conformed dimensions:

```
                          dim_date
                             |
        dim_user ---- fact_event ---- dim_product
                             |             |
                       dim_event_type      |
                                           |
        dim_user -- fact_session_funnel ---+
                                           |
   dim_warehouse -- fact_inventory_daily --+
                             |
                          dim_date
```

| | fact_event | fact_session_funnel | fact_inventory_daily |
|---|---|---|---|
| Kimball type | Transaction | Accumulating snapshot | Periodic snapshot |
| Grain | one user event | one session | one SKU × warehouse × day |
| Rows (measured) | 4,754,015 | 954,686 | 1,898,850 |
| Measures | `price` | milestone lags, counts, values | stock, velocity, days to stock-out |
| Degenerate dim | `user_session` | — | — |
| Serves | BR1, BR3, BR8 | BR2, BR5 | BR6 |

**The contrast the report has to make.** The star schema is *normalised around a
grain and queried many ways*: one `fact_event` answers BR1, BR3, BR8, BR9 and
every ad-hoc question, by joining whichever dimensions the question needs. The
Cassandra model is the opposite — *one table per question, keyed backwards from
the screen*. `gmv_by_minute` cannot answer BR3 and `trending_products` cannot
answer BR1, because neither has a key that supports the other's filter. That is
not a defect in Cassandra; it is the trade the design makes deliberately, and
measuring both is what section 12 exists for.

| | Star (Parquet / Postgres) | Cassandra gold |
|---|---|---|
| Design driven by | the grain of the business process | the query the screen issues |
| One table answers | many questions | exactly one |
| Adding a question costs | a new query | a new table and a new write path |
| Joins | yes, that is the point | none, ever |
| Filter freedom | any column | partition key first, always |

### 5.3 Physical — what differs between the two realisations

| | Parquet (primary) | PostgreSQL (mirror) |
|---|---|---|
| Partitioning | directory partitions on `event_date` / `snapshot_date` | declarative `PARTITION BY RANGE (event_date)` / `LIST (warehouse_id)` |
| Row-group pruning | min/max statistics per row group | BRIN on the same column |
| Point lookups | none — full column scan | B-tree |
| Nested data | `struct` column, read a leaf without the rest | `jsonb` + GIN |
| Compression | snappy (zstd measured as an alternative) | TOAST on the wide columns |
| Sort within unit | `sortWithinPartitions` before write | `CLUSTER` on the chosen index |

That both realisations carry the *same logical model* is what makes the
benchmark like-for-like: DuckDB on the Parquet star against Postgres on the
Postgres star is a fair comparison, which "DuckDB on Parquet vs Postgres on a
flat table" never was.

### 5.4 Dimension DDL

```sql
-- =====================================================================
-- dim_date. One row per day, 2019-10-01 .. 2019-12-31 (92 rows).
-- Generated by processing/batch_warehouse.py from seed/holidays_2019.csv.
-- =====================================================================
CREATE TABLE dim_date (
  date_key        integer  PRIMARY KEY,   -- smart key yyyymmdd, e.g. 20191129
  full_date       date     NOT NULL UNIQUE,
  year            smallint NOT NULL,
  quarter         smallint NOT NULL,
  month           smallint NOT NULL,
  month_name      text     NOT NULL,
  day_of_month    smallint NOT NULL,
  day_of_week     smallint NOT NULL,      -- ISO: 1 = Monday .. 7 = Sunday
  day_name        text     NOT NULL,
  iso_week        smallint NOT NULL,
  is_weekend      boolean  NOT NULL,
  is_holiday      boolean  NOT NULL,      -- from seed/holidays_2019.csv
  holiday_name    text,                   -- NULL unless is_holiday
  holiday_type    text,                   -- public_holiday|retail_event|promo_period|observance
  CONSTRAINT ck_dim_date_holiday
    CHECK (is_holiday = (holiday_name IS NOT NULL))
);

-- =====================================================================
-- dim_event_type. 5 rows. Small, but it owns two definitions that would
-- otherwise be copy-pasted into every BR: the funnel ORDER, and what
-- counts as an order.
-- =====================================================================
CREATE TABLE dim_event_type (
  event_type_key  smallint PRIMARY KEY,
  event_type_code text     NOT NULL UNIQUE,  -- as it arrives in the feed
  event_type_name text     NOT NULL,         -- label the dashboard prints
  stage_rank      smallint NOT NULL,         -- 1 view, 2 cart, 3 purchase, 9 other
  is_funnel_stage boolean  NOT NULL,
  is_conversion   boolean  NOT NULL,         -- the ONE definition of "an order"
  cart_value_sign smallint NOT NULL          -- +1 adds, -1 removes, 0 neutral
    CHECK (cart_value_sign IN (-1, 0, 1))
);

INSERT INTO dim_event_type VALUES
  (1, 'view',             'Viewed',           1, true,  false,  0),
  (2, 'cart',             'Added to cart',    2, true,  false,  1),
  (3, 'purchase',         'Purchased',        3, true,  true,   0),
  (4, 'remove_from_cart', 'Removed from cart',9, false, false, -1),
  (-1,'unknown',          'Unknown',         99, false, false,  0);

-- =====================================================================
-- dim_warehouse. 5 synthetic rows. warehouse_id is ALSO the Cassandra
-- partition key of stockout_risk — the same choice in both engines.
-- =====================================================================
CREATE TABLE dim_warehouse (
  warehouse_key  smallint PRIMARY KEY,
  warehouse_id   smallint NOT NULL UNIQUE,   -- natural key
  warehouse_code text     NOT NULL UNIQUE,
  warehouse_name text     NOT NULL,
  city           text     NOT NULL,
  region         text     NOT NULL,          -- rollup for the BR6 filter
  warehouse_type text     NOT NULL,          -- central|regional|fulfilment_partner
  lead_time_days smallint NOT NULL,          -- BR6's red line
  capacity_units integer  NOT NULL,
  is_active      boolean  NOT NULL
);

-- =====================================================================
-- dim_product. SCD TYPE 2 on price. REES46 reprices constantly, so this
-- dimension has natural version history — no synthetic changes needed.
-- Measured: 127,693 products -> 244,025 versions.
-- =====================================================================
CREATE TABLE dim_product (
  product_sk    bigint        PRIMARY KEY,   -- surrogate, assigned in Spark
  product_id    bigint        NOT NULL,      -- natural key (REES46)
  version_no    integer       NOT NULL,      -- 1..n within product_id
  price         numeric(10,2) NOT NULL,      -- the Type 2 tracked attribute
  brand         text          NOT NULL,      -- Type 1
  category_id   bigint,                      -- Type 1
  category_code text,                        -- Type 1
  category_l1   text          NOT NULL,      -- Type 1, 'unknown' when absent
  category_l2   text,
  category_l3   text,
  attributes    jsonb         NOT NULL,      -- from data/catalog/products.json
  valid_from    date          NOT NULL,
  valid_to      date          NOT NULL,      -- exclusive; 9999-12-31 = open
  is_current    boolean       NOT NULL,
  CONSTRAINT uq_dim_product_ver   UNIQUE (product_id, valid_from),
  CONSTRAINT ck_dim_product_range CHECK (valid_from < valid_to),
  CONSTRAINT ck_dim_product_attr  CHECK (jsonb_typeof(attributes) = 'object')
);

-- The GIN index, and why jsonb_path_ops rather than the default.
--   jsonb_ops       indexes every KEY and every VALUE. Supports ?, ?|, ?&
--                   (key existence) as well as @>. Larger, slower to build.
--   jsonb_path_ops  indexes only hashed PATHS. Supports @> only, but is
--                   roughly 3x smaller and faster for exactly that operator.
-- BR9 asks "products whose attributes contain {...}", which is @>. So:
CREATE INDEX ix_dim_product_attrs
  ON dim_product USING gin (attributes jsonb_path_ops);

-- The SCD2 access pattern: one partial index, not two.
CREATE UNIQUE INDEX ux_dim_product_current
  ON dim_product (product_id) WHERE is_current;

-- =====================================================================
-- dim_user. SCD TYPE 2 on RFM segment.
-- =====================================================================
CREATE TABLE dim_user (
  user_sk       bigint        PRIMARY KEY,
  user_id       bigint        NOT NULL,
  version_no    integer       NOT NULL,
  snapshot_date date          NOT NULL,      -- RFM snapshot that produced this row
  recency_days  integer,                     -- NULL when never purchased
  frequency     integer       NOT NULL,
  monetary      numeric(14,2) NOT NULL,
  r_score       smallint,                    -- 1..5, NULL if never purchased
  f_score       smallint,
  m_score       smallint,
  rfm_cell      char(3),                     -- '545' — the Type 2 tracked attribute
  segment       text          NOT NULL,
  valid_from    date          NOT NULL,
  valid_to      date          NOT NULL,
  is_current    boolean       NOT NULL,
  CONSTRAINT uq_dim_user_ver UNIQUE (user_id, valid_from),
  CONSTRAINT ck_dim_user_seg CHECK (segment IN
    ('champion','loyal','promising','needs_attention',
     'at_risk','hibernating','no_purchase'))
);

CREATE UNIQUE INDEX ux_dim_user_current
  ON dim_user (user_id) WHERE is_current;
```

**Two traps in the SCD2 build, both of which have bitten this design already.**

*Null-safe change detection.* The obvious predicate
`WHERE prev_value IS NULL OR value <> prev_value` is correct for `dim_product`
only because `price` is `NOT NULL` in silver. `dim_user.rfm_cell` **is** null
for users who have never purchased — 88% of them at the first snapshot — and
`NULL <> NULL` is null, not true, so that predicate emits a fresh version at
every snapshot for every non-buyer. Use `IS DISTINCT FROM` in both builds.

*Never range-join the fact to the dimension.* The Kimball lookup
`ON f.product_id = d.product_id AND f.event_time BETWEEN d.valid_from AND d.valid_to`
produces 305,663,175 intermediate rows — 65× the fact table — and one product
(`1005115`, 46,499 events × 1,642 price versions) is 25% of that on its own. AQE
skew handling cannot split a single join key. Instead assign `product_sk` **in
the same window pass over silver that detects the price change**, so the
surrogate key is already on the event row and the join never happens.

### 5.5 Fact DDL

```sql
-- =====================================================================
-- fact_event. TRANSACTION fact. Grain: one cleaned user event.
-- 1:1 with silver. Measured: 4,754,015 rows.
-- Column order is 8-byte columns first: "readable" order costs ~8 bytes
-- of alignment padding per row, about 37 MB on this table.
-- =====================================================================
CREATE TABLE fact_event (
  event_sk      bigint        NOT NULL,   -- surrogate, assigned in Spark
  product_sk    bigint        NOT NULL,   -- SCD2 version in force on event_date
  user_sk       bigint        NOT NULL,   -- SCD2 version in force on event_date
  event_time    timestamp     NOT NULL,   -- silver already shifted to UTC+7
  user_session  uuid          NOT NULL,   -- DEGENERATE DIMENSION (no dim table)
  price         numeric(10,2) NOT NULL,   -- the measure
  date_key      integer       NOT NULL,   -- FK dim_date
  event_date    date          NOT NULL,   -- partition key, = event_time::date
  event_type_key smallint     NOT NULL,   -- FK dim_event_type
  CONSTRAINT pk_fact_event PRIMARY KEY (event_sk, event_date),
  CONSTRAINT ck_fact_price CHECK (price > 0),
  CONSTRAINT ck_fact_date  CHECK (event_date = event_time::date)
) PARTITION BY RANGE (event_date);
-- 31 daily partitions (Vietnam dates 2019-11-01 .. 2019-12-01, see section 4)
-- + a DEFAULT catch-all, created by warehouse/ddl.sql, not by the loader: the
-- 2019-12-01 partition must exist before the first row arrives, or that row
-- lands in DEFAULT and adding the partition later fails. fact_session_funnel
-- gets the same 31 days + DEFAULT in ddl.sql.

-- B-tree for BR1: the executive screen always filters date then category.
CREATE INDEX ix_fact_event_purchase
  ON fact_event (event_date, event_type_key, event_time);
-- BRIN for the report's index comparison: 4.7M rows written in event_time
-- order, so correlation is ~1.0 and BRIN is ~200x smaller than the B-tree.
-- Included to be MEASURED. Reporting that BRIN loses on point lookups and
-- wins on range scans is a real finding, not a failure.
CREATE INDEX ix_fact_event_time_brin
  ON fact_event USING brin (event_time) WITH (pages_per_range = 32);
-- BR8: orders per user per window.
CREATE INDEX ix_fact_event_user
  ON fact_event (user_sk, event_time) WHERE event_type_key = 3;

-- =====================================================================
-- fact_session_funnel. ACCUMULATING SNAPSHOT. Grain: one session.
-- Measured: 954,686 sessions.
-- =====================================================================
CREATE TABLE fact_session_funnel (
  session_sk         bigint        NOT NULL,  -- surrogate, xxhash64(user_session)
  user_session       text          NOT NULL,  -- natural key
  user_sk            bigint        NOT NULL,  -- SCD2 AS OF session start
  user_id            bigint        NOT NULL,  -- kept for the Cassandra join
  session_start_date date          NOT NULL,  -- partition key
  session_start_at   timestamp     NOT NULL,
  first_view_at      timestamp,               -- MILESTONE, NULL until reached
  first_cart_at      timestamp,               -- MILESTONE, NULL until reached
  purchase_at        timestamp,               -- MILESTONE, NULL until reached
  last_event_at      timestamp     NOT NULL,
  view_to_cart_sec     integer,               -- NULL unless both ends exist
  cart_to_purchase_sec integer,
  view_count         integer       NOT NULL,
  cart_count         integer       NOT NULL,
  purchase_count     integer       NOT NULL,
  cart_value         numeric(12,2) NOT NULL,
  purchase_value     numeric(12,2) NOT NULL,
  funnel_stage       smallint      NOT NULL,  -- furthest milestone: 0/1/2/3
  is_abandoned       boolean       NOT NULL,
  CONSTRAINT pk_fsf PRIMARY KEY (session_start_date, session_sk),
  CONSTRAINT ck_fsf_stage CHECK (funnel_stage =
    CASE WHEN purchase_at   IS NOT NULL THEN 3
         WHEN first_cart_at IS NOT NULL THEN 2
         WHEN first_view_at IS NOT NULL THEN 1
         ELSE 0 END),
  CONSTRAINT ck_fsf_lags CHECK (
    (view_to_cart_sec     IS NULL) = (first_view_at IS NULL OR first_cart_at IS NULL)
AND (cart_to_purchase_sec IS NULL) = (first_cart_at IS NULL OR purchase_at   IS NULL))
) PARTITION BY RANGE (session_start_date);

CREATE INDEX ix_fsf_abandoned
  ON fact_session_funnel (session_start_date, cart_value DESC)
  WHERE is_abandoned;
CREATE INDEX ix_fsf_stage ON fact_session_funnel (session_start_date, funnel_stage);

-- =====================================================================
-- fact_inventory_daily. PERIODIC SNAPSHOT. Grain: one SKU x warehouse x day.
-- Dense by definition: a row exists whether or not anything moved.
-- =====================================================================
CREATE TABLE fact_inventory_daily (
  product_sk          bigint   NOT NULL,   -- SCD2 version AS OF snapshot_date
  product_id          bigint   NOT NULL,   -- natural key, carried on purpose
  date_key            integer  NOT NULL,   -- FK dim_date
  warehouse_key       smallint NOT NULL,   -- FK dim_warehouse
  warehouse_id        smallint NOT NULL,   -- natural key AND the partition key
  snapshot_date       date     NOT NULL,
  stock_on_hand       integer  NOT NULL,   -- SEMI-ADDITIVE: never SUM across days
  reorder_point       integer  NOT NULL,   -- NON-ADDITIVE: a policy level
  units_sold_that_day integer  NOT NULL,   -- FULLY ADDITIVE
  velocity_7d         real     NOT NULL,   -- NON-ADDITIVE: an average
  days_to_stockout    real,                -- NON-ADDITIVE; NULL iff velocity_7d = 0
  is_below_reorder    boolean  NOT NULL,
  CONSTRAINT pk_fid PRIMARY KEY (warehouse_id, snapshot_date, product_id),
  CONSTRAINT ck_fid_dts CHECK ((days_to_stockout IS NULL) = (velocity_7d = 0))
) PARTITION BY LIST (warehouse_id);
-- ddl.sql creates one partition per warehouse (wh1..wh5) and no DEFAULT, so a
-- row for a warehouse 6 fails loudly instead of hiding.
-- Partitioned by warehouse_id because that is exactly BR6's access path — and
-- because it makes the Postgres physical design converge on the Cassandra one:
-- stockout_risk's partition key is (warehouse_id) too. Same logical model, two
-- engines, the same pruning decision. That is a clean paragraph for the report.

CREATE INDEX ix_fid_hot
  ON fact_inventory_daily (warehouse_id, snapshot_date, days_to_stockout)
  WHERE days_to_stockout IS NOT NULL;
```

**Additivity matters on screen, not just on paper.** `stock_on_hand` is
semi-additive: summing it across warehouses on one day is stock; summing it
across days is nonsense. The BR6 screen must therefore aggregate across
warehouses and *filter* to one day, never sum a date range. This is the standard
periodic-snapshot trap and it belongs in the report.

**The SKU universe is narrowed, deliberately.** All 127,693 sampled products ×
5 warehouses × 30 days would be 19,153,950 rows — four times `fact_event`, and
past the 5-million-row cap in CLAUDE.md, to serve one BR. It is also 99.8% dead
weight: only 12,659 products are ever purchased in the sample, so the other
115,034 have zero velocity, infinite days-to-stock-out, and can never appear on
the BR6 screen. The inventory universe is therefore **SKUs with at least one
purchase in the window**: 12,659 × 5 × 30 = 1,898,850 rows. The grain is
unchanged and the fact is still a dense periodic snapshot; only the SKU universe
is scoped, and the report says so.

### 5.6 Build order

`processing/batch_warehouse.py` runs these in order. The order is forced — see
the RFM note below.

1. `dim_date` (from `seed/holidays_2019.csv`), `dim_event_type`, `dim_warehouse`
   — no dependencies
2. `dim_product` — SCD2 from silver price history + `data/catalog/products.json`
3. `stg_rfm_snapshot` — R/F/M per user per snapshot date, straight from silver
4. `dim_user` — SCD2 over `stg_rfm_snapshot`
5. `fact_event`, `fact_session_funnel`, `fact_inventory_daily`
6. Write Parquet, then load Postgres from the same DataFrames: the tables read
   back from that Parquet, passed to the loading functions in
   `serving/load_star_postgres.py` (Tin, W40). Until those exist, that script runs
   on its own and loads the three small dimensions

**Why step 3 exists.** RFM is BR4, a gold table — but `dim_user` is Type 2 on
RFM segment, and gold is now built from the star. That is a cycle: dim_user needs
RFM, RFM needs gold, gold needs the star. It is broken by treating RFM as what it
actually is — a derived *attribute of the user dimension*, not a gold aggregate.
It is computed inside the warehouse layer on natural keys, before any fact is
built. BR4's gold table then reads `dim_user` instead of recomputing anything.

### 5.7 A graph database was considered and rejected

BR7 (frequently bought together) is a graph problem in the textbook sense:
products are nodes, co-purchases are weighted edges, and "what sells with A" is a
one-hop traversal. Neo4j would express it directly.

It was rejected on cost. The team has 2–4 hours per person per week and nobody
has used Spark before; every new technology costs roughly a week the schedule
does not have. The rubric's Technology Content criterion rewards **depth** —
more than three worked illustrations — not the number of technologies, so a
fourth data store would trade a week of schedule for no marks. And the affinity
problem at this scale does not need a graph: a self-join over purchase events
grouped by session produces the full co-occurrence matrix in one Spark SQL
statement, and BR7's screen only ever asks for one hop from one anchor product.

The rationale is recorded here because "we considered a graph database and chose
not to use it, for these reasons" is worth more in the report than silence — and
it pairs with the accumulating-snapshot limitation in section 8 as a second
honest "considered and declined" entry.

## 6. Cassandra schema

Cassandra cannot filter arbitrarily, so keys are designed backwards from the
question each screen will ask.

```sql
-- BR1: GMV per minute, for the executive screen
CREATE TABLE gmv_by_minute (
  event_date    date,
  category_l1   text,
  window_start  timestamp,
  gmv           decimal,
  order_count   int,
  PRIMARY KEY ((event_date, category_l1), window_start)
) WITH CLUSTERING ORDER BY (window_start DESC);

-- BR3: trending products, 15-minute sliding window
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

-- BR5: abandoned carts, for the CRM team
CREATE TABLE abandoned_carts (
  event_date    date,
  user_session  text,
  cart_value    decimal,
  user_id       bigint,
  item_count    int,
  last_event_at timestamp,
  PRIMARY KEY ((event_date), user_session)
);

-- BR6: stock-out risk per warehouse
CREATE TABLE stockout_risk (
  warehouse_id      int,
  days_to_stockout  float,
  product_id        bigint,
  stock_on_hand     int,
  velocity_7d       float,
  PRIMARY KEY ((warehouse_id), days_to_stockout, product_id)
);

-- BR8: order velocity alerts
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

Reasoning behind the keys, to be reused in the report:

- BR1: the partition key is `(event_date, category_l1)` because the screen always
  filters by date and category. Clustering by `window_start DESC` means "the last
  60 minutes" reads exactly 60 adjacent rows at the head of one partition, with
  no sort step.
- BR6: `days_to_stockout` ascending puts the most urgent SKUs at the head of the
  partition.

### 6.1 Three tables that leave stale rows, handled three different ways

Any table that clusters on a value which *changes between runs* gets a new row
from an upsert instead of replacing the old one. Three tables here do, and the
correct fix is different for each. Getting this wrong shows up on screen as
duplicated products, duplicated carts, or a list that empties itself mid-demo.

| Table | Written by | Fix |
|---|---|---|
| `stockout_risk` | batch, rewrites every warehouse in full | `DELETE FROM stockout_risk WHERE warehouse_id = ?`, then insert |
| `trending_products` | streaming, re-emits each window | `DELETE FROM trending_products WHERE window_start = ?`, then insert the new top-N |
| `abandoned_carts` | streaming, accumulates through the day | **no delete** — see below |

`abandoned_carts` was the hard one. Deleting its partition
(`WHERE event_date = ?`) inside `foreachBatch` would erase every cart found
earlier the same day, so the BR5 screen would show only the last micro-batch's
carts and visibly empty itself during the demo. But deleting just one session's
old row is *not expressible* against a key of
`((event_date), cart_value, user_session)`: Cassandra deletes by a prefix of the
clustering columns, so it would need the session's **previous** `cart_value` —
which is exactly the value that changed.

The key above therefore drops `cart_value` out of the primary key entirely:
`PRIMARY KEY ((event_date), user_session)`. Now the upsert is naturally
idempotent — same session, same row, new value — and no delete is needed at all.

The cost is real and must be stated: the rows are no longer stored sorted by cart
value, so "the 50 highest-value carts today" is a partition read plus a sort of
at most a few thousand rows in the API. That trade — give up on-disk ordering to
get idempotent writes — is itself good report material, and it is a more honest
BR5 key-design story than the original one, which did not survive contact with
the delete semantics.

`trending_products` has the same changing-clustering-value bug (a product at rank
3 in one emission and rank 5 in the next leaves two live rows, and `LIMIT 20`
returns it twice), but there the partition *is* one window, so deleting the
partition is exactly right.

**`days_to_stockout` must never be null in Cassandra.** It is a clustering
column, and Cassandra rejects null clustering keys. `stock_on_hand / velocity_7d`
returns null in Spark whenever `velocity_7d` is 0, which is true for ~90% of
SKUs. The star schema stores that honestly as `NULL`; the Cassandra projection
substitutes a sentinel, `when(velocity_7d > 0, stock_on_hand/velocity_7d).otherwise(9999.0)`.
The report states that BR6 only ranks SKUs with movement.

## 7. Gold tables in Parquet

```
gold/funnel_daily/event_date=2019-11-01/
    event_date, category_l1, views, carts, purchases,
    cr_view_to_cart, cr_cart_to_purchase

gold/rfm_segments/snapshot_date=2019-11-30/
    user_id, recency_days, frequency, monetary,
    r_score, f_score, m_score, segment

gold/product_affinity/
    product_a, product_b, co_count, support, lift
```

`funnel_daily` is now an aggregation of `fact_session_funnel`, and `rfm_segments`
is a projection of `dim_user` where `is_current`. Neither recomputes anything
from silver.

## 8. Life of an event

There are two paths and they are deliberately separate. Following one event
through both is the clearest way to explain the system.

**Batch path (BR2, BR4, BR6, BR7, BR9):**

1. `load_bronze.py` reads `data/raw/2019-Nov.csv`, keeps the 7% user sample, and
   writes `data/bronze/` as Parquet partitioned by `event_date`.
2. `batch_silver.py` builds `data/silver/` from bronze using the seven cleaning
   rules in section 4 — including the UTC+7 shift and the recomputed
   `event_date`. This runs before any other batch job, including in W39, before
   the streaming job exists.
3. `batch_warehouse.py` builds the star schema in the order given in 5.6, writes
   it to `data/warehouse/` as Parquet, and loads the same DataFrames into
   Postgres through `serving/load_star_postgres.py` (5.6 step 6).
4. `batch_gold.py` reads the **star**, not silver, and computes the funnel (BR2),
   RFM projection (BR4), affinity (BR7) and stock-out risk (BR6), writing to
   Parquet gold and — for BR6 only — to Cassandra.

**Streaming path (BR1, BR3, BR5, BR8):**

5. `replayer.py` reads `data/bronze/` (Parquet — *not* the raw CSV), orders by
   `event_time`, and every 5 seconds writes a JSON file into `data/stream_landing/`.
   A speed factor compresses playback so a demo does not have to wait: at
   `--speed 60` one hour of real data replays in one minute, and each file holds
   5 minutes of events: 554 rows on average, but about 90 at 00:00 UTC and about
   880 at 15:00–16:00 UTC, about 2,000 from 08:00 UTC on 17 November (the day
   with the most purchases, 13,076), and 3,078 in the busiest slice of the month
   (measured over all 8,640 slices). `--start` picks the first event time, in
   UTC. 15 November (UTC) has 432,575 events and no purchase at all, so BR1 shows
   GMV 0 for that whole day.

   It must read bronze and not `data/raw/2019-Nov.csv`. The raw file holds all
   3,696,117 users; bronze holds only the 258,390 in the 7% bucket. A replayer
   pointed at raw would feed the Cassandra tables a 14× larger, differently
   shaped population than the batch side, and the ≥99% correctness gate would be
   unreachable for BR1/BR3/BR5/BR8 by construction.

6. `streaming_gold.py` is already running with
   `readStream.format("json").schema(EVENT_SCHEMA).load("data/stream_landing/")`.
   Spark picks up the new file in its next micro-batch.
7. Inside the micro-batch: apply **the same seven cleaning rules as silver,
   including the UTC+7 shift and the recomputed `event_date`**, by importing
   `clean()` from `batch_silver.py` rather than copying the rules. Then
   `withWatermark("event_time", "10 minutes")` so old state can be dropped.
   Importing the function does not make the stream a silver writer.

   The timezone shift is easy to omit here because the rules were written for
   `batch_silver.py`. Omit it and `gmv_by_minute.event_date` is UTC while
   `funnel_daily.event_date` is UTC+7, so the executive screen and the funnel
   screen disagree about which day a 17:00–24:00 UTC event belongs to.

8. Four aggregations run over that stream: GMV in 1-minute windows (BR1); top-N
   over a 15-minute window sliding every minute (BR3 — Structured Streaming
   cannot rank a streaming DataFrame, so the ordering and the top-N cut happen
   inside `foreachBatch`, where the micro-batch is an ordinary static DataFrame);
   sessions with a `cart` and no `purchase` after 30 minutes (BR5); orders per
   user in 5-minute windows with a severity label (BR8).
9. Each aggregation ends in `foreachBatch`, where plain `cassandra-driver` code
   writes the result using the per-table rule from section 6.1. Checkpoints go to
   `data/checkpoints/<job_name>/`.

**The streaming job does not write silver.** The earlier design had silver with
two writers — batch and stream — "by design". That does not work, for two
independent reasons. If the stream writes with a Parquet file sink it creates
`data/silver/_spark_metadata/`, and from then on `spark.read.parquet("data/silver")`
reads *only* files listed in that log, making every file `batch_silver.py` wrote
invisible to Spark while DuckDB and the Postgres loader still glob the whole
directory — Spark and DuckDB would then disagree on the same path, voiding the
correctness gate. And if it writes through `foreachBatch` instead, the rows are
duplicates: the replayer replays bronze, which `batch_silver.py` has already
turned into silver, so a second demo run inflates BR2's funnel and BR7's
co-occurrence counts and shifts BR4's recency. The streaming job's outputs are
the Cassandra gold tables and nothing else.

**One honest limitation, worth stating rather than hiding.** An accumulating
snapshot is defined by rows that fill in over time, and plain Parquet cannot
update in place — Iceberg and Delta are out of scope. So
`fact_session_funnel` is rebuilt by full recompute-and-overwrite on every batch
run, not incrementally updated. It is cheap (954,686 sessions, one shuffle,
seconds). Saying plainly that "accumulating snapshot here means
recompute-and-overwrite, and this is exactly the limitation a table format would
remove" is a stronger report paragraph than pretending the rows mutate.

10. FastAPI routes each request: BR1/3/5/6/8 hit Cassandra with a point query on
    the partition key; BR2/4/7/9 let DuckDB read the gold and warehouse Parquet
    directly.
11. React renders. Target: every screen responds in under 2 seconds.

## 9. The eight screens

| Screen | BR | Reads from | Components | Filters |
|---|---|---|---|---|
| Real-time executive | BR1 | Cassandra | Four large metric cards plus a GMV line chart for the last 60 minutes, refreshing every 10s | Date, category |
| Conversion funnel | BR2 | Parquet | Three-stage funnel chart plus a conversion rate table by category | Date range, category |
| Trending products | BR3 | Cassandra | Top 20 table with rank-change arrows against the previous window | Time window |
| Customer segments | BR4 | Parquet | 5x5 RFM heatmap plus a customer list for the selected cell | Snapshot date, segment |
| Abandoned carts | BR5 | Cassandra | List sorted by cart value descending, plus a simulated "create campaign" action | Date, value threshold |
| Inventory alerts | BR6 | Cassandra | SKU table coloured by days remaining, red under 3 days | Warehouse, day threshold |
| Bought together | BR7 | Parquet | Product search box, then 10 related products with their lift scores | Anchor product |
| Risk alerts | BR8 | Cassandra | Alert timeline by severity, expandable to the underlying orders | Date, severity |
| Ad-hoc lookup (bonus) | BR9 | Parquet | Combined filters over the star, including a `jsonb`/struct attribute filter, with query time shown on screen | Category, brand, price, date, attributes |

BR9 is the bonus ninth screen; the eight above it are the ones the grade depends
on.

Executive screen sketch:

```
+----------------------------------------------------------+
|  ShopInsight        [Executive v]   Date: 2019-11-01      |
+----------------------------------------------------------+
|  Category: [ All v ]                   Updated 10s ago    |
|                                                           |
|  +---------+  +---------+  +---------+  +---------+       |
|  |  GMV    |  | Orders  |  |  AOV    |  | vs last |       |
|  | 1.24 B  |  |  8,412  |  |  147 K  |  |  +12%   |       |
|  +---------+  +---------+  +---------+  +---------+       |
|                                                           |
|  GMV per minute — last 60 minutes                         |
|  +-----------------------------------------------------+  |
|  |            /\      /\                               |  |
|  |      /\  /    \  /    \      /\                     |  |
|  |  __/    \      \/      \____/  \___                 |  |
|  +-----------------------------------------------------+  |
|                                                           |
|  Query: 43 ms · Cassandra · 1 partition · 60 rows         |
+----------------------------------------------------------+
```

That last line appears on **every** screen. It turns the dashboard into live
evidence for the evaluation section — a grader sees it without opening the report.

## 10. Repository layout

```
shop-insight/
├── CLAUDE.md                   Context for Claude Code
├── SYSTEM_DESIGN.md            This file
├── PLAN.md                     Schedule and gates (Vietnamese, internal)
├── docker-compose.yml          Cassandra + Postgres, tags pinned to the patch
├── .env.example                Ports, database, user, password. Copy to .env to change one
├── requirements.txt
├── README.md                   One-command run instructions
├── conf/
│   └── spark-defaults.conf     Driver memory + UTC session time zone, read by every script
├── seed/
│   └── holidays_2019.csv       Committed. Feeds dim_date.is_holiday
├── data/                       gitignored except the .gitkeep skeleton
│   ├── raw/                    Original CSV from Kaggle
│   ├── bronze/                 Raw Parquet
│   ├── silver/                 Cleaned Parquet
│   ├── warehouse/              Star schema Parquet: 5 dims + 3 facts
│   ├── catalog/                Generated products.json
│   ├── inventory/              Generated daily inventory series
│   ├── gold/                   Aggregated Parquet
│   ├── stream_landing/         Where the replayer writes JSON
│   └── checkpoints/            Spark streaming checkpoints
├── ingestion/
│   ├── replayer.py             Simulates the real-time stream (reads bronze)
│   ├── load_bronze.py          CSV -> bronze Parquet, 7% user sample
│   ├── gen_catalog.py          Synthetic product attributes JSON
│   └── gen_inventory.py        Daily inventory series
├── processing/
│   ├── schema.py               Shared EVENT_SCHEMA
│   ├── source.py               Source reader (Kafka swap touches only this)
│   ├── kata.py                 Spark install check, prints four expected counts
│   ├── batch_silver.py         bronze -> silver. Runs before any batch job
│   ├── batch_warehouse.py      silver -> star schema (Parquet + Postgres)
│   ├── dim_product.py          dim_product SCD2 + product_sk (5.6 step 2), imported by batch_warehouse
│   ├── dim_user.py             stg_rfm_snapshot + dim_user SCD2 + user_sk (steps 3-4), imported likewise
│   ├── streaming_gold.py       BR1, BR3, BR5, BR8
│   └── batch_gold.py           BR2, BR4, BR6, BR7 — reads the star
├── warehouse/
│   └── ddl.sql                 Postgres star schema DDL (sections 5.4, 5.5)
├── serving/
│   ├── check_infra.py          Both drivers reach both containers; prints INFRA OK
│   ├── cassandra_schema.cql    All CREATE TABLE statements
│   ├── apply_schema.py
│   ├── load_star_postgres.py   Postgres loader: batch_warehouse step 6 calls it
│   └── api/                    FastAPI, one router per BR
├── benchmark/
│   ├── queries.sql             Shared query set across all configurations
│   ├── run_benchmark.py        Measures p50/p95, writes CSV
│   └── results/
├── tests/
│   └── test_fixtures.py        API contract check: fixtures and routers vs docs/API_CONTRACT.md
├── checks/
│   ├── scd2_integrity.py       SCD2 check: no overlap or gap, one current row per key
│   └── fact_event_spot.py      fact_event has the right price at event time, on 5 pinned events
├── web/                        React + TypeScript
└── docs/
    ├── SETUP_SPARK.md          Unattended install: JDK, Python, PySpark, Docker
    ├── SPARK_GUIDE_VI.md       The same, in Vietnamese, explaining every step and file
    ├── BR_SCOPE.md             The 8 BRs: scope, owners, done criteria
    ├── STREAMING_PATTERN.md    The BR1 reference pattern the other three copy
    ├── DATA_MODEL.md           ERD + star + physical design, for the report
    ├── AI_USAGE.md             Where AI assistance was used
    ├── API_CONTRACT.md         Frozen BR1-BR8 endpoint contract
    └── evidence/               EXPLAIN ANALYZE output, DESCRIBE TABLE
                                screenshots, query plans. Feeds report + slides
```

Two `.gitignore` consequences of the new directories, both already handled:
`seed/` is outside `data/` so it is tracked with no rule change; `data/warehouse/`,
`data/catalog/` and `data/inventory/` each need an explicit negation added,
because `data/*` excludes every child and git will not descend into an excluded
directory to find a `.gitkeep`.

## 11. Running the system

```bash
# 1. Infrastructure
docker compose up -d --wait          # Cassandra + Postgres; --wait returns only when both are healthy
python serving/check_infra.py        # both drivers connect; prints INFRA OK
python serving/apply_schema.py       # Cassandra keyspace and tables
docker compose exec -T postgres psql -U shopinsight -d shopinsight -v ON_ERROR_STOP=1 < warehouse/ddl.sql   # Postgres star schema

# 2. Build the data, steps 1-6 in this order (1-2 once, 15-25 minutes)
python ingestion/load_bronze.py      # 1. 7% user sample, rule is hard-coded
python processing/batch_silver.py    # 2. bronze -> silver. Batch needs this
python ingestion/gen_catalog.py      # 3. product attributes JSON
python ingestion/gen_inventory.py    # 4. daily inventory series
python processing/batch_warehouse.py # 5. silver -> star (Parquet + Postgres)
python serving/load_star_postgres.py #    optional, Postgres only, until step 6 of batch_warehouse calls it
python processing/batch_gold.py      # 6. reads the star

# 3. Real-time stream (two terminals)
python processing/streaming_gold.py       # start FIRST, wait for READY (--fresh: forget earlier runs)
python ingestion/replayer.py --speed 60   # 1 hour of data per minute

# 4. Application
uvicorn serving.api.main:app --reload --port 8000
cd web && npm ci && npm run dev
```

`load_bronze.py` takes no `--rows` flag. The sample size is whatever the
deterministic user-hash rule yields (4,767,012 rows); a row count would break
byte-identical output across the four machines.

Cassandra takes 30-60 seconds to accept CQL. `--wait` is what makes the shell
wait for it rather than the next command failing on a refused connection; it
returns only once both healthchecks pass.

The order in step 3 matters: the streaming job must be running before the
replayer starts. Start it after and the files already sitting in the landing
directory collapse into one huge micro-batch, which looks nothing like real time
during a demo.

### 11.1 Toolchain — pin these exactly

| | Version | Why |
|---|---|---|
| Python | 3.14.x | The only interpreter Ubuntu 26.04 ships; 3.11–3.13 are not in the repos |
| PySpark | `pyspark==4.1.3` | 3.5.x **segfaults** on Python 3.14 — its vendored cloudpickle 2.x calls a `pickle._getattribute` that changed in 3.14, and cloudpickle serialises every Python function Spark ships to a worker (every UDF and RDD lambda). In the classic `local[*]` mode used here `foreachBatch` is *not* pickled — it is a py4j callback on the driver (`ForeachBatchFunction` in `pyspark/sql/utils.py`) — so the earlier claim that the crash lands on the Cassandra write path was wrong about the mechanism, not about the pin |
| JDK | OpenJDK 21 | Spark 4.x needs Java 17 or newer; 21 is pinned so four machines match |
| Cassandra | `cassandra:4.1.12` | Single node in Docker. Pinned to the patch: `4.1` is a moving tag, and a node that starts on one patch and restarts on another after a `docker pull` is a debugging session nobody has time for. Its heap is capped at 2 GB (`MAX_HEAP_SIZE` **and** `HEAP_NEWSIZE` in `docker-compose.yml` — this image runs CMS, which exits 1 unless both are set) because the default is a quarter of host RAM, about 3.7 GB inside a 16 GB WSL, and Spark's driver already claims 6 GB |
| PostgreSQL | `postgres:16.15` | The **second physical realisation of the star schema** (section 5.3), not only a benchmark baseline. 16 ships `jsonb` and the `gin (... jsonb_path_ops)` operator class in core, so `warehouse/ddl.sql` needs no `CREATE EXTENSION` — only room: `maintenance_work_mem=256MB` for the W39 GIN build on `dim_product.attributes`, `shared_buffers=512MB` |

The two container settings above live in `docker-compose.yml` and nowhere else,
the way the Spark settings live in `conf/spark-defaults.conf`. They are a
**config of record, not tuning**: modest values chosen so that Cassandra,
Postgres and a 6 GB Spark driver fit on one laptop at the same time, recorded so
that all four machines match. Hard rule 3 still applies — any change to them
waits for the W41 benchmarks. `python serving/check_infra.py` reads
`shared_buffers` and `maintenance_work_mem` back out of the running server, so a
setting that did not take effect is visible in one command rather than at the end
of a W39 index build.

Driver memory is set in the committed `conf/spark-defaults.conf`
(`spark.driver.memory 6g`), and Spark reads that file only when `SPARK_CONF_DIR`
points at `conf/` **before** the SparkSession is built. Every script therefore sets
`os.environ["SPARK_CONF_DIR"]` in its first lines. Setting driver memory on
`SparkSession.builder.config(...)` works only when that builder is what launches the
JVM. With a JVM already running in the process (the pyspark shell, a notebook, a
session stopped earlier) it is ignored, and after a `stop()` silently so: measured on
4.1.3, `getConf()` reports `6g` while the heap stays at 1 GB. And
`spark.executor.memory` does nothing at
all in `local[*]` — the driver *is* the executor. Four people who have never used
Spark will all hit this; `docs/SETUP_SPARK.md` says so explicitly.

The same file pins `spark.sql.session.timeZone UTC`. The raw `event_time` is UTC,
but the team's laptops run on UTC+7. Without the pin, `to_date(event_time)` in
`load_bronze.py` files the events of 30 Nov 17:00–24:00 UTC under 1 Dec, which
gives 31 bronze partitions instead of 30 and a different layout per machine.
`batch_silver.py`'s `from_utc_timestamp` shift also assumes a UTC session.

## 12. Comparison tier

Postgres and DuckDB do not serve the application. They exist to satisfy the
course requirement to "introduce at least one alternative solution for
comparison". There are now three configurations, not two.

| | PostgreSQL — flat | PostgreSQL — star | DuckDB |
|---|---|---|---|
| Data | the same ~4.7M silver rows in one wide table | the star schema from section 5 | reads the Parquet star directly, no load step |
| Purpose | shows classic index techniques on a wide denormalised table | the like-for-like counterpart to DuckDB: same logical model, different engine | ground truth for the correctness criterion, and the second alternative solution |
| Techniques shown | B-tree, BRIN, partial, composite | declarative partitioning, GIN on `jsonb`, FK joins, star-join plans | zone maps, vectorised scan over Parquet, struct projection |

The flat table is kept because it is what makes the B-tree/BRIN/partial/composite
comparison legible — those are the presentation's slide 2 — and the star is added
because it is what makes the DuckDB comparison fair. Loading Postgres from the
raw CSV instead of from silver would compare two different datasets and void both
the benchmark and the correctness check.

The benchmark query set lives in `benchmark/queries.sql` and runs identically
against every configuration. That is what makes the numbers comparable.

## 13. What this system deliberately does not do

Stating the limits in the report makes the conclusion stronger than pretending
everything is production grade, and it defuses the hard questions during defence.

- No real cluster. Spark runs locally, Cassandra is a single node. Performance
  conclusions are relative between configurations, not production figures.
- The real-time feed is a replay, not a live stream. Event ordering is cleaner
  than reality and there is almost no late-arriving data.
- The streaming BRs do not read the star schema. Only BR6 does. Section 1 says
  why.
- `fact_session_funnel` is an accumulating snapshot that is recomputed and
  overwritten rather than updated in place, because plain Parquet has no UPDATE.
- The inventory and product-attribute data are synthetic, so BR6 and the `jsonb`
  half of BR9 prove the mechanism but do not reflect real warehouse or catalogue
  behaviour.
- A graph database was considered for BR7 and rejected. Section 5.7 says why.
- No authentication or authorisation. The dashboard assumes an internal network.
