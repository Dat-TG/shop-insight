# Benchmark — Câu truy vấn và lệnh đo 4 cấu hình

File này chỉ ghi **câu truy vấn** và **lệnh chạy** của từng cấu hình. Nó không chứa số đo nào.
Mọi số p50/p95 do `benchmark/run_benchmark.py` đo (task T12: 3 lần khởi động + 20 lần đo cho
mỗi câu) và ghi ra `benchmark/results/summary_<timestamp>.csv`.

## Phiên bản phần mềm

| Thành phần | Phiên bản |
|---|---|
| PostgreSQL | 16.15 (image `postgres:16.15`), container `shopinsight-postgres` |
| Cassandra | 4.1.12 (image `cassandra:4.1.12`), container `shopinsight-cassandra` |
| DuckDB | 1.5.5 (`duckdb==1.5.5` trong `requirements.txt`), chạy trong process Python |
| PySpark | 4.1.3 (`pyspark==4.1.3`), chỉ dùng để dựng dữ liệu, không đo ở đây |
| Driver Python | `cassandra-driver==3.30.1`, `psycopg2-binary==2.9.13` |
| Dữ liệu nạp | Silver và star schema — không phải CSV thô |

Máy đo: xem `w41_benchmark_environment.md`.

> **Nguồn dữ liệu PostgreSQL và DuckDB:** tầng silver (`data/silver/`) được sinh bởi `batch_silver.py`, kho dữ liệu dạng star schema (`data/warehouse/`) được sinh bởi `batch_warehouse.py`, và bước 6 của nó nạp cùng các bảng đó vào PostgreSQL. Không có truy vấn nào đọc thẳng `data/raw/2019-Nov.csv`.

> **Không có bảng phẳng.** Repo không có bảng phẳng nào nạp từ silver. Cả hai cấu hình
> PostgreSQL (1 và 2) đều chạy trên bảng `fact_event` của star schema (partition theo
> `event_date`, `warehouse/ddl.sql`). Tên "Postgres không index / có index" chỉ nói về việc
> planner có được dùng index hay không, không phải hai bảng khác nhau.

---

## Cấu hình 1 — Postgres `fact_event` (star), không dùng index

**Bảng:** `fact_event` (partition theo ngày). `warehouse/ddl.sql` đã tạo sẵn index
`ix_fact_event_purchase (event_date, event_type_key, event_time)`, nên cấu hình này **tắt
index cho phiên đo** bằng `SET`, không xoá index và không sửa bảng. Cấu hình này chạy đúng
hai truy vấn A và B của cấu hình 2 (xem bên dưới), chỉ khác ba lệnh `SET` ở đầu phiên.

```sql
SET enable_indexscan = off;
SET enable_bitmapscan = off;
SET enable_indexonlyscan = off;
-- rồi chạy truy vấn A và truy vấn B của cấu hình 2
```

Ghi chú đọc kết quả: với truy vấn A, `EXPLAIN` (không ANALYZE) chạy ngày 10/11/2026 cho ra
cùng một plan `Seq Scan on fact_event_20191129` dù bật hay tắt index, vì mọi dòng của
partition đó đều khớp `event_date = '2019-11-29'`; partition pruning đã làm hết việc. Khác
biệt có/không index nằm ở truy vấn B: bật index thì planner dùng `Bitmap Index Scan` trên
`fact_event_20191129_user_sk_event_time_idx` (index một phần `ix_fact_event_user`,
`WHERE event_type_key = 3`) + `Nested Loop` với `dim_product`, tắt index thì `Parallel Seq Scan` + `Parallel Hash Join`.

### Lệnh chạy

```bash
# Truy vấn A, tắt index
docker exec -i shopinsight-postgres \
  psql -X -U shopinsight -d shopinsight \
  -c "SET enable_indexscan = off; SET enable_bitmapscan = off; SET enable_indexonlyscan = off;" \
  -c "EXPLAIN (ANALYZE, BUFFERS) SELECT count(*) FROM fact_event WHERE event_date = '2019-11-29';"

# Truy vấn B, tắt index
docker exec -i shopinsight-postgres \
  psql -X -U shopinsight -d shopinsight \
  -c "SET enable_indexscan = off; SET enable_bitmapscan = off; SET enable_indexonlyscan = off;" \
  -c "EXPLAIN (ANALYZE, BUFFERS)
      SELECT p.category_l1, sum(f.price)
      FROM fact_event f JOIN dim_product p ON p.product_sk = f.product_sk
      WHERE f.event_date = '2019-11-29' AND f.event_type_key = 3
      GROUP BY p.category_l1 ORDER BY sum(f.price) DESC;"
```

