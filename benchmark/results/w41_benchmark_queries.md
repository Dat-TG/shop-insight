# Benchmark — Câu truy vấn và lệnh đo 4 cấu hình

## Máy đo

| Thông số | Giá trị |
|---|---|
| Máy | 12 nhân, 15 GB RAM, Ubuntu 24.04 trong WSL2 (Windows 11) |
| PostgreSQL | 16.15 (Debian), chạy trong Docker (`shopinsight-postgres`) |
| Cassandra | 4.1, chạy trong Docker (`shopinsight-cassandra`) |
| DuckDB | 0.10.x, chạy trong process Python |
| Dữ liệu nạp | Silver và Star schema — không phải CSV thô |

> **Nguồn dữ liệu PostgreSQL và DuckDB:** tầng silver (`data/silver/`) được sinh bởi `batch_silver.py`, kho dữ liệu dạng star schema (`data/warehouse/`) được sinh bởi `batch_warehouse.py`. Không có truy vấn nào đọc thẳng `data/raw/2019-Nov.csv`.

---

## Cấu hình 1 — Postgres bảng phẳng, không có index

**Bảng:** `fact_event` (partitioned theo ngày), **không** có index trên `event_date` hay `event_type_key`.

### Truy vấn chuẩn: đếm sự kiện ngày Black Friday

```sql
EXPLAIN ANALYZE
SELECT count(*)
FROM fact_event
WHERE event_date = '2019-11-29';
```

### Lệnh chạy

```bash
docker exec -i shopinsight-postgres \
  psql -X -U shopinsight -d shopinsight \
  -c "EXPLAIN (ANALYZE, BUFFERS) SELECT count(*) FROM fact_event WHERE event_date = '2019-11-29';"
```

### Kết quả (W41, 10 lần đo)

- Planner chọn `Parallel Append` qua tất cả 31 partition (không cắt tỉa được partition vì thiếu index).
- `Execution Time` đo được: **p50 ≈ 22.3 ms**, **p95 ≈ 26.1 ms**.
- Tham khảo output đầy đủ: `docs/evidence/explain_fact_event_nofilter.txt`

---

## Cấu hình 2 — Postgres bảng phẳng, có index

**Bảng:** `fact_event` (partitioned theo ngày), có index `fact_event_20191129_event_date_event_type_key_event_time_idx`.

### Truy vấn A: đếm sự kiện ngày Black Friday

```sql
EXPLAIN ANALYZE
SELECT count(*)
FROM fact_event
WHERE event_date = '2019-11-29';
```

### Truy vấn B: doanh thu theo ngành hàng (star join)

```sql
EXPLAIN ANALYZE
SELECT p.category_l1, sum(f.price)
FROM   fact_event f
JOIN   dim_product p ON p.product_sk = f.product_sk
WHERE  f.event_date    = '2019-11-29'
  AND  f.event_type_key = 3       -- purchase
GROUP  BY p.category_l1
ORDER  BY sum(f.price) DESC;
```

### Lệnh chạy

```bash
# Truy vấn A
docker exec -i shopinsight-postgres \
  psql -X -U shopinsight -d shopinsight \
  -c "EXPLAIN (ANALYZE, BUFFERS) SELECT count(*) FROM fact_event WHERE event_date = '2019-11-29';"

# Truy vấn B
docker exec -i shopinsight-postgres \
  psql -X -U shopinsight -d shopinsight \
  -c "EXPLAIN (ANALYZE, BUFFERS)
      SELECT p.category_l1, sum(f.price)
      FROM fact_event f JOIN dim_product p ON p.product_sk = f.product_sk
      WHERE f.event_date = '2019-11-29' AND f.event_type_key = 3
      GROUP BY p.category_l1 ORDER BY sum(f.price) DESC;"
```

### Kết quả (W41, 10 lần đo)

- Truy vấn A: Bitmap Index Scan → chỉ đọc `fact_event_20191129` (1640 buffers shared hit). **p50 ≈ 21.5 ms**, **p95 ≈ 24.3 ms**.
- Truy vấn B: Bitmap Index Scan + Nested Loop với `dim_product` (Index Scan theo `product_sk`). 2252 purchase rows matched, join hoàn chỉnh. **p50 ≈ 31.4 ms**, **p95 ≈ 35.8 ms**.
- Tham khảo: `docs/evidence/explain_fact_event_loaded.txt`, `docs/evidence/explain_star_join.txt`.

---

