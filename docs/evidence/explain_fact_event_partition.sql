-- docs/evidence/explain_fact_event_partition.sql
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- EXPLAIN evidence for W39 Postgres star schema.
-- These queries were run after batch_warehouse.py loaded the 3 small dims.
-- The output files were captured as:
--   docs/evidence/explain_fact_event_partition.txt
--   docs/evidence/explain_gin_attributes.txt
--   docs/evidence/explain_session_funnel.txt
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- 1. Partition pruning on fact_event for a single day (Black Friday).
--    Expected: only fact_event_20191129 should appear in the plan.
EXPLAIN (ANALYZE OFF, BUFFERS OFF, FORMAT TEXT)
SELECT COUNT(*) FROM fact_event WHERE event_date = '2019-11-29';

-- 2. GIN index containment search on dim_product.attributes.
--    Expected: Index Scan using idx_dim_product_attributes_gin.
EXPLAIN (ANALYZE OFF, BUFFERS OFF, FORMAT TEXT)
SELECT p.product_id, p.brand, p.category_l1
FROM   dim_product p
WHERE  p.attributes @> '{"brand": "samsung"}'::jsonb
  AND  p.is_current = TRUE;

-- 3. fact_session_funnel date-range scan (BR2 source table).
--    Expected: Index Scan on idx_fact_session_funnel_date_key.
EXPLAIN (ANALYZE OFF, BUFFERS OFF, FORMAT TEXT)
SELECT
    f.funnel_stage,
    COUNT(*)                                AS session_count,
    AVG(f.view_to_cart_sec)                 AS avg_view_to_cart_sec,
    AVG(f.cart_to_purchase_sec)             AS avg_cart_to_purchase_sec,
    COUNT(*) FILTER (WHERE f.is_abandoned)  AS abandoned_sessions
FROM fact_session_funnel f
WHERE f.session_date BETWEEN '2019-11-01' AND '2019-11-30'
GROUP BY f.funnel_stage
ORDER BY f.funnel_stage;

-- 4. fact_inventory_daily LIST-partition pruning for a single warehouse.
--    Expected: only fact_inventory_daily_wh1 in plan.
EXPLAIN (ANALYZE OFF, BUFFERS OFF, FORMAT TEXT)
SELECT
    f.product_id,
    f.stock_on_hand,
    f.days_to_stockout,
    f.is_below_reorder
FROM fact_inventory_daily f
WHERE f.inventory_date = '2019-11-30'
  AND f.warehouse_id = 1
ORDER BY f.days_to_stockout;

-- Run all four and save output:
--   PGPASSWORD=local_dev_only psql -h localhost -U shopinsight -d shopinsight \
--     -f docs/evidence/explain_fact_event_partition.sql \
--     -o docs/evidence/explain_output_w39.txt