### Kết quả

Số p50/p95 do `benchmark/run_benchmark.py` đo (task T12: 3 lần khởi động + 20 lần đo cho mỗi câu), ghi trong `benchmark/results/summary_<timestamp>.csv`.

---

## Cấu hình 2 — Postgres `fact_event` (star), có index

**Bảng:** cùng bảng `fact_event` của cấu hình 1, planner được dùng index như mặc định. Trên
partition `fact_event_20191129`, `ix_fact_event_purchase` có tên
`fact_event_20191129_event_date_event_type_key_event_time_idx`.

### Truy vấn A: đếm sự kiện ngày Black Friday

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT count(*)
FROM fact_event
WHERE event_date = '2019-11-29';
```

### Truy vấn B: doanh thu theo ngành hàng (star join)

```sql
EXPLAIN (ANALYZE, BUFFERS)
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

### Kết quả

Số p50/p95 do `benchmark/run_benchmark.py` đo (task T12: 3 lần khởi động + 20 lần đo cho mỗi câu), ghi trong `benchmark/results/summary_<timestamp>.csv`.

---

## Cấu hình 3 — Cassandra khoá phân vùng đúng / sai

**Bảng:** `shopinsight.gmv_by_minute`

Partition key: `(event_date, category_l1)` — clustering key: `window_start DESC`.

Hai truy vấn hỏi cùng một câu hỏi trên cùng bảng: GMV từng phút của ngành hàng `'all'`.
Khác nhau ở chỗ câu "khoá đúng" đưa đủ partition key, còn câu "khoá sai" chỉ lọc
`category_l1` (một nửa partition key), nên Cassandra từ chối nếu thiếu `ALLOW FILTERING`.

### Truy vấn đúng khoá (một partition)

```cql
TRACING ON;
SELECT *
FROM shopinsight.gmv_by_minute
WHERE event_date   = '2019-11-17'
  AND category_l1  = 'all'
LIMIT 60;
```

### Truy vấn sai khoá (chỉ lọc `category_l1`, `ALLOW FILTERING`)

```cql
TRACING ON;
SELECT *
FROM shopinsight.gmv_by_minute
WHERE category_l1 = 'all'
LIMIT 60
ALLOW FILTERING;
```

### Lệnh chạy

```bash
# Khoá đúng
docker exec -it shopinsight-cassandra \
  cqlsh -e "TRACING ON;
             SELECT * FROM shopinsight.gmv_by_minute
             WHERE event_date='2019-11-17' AND category_l1='all'
             LIMIT 60;"

# Khoá sai
docker exec -it shopinsight-cassandra \
  cqlsh -e "TRACING ON;
             SELECT * FROM shopinsight.gmv_by_minute
             WHERE category_l1='all'
             LIMIT 60 ALLOW FILTERING;"
```

### Kết quả

Số p50/p95 do `benchmark/run_benchmark.py` đo (task T12: 3 lần khởi động + 20 lần đo cho mỗi câu), ghi trong `benchmark/results/summary_<timestamp>.csv`.

---

## Cấu hình 4 — DuckDB trên Parquet star schema

**Nguồn:** `data/warehouse/fact_event/**/*.parquet` (hive-partitioned theo `event_date`).

### Truy vấn A: filter theo event_time (không qua partition key)

```python
import duckdb
duckdb.sql("""
  SELECT sum(price)
  FROM read_parquet('data/warehouse/fact_event/**/*.parquet', hive_partitioning=true)
  WHERE event_time >= TIMESTAMP '2019-11-29 12:00:00'
    AND event_time <  TIMESTAMP '2019-11-29 13:00:00'
""").fetchone()
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

Hai câu trên được `benchmark/run_benchmark.py` chạy trong process Python, đo bằng
`time.perf_counter()` bao quanh `con.execute(sql).fetchone()`. Muốn xem DuckDB đọc bao nhiêu
file, thêm `EXPLAIN ANALYZE` trước `SELECT` và đọc dòng `Total Files Read`.

### Kết quả

Số p50/p95 do `benchmark/run_benchmark.py` đo (task T12: 3 lần khởi động + 20 lần đo cho mỗi câu), ghi trong `benchmark/results/summary_<timestamp>.csv`.
