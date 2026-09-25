-- ShopInsight — PostgreSQL Star Schema DDL
-- warehouse/ddl.sql
--
-- Apply once to a blank database:
--   docker exec -i shopinsight-postgres psql -U shopinsight -d shopinsight < warehouse/ddl.sql
--
-- Re-running is safe: every object uses CREATE ... IF NOT EXISTS or CREATE OR REPLACE.
-- To start fresh: DROP SCHEMA public CASCADE; CREATE SCHEMA public;
--
-- W39 scope: DDL for all dimensions and facts, but only dim_date, dim_event_type,
-- and dim_warehouse are loaded this week. Large dims and facts load in W40.
--
-- Design choices:
--   • fact_event      → RANGE partition by event_date, 30 daily partitions + DEFAULT
--   • fact_inventory_daily → LIST partition by warehouse_id
--   • dim_product.attributes → JSONB with GIN index (jsonb_path_ops)
--   • dim_product and dim_user → unique partial index on natural key WHERE is_current
--   • All surrogate keys are BIGSERIAL (auto-increment) except where noted
--   • Timestamps stored as TIMESTAMPTZ (UTC); application layer converts to UTC+7

-- ══════════════════════════════════════════════════════════════════════════════
-- 1. DIMENSION TABLES
-- ══════════════════════════════════════════════════════════════════════════════

-- ── dim_date ─────────────────────────────────────────────────────────────────
-- Covers 2019-10-01 to 2019-12-31 (92 rows).
-- date_key = yyyymmdd INTEGER for join efficiency (no casting in fact queries).
CREATE TABLE IF NOT EXISTS dim_date (
    date_key      INTEGER       PRIMARY KEY,          -- yyyymmdd e.g. 20191101
    full_date     DATE          NOT NULL UNIQUE,
    year          SMALLINT      NOT NULL,
    quarter       SMALLINT      NOT NULL CHECK (quarter BETWEEN 1 AND 4),
    month         SMALLINT      NOT NULL CHECK (month BETWEEN 1 AND 12),
    month_name    VARCHAR(9)    NOT NULL,
    day_of_month  SMALLINT      NOT NULL CHECK (day_of_month BETWEEN 1 AND 31),
    day_of_week   SMALLINT      NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),  -- ISO: Mon=1 Sun=7
    iso_week      SMALLINT      NOT NULL CHECK (iso_week BETWEEN 1 AND 53),
    is_weekend    BOOLEAN       NOT NULL,
    -- RULE: is_holiday MUST equal (holiday_name IS NOT NULL) — enforced in application and batch_warehouse.py
    is_holiday    BOOLEAN       NOT NULL,
    holiday_name  VARCHAR(100),                       -- NULL when not a holiday
    holiday_type  VARCHAR(30)                         -- public_holiday | retail_event | promo_period | observance
        CHECK (holiday_type IN ('public_holiday', 'retail_event', 'promo_period', 'observance') OR holiday_type IS NULL),
    CONSTRAINT chk_dim_date_holiday_consistency
        CHECK (is_holiday = (holiday_name IS NOT NULL))
);

-- ── dim_event_type ────────────────────────────────────────────────────────────
-- 5 rows: view(1), cart(2), purchase(3), other(9), unknown(-1 sentinel).
CREATE TABLE IF NOT EXISTS dim_event_type (
    event_type_key  INTEGER       PRIMARY KEY,   -- -1=unknown, 1=view, 2=cart, 3=purchase, 9=other
    event_code      VARCHAR(30)   NOT NULL UNIQUE,
    display_name    VARCHAR(50)   NOT NULL,
    stage_rank      SMALLINT      NOT NULL,      -- 1=view, 2=cart, 3=purchase, 9=other, 0=unknown
    is_funnel_stage BOOLEAN       NOT NULL,
    is_conversion   BOOLEAN       NOT NULL,
    cart_value_sign SMALLINT      NOT NULL CHECK (cart_value_sign IN (-1, 0, 1))
                                                 -- +1 add-to-cart, -1 checkout, 0 not applicable
);

-- ── dim_warehouse ─────────────────────────────────────────────────────────────
-- 5 rows, warehouse_id 1–5.
CREATE TABLE IF NOT EXISTS dim_warehouse (
    warehouse_id    INTEGER       PRIMARY KEY,   -- 1-5
    warehouse_name  VARCHAR(100)  NOT NULL,
    region          VARCHAR(50)   NOT NULL,
    city            VARCHAR(50)   NOT NULL,
    lead_time_days  SMALLINT      NOT NULL CHECK (lead_time_days > 0),
    capacity_units  INTEGER       NOT NULL CHECK (capacity_units > 0),
    is_active       BOOLEAN       NOT NULL DEFAULT TRUE
);