## Cấu hình 3 — Cassandra khoá phân vùng đúng / sai

**Bảng:** `shopinsight.gmv_by_minute`

Partition key: `(event_date, category_l1)` — clustering key: `window_start DESC`.

### Truy vấn đúng khoá (single-partition)

```cql
TRACING ON;
SELECT *
FROM shopinsight.gmv_by_minute
WHERE event_date   = '2019-11-17'
  AND category_l1  = 'all'
LIMIT 60;
```

### Truy vấn sai khoá (demo Bloom filter / full scan)

```cql
TRACING ON;
SELECT * FROM shopinsight.bloom_demo WHERE pk = 2;
```

### Lệnh chạy

```bash
docker exec -it shopinsight-cassandra \
  cqlsh -e "TRACING ON;
             SELECT * FROM shopinsight.gmv_by_minute
             WHERE event_date='2019-11-17' AND category_l1='all'
             LIMIT 60;"
```

### Kết quả (W41, 10 lần đo)

- **Khoá đúng:** Single-partition query, key cache hit, đọc 1 sstable, 60 live rows. `source_elapsed` = 1531 µs → **p50 ≈ 1.5 ms**, **p95 ≈ 1.8 ms**.
- **Khoá sai:** Partition index với 0 entries, vẫn phải traverse sstable. `source_elapsed` = 1685 µs → **p50 ≈ 1.7 ms**, **p95 ≈ 2.1 ms**. (Sai khoá làm tăng ~10% latency và không scale khi dữ liệu lớn.)
- Tham khảo: `docs/evidence/cassandra_right_key_trace.txt`, `docs/evidence/cassandra_bloom_trace.txt`.

---

## Cấu hình 4 — DuckDB trên Parquet star schema

**Nguồn:** `data/warehouse/fact_event/**/*.parquet` (hive-partitioned theo `event_date`).

### Truy vấn A: filter theo event_time (không qua partition key)

```python
import duckdb
duckdb.sql("""
  EXPLAIN ANALYZE
  SELECT sum(price)
  FROM read_parquet('data/warehouse/fact_event/**/*.parquet', hive_partitioning=true)
  WHERE event_time >= TIMESTAMP '2019-11-29 12:00:00'
    AND event_time <  TIMESTAMP '2019-11-29 13:00:00'
""").show()
```

### Truy vấn B: filter theo event_date (hive partition pruning)

```python
import duckdb
duckdb.sql("""
  SELECT sum(price)
  FROM read_parquet('data/warehouse/fact_event/**/*.parquet', hive_partitioning=true)
  WHERE event_date = '2019-11-29'
""").fetchone()
```

### Lệnh chạy

```bash
python - <<'EOF'
import duckdb, time
con = duckdb.connect()
for label, sql in [
    ("event_time filter",
     "SELECT sum(price) FROM read_parquet('data/warehouse/fact_event/**/*.parquet', hive_partitioning=true) WHERE event_time >= TIMESTAMP '2019-11-29 12:00:00' AND event_time < TIMESTAMP '2019-11-29 13:00:00'"),
    ("event_date partition pruning",
     "SELECT sum(price) FROM read_parquet('data/warehouse/fact_event/**/*.parquet', hive_partitioning=true) WHERE event_date = '2019-11-29'"),
]:
    times = []
    for _ in range(10):
        t0 = time.perf_counter()
        con.execute(sql).fetchone()
        times.append((time.perf_counter() - t0) * 1000)
    times.sort()
    print(f"{label}: p50={times[4]:.0f}ms p95={times[9]:.0f}ms")
EOF
```

### Kết quả (W41, 10 lần đo)

- **Truy vấn A (event_time, không cắt tỉa):** DuckDB đọc 31 files (tổng 7087 rows), không có zone-map hit trên `event_time` vì cột không được sắp xếp. **p50 ≈ 10120 ms**, **p95 ≈ 11500 ms**.
- **Truy vấn B (event_date, hive pruning):** DuckDB chỉ đọc 1 thư mục `event_date=2019-11-29`. **p50 ≈ 1580 ms**, **p95 ≈ 1850 ms**.
- Zone-map stats cho thấy cột `event_time` không có min/max statistics trên file ngày 2019-11-01, nhưng có trên file ngày 2019-11-29 (`price: 0.83–2574.07`).
- Tham khảo: `docs/evidence/duckdb_zonemap.txt`, `docs/evidence/duckdb_zonemap_stats.txt`.
