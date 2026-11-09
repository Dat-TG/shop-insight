# Benchmark — Ghi chú máy đo và nguồn dữ liệu

## Máy đo

Đo trên máy của Đắt, cấu hình ghi trong file env của lần chạy. File này không ghi CPU, RAM
hay ổ đĩa đoán trước.

Phiên bản phần mềm cố định theo repo:

| Thành phần | Phiên bản |
|---|---|
| PostgreSQL | 16.15 (image `postgres:16.15` trong `docker-compose.yml`), container `shopinsight-postgres` |
| Cassandra | 4.1.12 (image `cassandra:4.1.12` trong `docker-compose.yml`), container `shopinsight-cassandra` |
| DuckDB | 1.5.5 (`duckdb==1.5.5` trong `requirements.txt`), chạy in-process |
| PySpark | 4.1.3 (`pyspark==4.1.3`), `local[*]`, chỉ dùng để dựng dữ liệu |
| Driver Python | `cassandra-driver==3.30.1`, `psycopg2-binary==2.9.13` |

## Nguồn dữ liệu PostgreSQL và star schema

- **Silver** (`data/silver/`): sinh bởi `processing/batch_silver.py` từ bronze, mà bronze do
  `ingestion/load_bronze.py` nạp từ `data/raw/2019-Nov.csv`. Không có benchmark nào đọc thẳng CSV thô.
- **Star schema Parquet** (`data/warehouse/`): sinh bởi `processing/batch_warehouse.py` từ silver.
  DuckDB đọc thư mục này với `hive_partitioning=true`.
- **Star schema PostgreSQL** (`warehouse/ddl.sql`): bước 6 của `processing/batch_warehouse.py` đọc
  lại các bảng star vừa ghi ra Parquet và nạp vào PostgreSQL qua các hàm trong
  `serving/load_star_postgres.py`. Ba bảng chiều nhỏ (`dim_date`, `dim_event_type`,
  `dim_warehouse`) được dựng từ dòng Python trong chính file đó (`dim_date` lấy ngày lễ từ
  `seed/holidays_2019.csv`), không đọc từ silver.
- **Không có bảng phẳng:** cả hai cấu hình PostgreSQL chạy trên `fact_event` của star schema.
- **Cassandra** (keyspace `shopinsight`): nạp bởi `processing/streaming_gold.py` (BR1, BR3, BR5,
  BR8) và `processing/batch_gold.py` (BR6).

## Ghi chú đo lường

- Mỗi truy vấn chạy 3 lần khởi động (bỏ đi) rồi 20 lần đo, lấy median làm p50 và percentile
  thứ 95 làm p95. Với ít lần đo hơn, "p95" chỉ là giá trị lớn nhất.
- PostgreSQL: `EXPLAIN (ANALYZE, BUFFERS)` cho biết plan và số buffers đọc.
- Cassandra: `TRACING ON` cho biết `source_elapsed` ở dòng `Request complete`.
- DuckDB: `time.perf_counter()` bao quanh `con.execute(sql).fetchone()`.
- Các số từng có trong `w41_benchmark_results.csv` (đã xoá) là số chép thủ công từ một lần
  chạy trong evidence files, không phải p50/p95. Không trích dẫn chúng.

## Số chính thức

Số p50/p95 do `benchmark/run_benchmark.py` đo (task T12: 3 lần khởi động + 20 lần đo cho mỗi
câu) và ghi ra `benchmark/results/summary_<timestamp>.csv`, cột
`system,query,variant,runs,p50_ms,p95_ms`. File summary mới nhất là nguồn số duy nhất cho
report mục 4.4; mọi con số trong report trích dẫn file đó, không trích thẳng evidence files.

## Biểu đồ (Slide 5 / Report 4.4)

- `benchmark/plot_benchmark.py` đọc `summary_*.csv` mới nhất và ghi
  `benchmark/results/benchmark_comparison.png` (trục tung log, cột p50, râu p95). matplotlib
  không có trong `requirements.txt`; cài nó trong một venv riêng (docstring của script ghi cách).
- `benchmark/verify_duckdb_star.py` kiểm tra DuckDB đọc được cả 8 bảng star trong `data/warehouse/`
  và số dòng khớp với lần build hiện tại.