-- ── dim_product (SCD Type 2) ──────────────────────────────────────────────────
-- Loaded in W40 by Nguyên. DDL created now so fact_event FK compiles.
-- attributes is JSONB: stores category_code, brand, and any future flexible fields.
CREATE TABLE IF NOT EXISTS dim_product (
    product_sk      BIGSERIAL     PRIMARY KEY,
    product_id      BIGINT        NOT NULL,       -- natural key from silver
    category_id     BIGINT,
    category_code   VARCHAR(200),                 -- e.g. "electronics.smartphone"
    category_l1     VARCHAR(50),
    category_l2     VARCHAR(50),
    category_l3     VARCHAR(50),
    brand           VARCHAR(100),
    price           NUMERIC(10,2),                -- price at which the product first appeared
    attributes      JSONB,                        -- flexible attributes; GIN indexed below
    valid_from      DATE          NOT NULL,
    valid_to        DATE,                         -- NULL means current
    is_current      BOOLEAN       NOT NULL DEFAULT TRUE,
    loaded_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- GIN index on dim_product.attributes for @> containment operator.
-- jsonb_path_ops: smaller index, supports @> only (sufficient for all planned queries).
CREATE INDEX IF NOT EXISTS idx_dim_product_attributes_gin
    ON dim_product USING GIN (attributes jsonb_path_ops);

-- Unique partial index: only ONE current row per product_id.
CREATE UNIQUE INDEX IF NOT EXISTS uq_dim_product_current
    ON dim_product (product_id)
    WHERE is_current = TRUE;

-- ── dim_user (SCD Type 2) ────────────────────────────────────────────────────
-- Loaded in W40 by Khang (stg_rfm_snapshot → dim_user).
CREATE TABLE IF NOT EXISTS dim_user (
    user_sk         BIGSERIAL     PRIMARY KEY,
    user_id         BIGINT        NOT NULL,       -- natural key from silver
    recency_days    SMALLINT,                     -- NULL for no-purchase users
    frequency       INTEGER       NOT NULL DEFAULT 0,
    monetary        NUMERIC(14,2) NOT NULL DEFAULT 0,
    r_score         SMALLINT,                     -- 1–5; NULL for no-purchase
    f_score         SMALLINT,
    m_score         SMALLINT,
    rfm_cell        CHAR(3),                      -- e.g. '555'; NULL for no-purchase
    segment         VARCHAR(30)   NOT NULL DEFAULT 'no_purchase',
    snapshot_date   DATE          NOT NULL,
    valid_from      DATE          NOT NULL,
    valid_to        DATE,
    is_current      BOOLEAN       NOT NULL DEFAULT TRUE,
    loaded_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- Unique partial index: only ONE current row per user_id.
CREATE UNIQUE INDEX IF NOT EXISTS uq_dim_user_current
    ON dim_user (user_id)
    WHERE is_current = TRUE;

-- ══════════════════════════════════════════════════════════════════════════════
-- 2. FACT TABLES
-- ══════════════════════════════════════════════════════════════════════════════

-- ── fact_event (transaction fact) ────────────────────────────────────────────
-- Range-partitioned by event_date: one partition per day of November 2019,
-- plus a DEFAULT loader partition for any date outside that range.
--
-- Why 30 daily partitions and a DEFAULT:
--   • Silver covers 2019-11-01 to 2019-12-01 (31 event_date values in silver,
--     but the Dec-01 partial day only has 25,859 rows — a separate partition).
--   • The DEFAULT partition catches Dec-01 rows and any future replays without
--     needing to ADD PARTITION before INSERT.
--   • Partition pruning on event_date is the primary performance lever (PLAN.md
--     benchmark goal W41).
CREATE TABLE IF NOT EXISTS fact_event (
    event_sk        BIGSERIAL,
    event_date      DATE          NOT NULL,   -- partition key
    event_time      TIMESTAMPTZ   NOT NULL,   -- Vietnam wall-clock time
    event_type_key  INTEGER       NOT NULL REFERENCES dim_event_type(event_type_key),
    product_sk      BIGINT        REFERENCES dim_product(product_sk),
    user_sk         BIGINT        REFERENCES dim_user(user_sk),
    warehouse_id    INTEGER       REFERENCES dim_warehouse(warehouse_id),
    user_session    VARCHAR(50)   NOT NULL,
    price           NUMERIC(10,2) NOT NULL CHECK (price > 0),
    PRIMARY KEY (event_sk, event_date)
) PARTITION BY RANGE (event_date);

-- 30 daily partitions: 2019-11-01 to 2019-11-30
CREATE TABLE IF NOT EXISTS fact_event_20191101 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-01') TO ('2019-11-02');
CREATE TABLE IF NOT EXISTS fact_event_20191102 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-02') TO ('2019-11-03');
CREATE TABLE IF NOT EXISTS fact_event_20191103 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-03') TO ('2019-11-04');
CREATE TABLE IF NOT EXISTS fact_event_20191104 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-04') TO ('2019-11-05');
CREATE TABLE IF NOT EXISTS fact_event_20191105 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-05') TO ('2019-11-06');
CREATE TABLE IF NOT EXISTS fact_event_20191106 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-06') TO ('2019-11-07');
CREATE TABLE IF NOT EXISTS fact_event_20191107 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-07') TO ('2019-11-08');
CREATE TABLE IF NOT EXISTS fact_event_20191108 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-08') TO ('2019-11-09');
CREATE TABLE IF NOT EXISTS fact_event_20191109 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-09') TO ('2019-11-10');
CREATE TABLE IF NOT EXISTS fact_event_20191110 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-10') TO ('2019-11-11');
CREATE TABLE IF NOT EXISTS fact_event_20191111 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-11') TO ('2019-11-12');
CREATE TABLE IF NOT EXISTS fact_event_20191112 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-12') TO ('2019-11-13');
CREATE TABLE IF NOT EXISTS fact_event_20191113 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-13') TO ('2019-11-14');
CREATE TABLE IF NOT EXISTS fact_event_20191114 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-14') TO ('2019-11-15');
CREATE TABLE IF NOT EXISTS fact_event_20191115 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-15') TO ('2019-11-16');
CREATE TABLE IF NOT EXISTS fact_event_20191116 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-16') TO ('2019-11-17');
CREATE TABLE IF NOT EXISTS fact_event_20191117 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-17') TO ('2019-11-18');
CREATE TABLE IF NOT EXISTS fact_event_20191118 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-18') TO ('2019-11-19');
CREATE TABLE IF NOT EXISTS fact_event_20191119 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-19') TO ('2019-11-20');
CREATE TABLE IF NOT EXISTS fact_event_20191120 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-20') TO ('2019-11-21');
CREATE TABLE IF NOT EXISTS fact_event_20191121 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-21') TO ('2019-11-22');
CREATE TABLE IF NOT EXISTS fact_event_20191122 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-22') TO ('2019-11-23');
CREATE TABLE IF NOT EXISTS fact_event_20191123 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-23') TO ('2019-11-24');
CREATE TABLE IF NOT EXISTS fact_event_20191124 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-24') TO ('2019-11-25');
CREATE TABLE IF NOT EXISTS fact_event_20191125 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-25') TO ('2019-11-26');
CREATE TABLE IF NOT EXISTS fact_event_20191126 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-26') TO ('2019-11-27');
CREATE TABLE IF NOT EXISTS fact_event_20191127 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-27') TO ('2019-11-28');
CREATE TABLE IF NOT EXISTS fact_event_20191128 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-28') TO ('2019-11-29');
CREATE TABLE IF NOT EXISTS fact_event_20191129 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-29') TO ('2019-11-30');
CREATE TABLE IF NOT EXISTS fact_event_20191130 PARTITION OF fact_event
    FOR VALUES FROM ('2019-11-30') TO ('2019-12-01');
-- DEFAULT loader partition: catches 2019-12-01 partial day and any future replays.
CREATE TABLE IF NOT EXISTS fact_event_default  PARTITION OF fact_event DEFAULT;

-- ── fact_session_funnel (accumulating snapshot) ───────────────────────────────
-- One row per (user_session, session_date).
-- Tracks the highest funnel stage reached and timing between stages.
-- BR2 reads this table.
CREATE TABLE IF NOT EXISTS fact_session_funnel (
    session_sk              BIGSERIAL     PRIMARY KEY,
    user_session            VARCHAR(50)   NOT NULL,
    session_date            DATE          NOT NULL,
    user_sk                 BIGINT        REFERENCES dim_user(user_sk),
    date_key                INTEGER       REFERENCES dim_date(date_key),
    funnel_stage            SMALLINT      NOT NULL DEFAULT 1,
                                          -- 1=view only, 2=reached cart, 3=purchased
    first_view_at           TIMESTAMPTZ,
    first_cart_at           TIMESTAMPTZ,
    first_purchase_at       TIMESTAMPTZ,
    view_to_cart_sec        NUMERIC(10,2),   -- seconds from first view to first cart; NULL if no cart
    cart_to_purchase_sec    NUMERIC(10,2),   -- seconds from first cart to purchase; NULL if no purchase
    is_abandoned            BOOLEAN       NOT NULL DEFAULT FALSE,
                                          -- TRUE when funnel_stage=2 and no purchase in session
    CONSTRAINT uq_fact_session_funnel_session
        UNIQUE (user_session, session_date)
);

-- Index for BR2 date-range queries
CREATE INDEX IF NOT EXISTS idx_fact_session_funnel_date_key
    ON fact_session_funnel (date_key);
CREATE INDEX IF NOT EXISTS idx_fact_session_funnel_stage
    ON fact_session_funnel (funnel_stage, session_date);

-- ── fact_inventory_daily (periodic snapshot) ──────────────────────────────────
-- One row per (inventory_date, warehouse_id, product_id).
-- LIST-partitioned by warehouse_id (5 warehouses).
-- BR6 reads this table.
--
-- IMPORTANT: stock_on_hand is SEMI-ADDITIVE.
--   ✓ SUM(stock_on_hand) across warehouse_id on ONE date = total stock that day.
--   ✗ SUM(stock_on_hand) across multiple dates = meaningless double-counting.
--   The BR6 fixture and API must enforce this with a single-date filter.
CREATE TABLE IF NOT EXISTS fact_inventory_daily (
    inventory_sk        BIGSERIAL,
    inventory_date      DATE          NOT NULL,   -- the snapshot date
    warehouse_id        INTEGER       NOT NULL REFERENCES dim_warehouse(warehouse_id),
    product_sk          BIGINT        REFERENCES dim_product(product_sk),
    product_id          BIGINT        NOT NULL,   -- denormalized for Cassandra parity
    date_key            INTEGER       REFERENCES dim_date(date_key),
    stock_on_hand       INTEGER       NOT NULL CHECK (stock_on_hand >= 0),
    velocity_7d         NUMERIC(10,4) NOT NULL DEFAULT 0,
                                      -- average daily sales in the past 7 days
    days_to_stockout    NUMERIC(10,2) NOT NULL DEFAULT 9999,
                                      -- stock_on_hand / velocity_7d; 9999 when velocity=0
    reorder_point       INTEGER       NOT NULL DEFAULT 0,
    is_below_reorder    BOOLEAN       NOT NULL DEFAULT FALSE,
    PRIMARY KEY (inventory_sk, warehouse_id)
) PARTITION BY LIST (warehouse_id);

-- One partition per warehouse
CREATE TABLE IF NOT EXISTS fact_inventory_daily_wh1 PARTITION OF fact_inventory_daily
    FOR VALUES IN (1);
CREATE TABLE IF NOT EXISTS fact_inventory_daily_wh2 PARTITION OF fact_inventory_daily
    FOR VALUES IN (2);
CREATE TABLE IF NOT EXISTS fact_inventory_daily_wh3 PARTITION OF fact_inventory_daily
    FOR VALUES IN (3);
CREATE TABLE IF NOT EXISTS fact_inventory_daily_wh4 PARTITION OF fact_inventory_daily
    FOR VALUES IN (4);
CREATE TABLE IF NOT EXISTS fact_inventory_daily_wh5 PARTITION OF fact_inventory_daily
    FOR VALUES IN (5);

-- Unique constraint: one snapshot per (date, warehouse, product)
CREATE UNIQUE INDEX IF NOT EXISTS uq_fact_inventory_daily
    ON fact_inventory_daily (inventory_date, warehouse_id, product_id);
CREATE INDEX IF NOT EXISTS idx_fact_inventory_daily_date_key
    ON fact_inventory_daily (date_key, warehouse_id);
CREATE INDEX IF NOT EXISTS idx_fact_inventory_daily_stockout
    ON fact_inventory_daily (warehouse_id, days_to_stockout);

-- ══════════════════════════════════════════════════════════════════════════════
-- 3. VERIFICATION QUERIES (run manually or via EXPLAIN to produce evidence files)
-- ══════════════════════════════════════════════════════════════════════════════

-- Save one of these as docs/evidence/explain_fact_event_partition.txt:
--
-- EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
-- SELECT COUNT(*) FROM fact_event WHERE event_date = '2019-11-29';
--
-- EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
-- SELECT p.product_id, p.brand, p.category_l1
-- FROM   dim_product p
-- WHERE  p.attributes @> '{"brand": "samsung"}'::jsonb
--   AND  p.is_current = TRUE;
--
-- EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
-- SELECT f.funnel_stage, f.view_to_cart_sec, f.cart_to_purchase_sec, f.is_abandoned
-- FROM   fact_session_funnel f
-- WHERE  f.session_date BETWEEN '2019-11-01' AND '2019-11-30';
