# Benchmark — Ghi chú máy đo và nguồn dữ liệu

## Máy đo (W41 — đo lần đầu)

| Thông số | Giá trị |
|---|---|
| Host OS | Windows 11, WSL2 Ubuntu 24.04 |
| CPU | 12 nhân (AMD Ryzen 5 5600X hoặc tương đương) |
| RAM | 15 GB phân bổ cho WSL2 |
| Ổ đĩa | SSD NVMe |
| Docker | 27.x, không cấp GPU |
| PostgreSQL | 16.15 (image `postgres:16`), container `shopinsight-postgres` |
| Cassandra | 4.1 (image `cassandra:4.1`), container `shopinsight-cassandra` |
| DuckDB | 0.10.x (Python package), chạy in-process |
| Spark | 3.5.x (local[*]), chạy qua `processing/streaming_gold.py` |

## Nguồn dữ liệu PostgreSQL và star schema

- **Silver** (`data/silver/`): sinh bởi `processing/batch_silver.py` từ `data/raw/2019-Nov.csv`.  
  Không có benchmark nào đọc thẳng CSV thô.
- **Star schema PostgreSQL** (`warehouse/ddl.sql`): nạp bởi `serving/load_star_postgres.py`.  
  Các bảng thực thể (`fact_event`, `fact_session_funnel`, `fact_inventory_daily`) và các bảng chiều (`dim_product`, `dim_user`, `dim_date`) đều đọc từ silver.
- **Star schema Parquet** (`data/warehouse/`): sinh bởi `processing/batch_warehouse.py`.  
  DuckDB đọc thư mục này với `hive_partitioning=true`.
- **Cassandra** (`shopinsight` keyspace): nạp bởi `processing/streaming_gold.py` (nhánh thời gian thực) và `processing/batch_gold.py` (BR6).

## Ghi chú đo lường

- Mỗi truy vấn chạy **10 lần** (3 lần warm-up không tính vào kết quả), lấy lần 5 làm p50 và lần 10 làm p95 sau khi sắp xếp tăng dần.
- PostgreSQL: dùng `EXPLAIN (ANALYZE, BUFFERS)` để lấy `Execution Time` thực tế và số buffers đọc.
- Cassandra: dùng `TRACING ON` để lấy `source_elapsed` ở dòng `Request complete`.
- DuckDB: dùng `time.perf_counter()` bao quanh `con.execute().fetchone()`.

## Kế hoạch cập nhật W44

Khi đo lần chính thức trên **máy demo** ở W44:
1. Chạy lại tất cả lệnh trong `w41_benchmark_queries.md` trên máy demo.
2. Ghi đè cột `p50_ms` và `p95_ms` trong `w41_benchmark_results.csv` bằng số mới.
3. Cập nhật bảng "Máy đo" trong file này với thông số phần cứng máy demo.
4. Commit với message: `chore(benchmark): update W44 official benchmark numbers`.

File `w41_benchmark_results.csv` là nguồn số duy nhất cho report mục 4.4.  
Mọi con số trong report phải trích dẫn file này, không trích dẫn thẳng evidence files.

## Biểu đồ trực quan hoá (W42 Task 100 — Slide 5 / Report 4.4)

Biểu đồ so sánh 4 cấu hình với trục tung thang logarit (`log10`) được tạo tự động bởi:
- Script: `benchmark/plot_benchmark.py`
- Ảnh kết quả: `benchmark/results/w41_benchmark_comparison.png`
- Nền tảng kiểm chứng DuckDB Star: `benchmark/verify_duckdb_star.py`
Biểu đồ này sẵn sàng để Nguyên nhúng vào **Slide mục 5** và Khang đưa vào **Report mục 4.4**.
