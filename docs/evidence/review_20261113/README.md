# Extra measurements for the report, 13 Nov 2026

Small read-only scripts behind a few numbers added to the report on 13 Nov 2026. Each reads
`data/` with DuckDB and prints its result; the `.txt` next to it is that output, and its
first line is the command and the run date. They ran on machine 2 at commit `82417f7`, on the
7% sample, except the ones that read `data/raw/2019-Nov.csv` directly.

Rerun one from the repo root after building the data (`docs/SETUP_SPARK.md`):

```
.venv/bin/python -I docs/evidence/review_20261113/<script>.py
```

Timings depend on the machine and the OS page cache; the report uses the ratios.

| Script | What it measures | Report section |
|---|---|---|
| `r1_inventory_waiting.py` | Which BR6 rows the inventory generator planted. | 1-3 |
| `r1_raw_profile.py` | Profile the raw CSV (data/raw/2019-Nov.csv) and the bronze sample for report sections 1 and 3. | 1-3 |
| `r1_raw_scan_timing.py` | Time one parallel engine (DuckDB) answering report 1.3's question on the raw CSV. | 1-3 |
| `r1_rfm_ties.py` | How ntile(5) splits ties in BR4's RFM scores (data/warehouse/stg_rfm_snapshot, snapshot 30/11). | 1-3 |
| `r1_silver_profile.py` | Profile the silver layer (and fact_session_funnel) for report sections 2.8 and 3.1. | 1-3 |
| `r2_brand_drift.py` | How far the streaming branch's labels drift from the warehouse. | 4.1 |
| `r2_lookahead.py` | Size of the look-ahead bias in dim_user for 1-7 Nov. | 4.1 |
| `r3_dim_user_versions.py` | Why dim_user opens new SCD2 versions, and how many events carry a look-ahead segment. | 4.4 |
| `r3_parquet_footer.py` | Parquet footer statistics of fact_event: what row-group skipping can and cannot do. | 4.4 |
| `r3_price_versions.py` | dim_product grain: price versions per change versus per day, and the cost of a range join. | 4.4 |
| `r3_session_funnel.py` | fact_session_funnel: sessions with several users, and sessions that cross midnight. | 4.4 |
| `r4_cpu_per_read.py` | CPU cost of one read: the same query on CSV and on silver Parquet, plus the raw file. | 4.5, 5 |
| `r4_screen_counts.py` | Counts behind the report's section 5.2 screen paragraphs (BR2, BR6, BR7, BR8). | 4.5, 5 |
| `r5_br6_inventory.py` | BR6 on the last day, and where the 32-bit floats of BR6 come from. | 6 |
| `r5_br8_thresholds.py` | How unusual are BR8's alert levels? Purchases per user per 5-minute window, from silver. | 6 |
| `r5_fullcsv.py` | BR2's and BR7's screen questions computed at read time straight from the full raw CSV. | 6 |
| `r5_gold_vs_onthefly.py` | The same screen question answered two ways: read the gold table, or compute it at read time. | 6 |
| `r6_br5_sessions.py` | BR5 abandoned carts: a batch simulation of session_window on silver. | 7 |
| `r6_br8_orders.py` | BR8: purchases per user per 5-minute window under three definitions of an order. | 7 |
| `r6_duplicates.py` | Duplicate events: silver, the 7% bronze sample and the full raw CSV. | 7 |
| `r6_sample_vs_full.py` | Which numbers of the 7% sample carry over to the full file: same SQL on both. | 7 |
| `r7_silver_warehouse_counts.py` | Counts on silver, the warehouse and the replay window that back the source rows of report appendix A. | Appendix A |
