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
| Cassandra | 4.1.12 (image `cassandra:4.1.12`), container `shopinsight-cassandra` |
| DuckDB | 1.5.5 (Python package `duckdb==1.5.5`), chạy in-process |
| PySpark | 4.1.3 (`pyspark==4.1.3`), local[*] |

## Nguồn dữ liệu PostgreSQL và star schema

- **Silver** (`data/silver/`): sinh bởi `processing/batch_silver.py` từ `data/raw/2019-Nov.csv`.  
  Không có benchmark nào đọc thẳng CSV thô.
- **Star schema PostgreSQL** (`warehouse/ddl.sql`): nạp bởi `serving/load_star_postgres.py`.  
  Các bảng thực thể (`fact_event`, `fact_session_funnel`, `fact_inventory_daily`) và các bảng chiều (`dim_product`, `dim_user`, `dim_date`) đều đọc từ silver.
- **Star schema Parquet** (`data/warehouse/`): sinh bởi `processing/batch_warehouse.py`.  
  DuckDB đọc thư mục này với `hive_partitioning=true`.
- **Cassandra** (`shopinsight` keyspace): nạp bởi `processing/streaming_gold.py` (nhánh thời gian thực) và `processing/batch_gold.py` (BR6).

## Ghi chú đo lường

- Mỗi truy vấn cần chạy **tối thiểu 20 lần** (bỏ 3 lần warm-up đầu), lấy median làm p50 và percentile thứ 95 làm p95 — khi đó p95 mới có ý nghĩa thống kê.
- PostgreSQL: dùng `EXPLAIN (ANALYZE, BUFFERS)` để lấy `Execution Time` thực tế và số buffers đọc.
- Cassandra: dùng `TRACING ON` để lấy `source_elapsed` ở dòng `Request complete`.
- DuckDB: dùng `time.perf_counter()` bao quanh `con.execute().fetchone()`.
- **Lưu ý:** Các số trong `w41_benchmark_results.csv` (đã xóa) là số trích thủ công từ evidence files, chưa phải kết quả 20 lần chạy. Số chính thức sẽ được sinh ra bởi script `benchmark/run_benchmark.py` (phụ trách: Đắt — T12/T14).

## Kế hoạch cập nhật — Số chính thức

Số p50/p95 chính thức sẽ được đo lần chính thức trên **máy demo** bởi script `benchmark/run_benchmark.py` (T12/T14 — phụ trách: Đắt):
1. Chạy tối thiểu 20 lần mỗi câu truy vấn, ghi kết quả thô ra file (tương tự `batch_timings.txt`).
2. Sinh `w41_benchmark_results.csv` mới từ số liệu thực tế, với cột `runs ≥ 20`.
3. Cập nhật bảng "Máy đo" trong file này với thông số phần cứng máy demo.
4. Regenerate biểu đồ log-scale bằng `benchmark/plot_benchmark.py`.
5. Commit với message: `chore(benchmark): add official 20-run benchmark numbers`.

File `w41_benchmark_results.csv` (khi được tạo lại) sẽ là nguồn số duy nhất cho report mục 4.4.  
Mọi con số trong report phải trích dẫn file này, không trích dẫn thẳng evidence files.

## Biểu đồ trực quan hoá (Slide 5 / Report 4.4)

Biểu đồ so sánh 4 cấu hình với trục tung thang logarit (`log10`) được tạo tự động bởi:
- Script: `benchmark/plot_benchmark.py`
- Nền tảng kiểm chứng DuckDB Star: `benchmark/verify_duckdb_star.py`

> **Lưu ý:** Ảnh `w41_benchmark_comparison.png` đã xóa vì được sinh từ số liệu chưa xác minh.  
> Biểu đồ sẽ được regenerate sau khi có `w41_benchmark_results.csv` chính thức.
