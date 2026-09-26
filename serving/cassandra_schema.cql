-- Cassandra gold tables for ShopInsight.
-- The key choices are fixed to match the screen access pattern and the stale-row
-- behaviour described in SYSTEM_DESIGN.md section 6.

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


