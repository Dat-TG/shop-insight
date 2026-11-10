# docs/evidence - what each file is

One line per file in this folder (sprint task T17, written for Tín on 10 Nov 2026). Date, machine and run
count come from each file's own header. Where a file has no header the cell says "not recorded" and,
in brackets, when and by whom git first added it. "Dat's machine" is Dat-Xiaoxin (20 logical cores,
15 GB RAM, Ubuntu 26.04.1 in WSL2).

**Measurement of record (10 Nov 2026, main at 02b22f1):** `t14_checks.txt`, `correctness_8br.txt` (the
T19 section), `gate2b_curl_raw.txt`, `gate2b_screens.txt`, `streaming_perf.txt`, `pg_vs_parquet_counts.txt`
and the benchmark files in `benchmark/results/`. Older files below record how each piece was first shown.
Some ran under other conditions (another machine, Postgres with only 3 days loaded, Parquet files since
rebuilt); the "Data" column says so. Quote today's files for numbers in the report.

| File | Date | Machine | Data | Runs | What it proves |
|---|---|---|---|---|---|
| `README.md` | 2026-11-10 | - | - | - | This index. |
| `batch_timings.txt` | 2026-11-03 20:07-20:14 +07:00, commit aa65472 | Dat's machine | `data/raw/2019-Nov.csv` (8.4G) -> 7% bronze -> silver -> star -> gold | 1 | The one-time batch build, `load_bronze.py` to `gold_br7.py`, takes 426.5 s and every job prints its OK line and passes its checks. |
| `cassandra_bloom_setting.txt` | not recorded (git: 2026-10-10, Nguyên, 7e5130f) | not recorded | `bloom_filter_fp_chance`, `compaction` of one table | 1 query | The Bloom filter false-positive chance is 0.01, with SizeTieredCompactionStrategy. |
| `cassandra_bloom_trace.txt` | 2026-10-08 (cqlsh trace timestamp) | not recorded | scratch table `bloom_demo` | 1 query | A cqlsh trace of a single-partition read on a demo table, for the Bloom filter / SSTable explanation. |
| `cassandra_describe_gmv_by_minute.png` | not recorded (git: 2026-10-09, Khang, 7d0dd25) | not recorded | schema of `gmv_by_minute` | - | Screenshot of `DESCRIBE TABLE gmv_by_minute`, used in REPORT.md section 4.2. |
| `cassandra_describe_trending_products.png` | not recorded (git: 2026-10-09, Khang, 7d0dd25) | not recorded | schema of `trending_products` | - | Screenshot of `DESCRIBE TABLE trending_products`, used in REPORT.md section 4.2. |
| `cassandra_right_key_trace.txt` | 2026-10-08 (cqlsh trace timestamp) | not recorded | `gmv_by_minute`, 17 Nov, `'all'`, LIMIT 60 | 1 query | A query through the partition key is "Executing single-partition query" and reads 60 live rows. Superseded for timing by the benchmark's `cassandra.*` rows. |
| `cassandra_sstable_files.txt` | file times Oct 8 04:11 | not recorded | one table's SSTable directory | - | The component files of one SSTable (Data, Filter, Index, Summary). |
| `cassandra_tablestats.txt` | not recorded (git: 2026-10-10, Nguyên, 7e5130f) | not recorded | one table | - | A table-statistics excerpt (no command recorded): 1 SSTable, 0 Bloom filter false positives. |
| `correctness_8br.txt` | 2026-11-06 (record then); 2026-11-08 (review re-run); 2026-11-10 (T19) | Khang's machine (6 Nov); Dat's machine (8 and 10 Nov) | 78-file replay of 17 Nov 15:00-21:30 Vietnam time, plus batch gold | 1 per date; 2 replays on 10 Nov | Every BR's stored result against an independent DuckDB answer. The 10 Nov nine-row table (BR1-BR8 plus SCD2) is 100% on every row and is the measurement of record; BR4 raw values 90.96% is explained there. 6 and 8 Nov BR8 rows used the old severity thresholds. |
| `dim_user_null_compare.txt` | 2026-10-18 | Khang's machine | `stg_rfm_snapshot`, `dim_user` | not recorded | Why the dim_user version test is null-safe (report section 4.3). |
| `duckdb_zonemap.txt` | not recorded (git: 2026-10-10, Nguyên, 7e5130f) | not recorded | `fact_event` Parquet; the file names it shows no longer exist after the warehouse was rebuilt | 1 | DuckDB reads all 31 files for a one-hour `event_time` filter. Superseded by the benchmark row `duckdb.event_time_one_hour.zonemap`. |
| `duckdb_zonemap_stats.txt` | not recorded (git: 2026-10-10, Nguyên, 7e5130f) | not recorded | one `fact_event` file from that older build | 1 | That file has no min/max for `event_time` and has min/max for `price`. |
| `explain_fact_event_loaded.txt` | not recorded (git: 2026-10-10, Nguyên, 7e5130f) | not recorded | Postgres `fact_event`, 131,796 rows in the 29 Nov partition; how many days were loaded is not recorded | 1 | `EXPLAIN ANALYZE` of a one-day count scans only `fact_event_20191129`. Superseded by the benchmark's `postgres.count_one_day.*`. |
| `explain_fact_event_nofilter.txt` | not recorded (git: 2026-10-10, Nguyên, 7e5130f) | not recorded | Postgres with 3 days of data loaded: the plan itself shows rows only in the 28, 29 and 30 Nov partitions (lines 42-46) | 1 | Without a date filter the plan appends all 31 partitions, most of them empty. |
| `explain_fact_event_partition.sql` | W39 (git: 2026-09-25, Tín, 4f14e58) | - | - | - | The SQL script that produced `explain_output_w39.txt`; not a measurement. |
| `explain_output_w39.txt` | W39 (git: 2026-09-25, Tín, 4f14e58) | not recorded | Postgres star with empty facts | 1 | Planner estimates only (plain EXPLAIN, no ANALYZE): a one-day filter plans only its own partition, and the GIN index is planned for `@>`. Not speed. |
| `explain_star_join.txt` | not recorded (git: 2026-10-10, Nguyên, 7e5130f) | not recorded in the file; Nguyên's machine per Dat's slide notes (docs/PRESENTATION_SLIDES.md line 269, a local file outside the repo history) | Postgres with only 3 days loaded (same commit as `explain_fact_event_nofilter.txt`, whose plan shows rows only for 28-30 Nov) | 1 | The star-join plan: an index scan per fact row (loops=2252). Not comparable with today's full-month Postgres; use `postgres.revenue_by_category.*` in the benchmark. |
| `gate1a_br1_run.txt` | 2026-09-30 | Dat's machine (branch w40-br1-slice) | replay from 17 Nov 08:00 UTC | 1 | Gate 1a: BR1 streams into `gmv_by_minute`, survives a restart without `--fresh`, and matched silver in a one-off comparison (100/100 and 50/50 minutes). |
| `gate1b_br3_run.txt` | 2026-10-01 | Khang's machine (branch w41-khang-br3) | 81-file replay, 15:00-21:45 Vietnam time | 1 | Gate 1b: BR3's top 20 per window, 7,600 of 7,600 rows equal to silver in a one-off DuckDB check; restart and delete-then-insert behaviour. |
| `gate2a_br2_run.txt` | 2026-10-07 | Dat's machine (branch w41-br2-slice) | full batch build | 1 | Gate 2a: BR2's `funnel_daily`, equal to the star on all 465 rows (one-off DuckDB EXCEPT), the API and the screen. |
| `gate2a_br5_run.txt` | 2026-10-12 | Dat's machine (branch w41-nguyen, 2e38359, reviewing PR #26) | 78-file replay, 15:00-21:30 Vietnam time | 1 | Gate 2a: BR5's `abandoned_carts`, 2,600 of 2,600 sessions equal to silver in a one-off DuckDB check, and the API. |
| `gate2b_br1.png` | 2026-11-10 | Dat's machine | after the T14 replay | - | BR1 screen with its QueryMeta footer (Gate 2b). |
| `gate2b_br2.png` | 2026-11-10 | Dat's machine | batch gold | - | BR2 screen with its QueryMeta footer (Gate 2b). |
| `gate2b_br3.png` | 2026-11-10 | Dat's machine | after the T14 replay | - | BR3 screen with its QueryMeta footer (Gate 2b). |
| `gate2b_br4.png` | 2026-11-10 | Dat's machine | batch gold, snapshot 2019-11-30 | - | BR4 screen with its QueryMeta footer, "72.78 ms / Parquet / 1 partition / 31,005 rows": BR4Page.tsx shows the largest ms and partitions of its five parallel calls and the sum of their rows (Gate 2b). |
| `gate2b_br5.png` | 2026-11-10 | Dat's machine | after the T14 replay | - | BR5 screen with its QueryMeta footer (Gate 2b). |
| `gate2b_br6.png` | 2026-11-10 | Dat's machine | `stockout_risk` from batch gold | - | BR6 screen with its QueryMeta footer (Gate 2b). |
| `gate2b_br7.png` | 2026-11-10 | Dat's machine | batch gold | - | BR7 screen with its QueryMeta footer (Gate 2b). |
| `gate2b_br8.png` | 2026-11-10 | Dat's machine | after the T14 replay | - | BR8 screen with its QueryMeta footer and severity cards (Gate 2b). |
| `gate2b_curl_raw.txt` | 2026-11-10 01:14-01:15 (+ BR4 per-R-score calls to 01:30) +07:00, main 02b22f1 | Dat's machine | right after the T14 replay | 3 warm-up + 20 timed per endpoint | Raw per-call QueryMeta ms and curl round trip for the 8 screens' endpoints; all under 2 s. |
| `gate2b_screens.txt` | 2026-11-10, main 02b22f1 | Dat's machine | from `gate2b_curl_raw.txt` | 20 timed per endpoint | Gate 2b summary: one line per screen with store, partitions, p50/p95, under 2 s (all yes) and its screenshot. |
| `gin_index_sizes.txt` | not recorded (git: 2026-10-10, Nguyên, 7e5130f) | not recorded | Postgres `dim_product` | 1 | Size of the GIN index with `jsonb_path_ops` (9672 kB) vs the default operator class (11 MB); table 91 MB. |
| `gin_vs_seqscan.txt` | not recorded (git: 2026-10-10, Nguyên, 7e5130f) | not recorded | Postgres `dim_product`, color crimson_red (21,078 rows) | 1 | GIN bitmap scan vs seq scan for `@>`. Superseded by the benchmark's `postgres.attributes_containment.*`. |
| `ground_truth_run.txt` | 2026-11-06 (PR run); 2026-11-08 (review re-run); 2026-11-10 (T14 run) | not recorded (6 Nov); Dat's machine (8 and 10 Nov) | 78-file replay of 17 Nov 15:00-21:30 (8 and 10 Nov) | 1 per date | `checks/ground_truth.py`: BR4, BR6, BR7, BR8 against a second DuckDB answer, 100% on 10 Nov; the mutations show the check can fail. |
| `perf_table.md` | 2026-11-10 | Dat's machine | from the files it cites | as cited | Vietnamese performance table for report section 6.2: what, how, tool, threshold, result. |
| `pg_vs_parquet_counts.txt` | 2026-11-10 01:17 +07:00, commit 02b22f1 | not recorded in the file; T14 step 5, the T14 session on Dat's machine, as the other T14 files record | the 8 star tables | 1 | Postgres and Parquet hold the same row count for all 8 star tables. |
| `presentation_csv_vs_parquet.txt` | 2026-10-21 21:07 +07:00, commit 78fa4e3 | Dat's machine | 7% sample as CSV vs partitioned silver Parquet | 1 warm-up + 5 timed, median | Same query, same sample: partitioned Parquet vs CSV (E4, deck page 17). |
| `presentation_parquet_run.txt` | 2026-10-20 23:57 +07:00, commit 03394c9 | Dat's machine | silver, 93 files | 1 per query (plans and Spark scan metrics, no timing) | Spark reads 1 of 93 files for one day and type, 9 of 93 with dynamic partition pruning, and all 93 for an hour on `event_time` (INT96, no min/max) (E1). |
| `presentation_price_zonemap.txt` | 2026-10-26 00:07 +07:00, commit cf744d5 | Dat's machine | silver, 93 row groups | 1 (footers only, no query timed) | A price filter cannot skip any silver row group from its min/max (E5). |
| `spark_partition_pruning.txt` | not recorded (git: 2026-10-10, Nguyên, 7e5130f) | not recorded (the plan's path is `/home/ry/Documents/shop-insight`) | silver | 1 | A Spark scan with `PartitionFilters` on `event_type` and `event_date`; 2,252 rows. |
| `star_join_rowcount.txt` | not recorded (git: 2026-10-10, Nguyên, 7e5130f) | not recorded | Postgres star, the data of `explain_star_join.txt` | 1 | The star join loses no fact row: 2,252 purchases, 2,252 joined rows. |
| `streaming_perf.txt` | 2026-11-10, main 02b22f1 | Dat's machine | 78-file replay, 187,468 rows | 2 replays, 78 micro-batches per job each (BR3: 77 in run 2) | Stream throughput keeps up with the offered 480.7 rows/s; micro-batch triggerExecution p50/p95/max per job. Run 1 is the one to quote. |
| `t09_t10_live_checks.txt` | 2026-11-10 01:15-01:23 +07:00, main 02b22f1 | Dat's machine | the T14 replays | 1 | T09: BR1 3/3 and BR2 2/2 of BR_SCOPE's checks on the running system; T10: BR8's first High alert 81 s after the replayer started. |
| `t14_checks.txt` | 2026-11-10 01:16-01:29 +07:00, main 02b22f1 | Dat's machine | 78-file replay plus batch gold | correctness 2 (one per replay); others 1 | Raw output of `correctness_8br.py`, `ground_truth.py`, `scd2_integrity.py` on both SCD2 dimensions and `fact_event_spot.py`; all OK. |
| `t14_logs/` (4 files) | 2026-11-10, replays started 01:06:33 and 01:21:11 | Dat's machine | the two T14 replays | 2 | Timestamped stream and replayer logs that `streaming_perf.txt` was computed from. |

`benchmark/results/`: the official T12 run is `raw_20261110_010557.csv` (every timed run), `summary_20261110_010557.csv`
(p50/p95 per variant), `env_20261110_010557.txt` (machine, versions, row counts), `plans_20261110_010557.txt` (one plan per
variant, 21/21 plan checks OK) and `stdout_20261110_010557.txt`: 2026-11-10 01:05 +07:00, Dat's machine, commit 02b22f1,
3 warm-up + 20 timed runs per variant, Postgres, DuckDB and Cassandra. `w41_benchmark_environment.md` and
`w41_benchmark_queries.md` describe the setup and queries and hold no numbers.
