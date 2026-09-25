# Phạm vi 8 BR và định nghĩa XONG — Nhóm 15

Bảng này thay cho buổi họp chốt phạm vi và là checklist để rà tiêu chí Application Implementation (8/10 điểm, mỗi BR demo được khoảng 1 điểm). Đúng 8 BR. BR9 (tra cứu ad-hoc) đã cắt để trả giờ cho tầng kho.

Mỗi người làm trọn ba tầng của BR mình: truy vấn Spark → endpoint API → màn hình React. Mọi màn hình có footer QueryMeta `Truy vấn: <ms> · <kho> · <partitions> · <rows>`; ngưỡng "dưới 2 giây" của Gate 2b đo theo trường `ms` đó.

## Bảng phạm vi

| BR | Người | Tuần | Nhóm người dùng | Câu hỏi | Đọc từ | Bảng kết quả | Màn hình | XONG khi |
|---|---|---|---|---|---|---|---|---|
| BR1 | Đắt | W40 | Ban điều hành | Doanh thu từng phút đang thế nào so với giờ trước? Ngành hàng nào đang kéo? | Luồng: replayer đọc `data/bronze/` → `data/stream_landing/` → `clean()` của silver (không đọc star) | Cassandra `gmv_by_minute` | 4 thẻ số (GMV, đơn, AOV, so với giờ trước) + biểu đồ GMV/phút 60 phút gần nhất, tự làm mới 10 s; lọc ngày, ngành hàng | Khi replayer chạy `--speed 60`, biểu đồ tự thêm điểm mỗi 10 s không cần F5; đổi ngành hàng thì biểu đồ đổi; có chuỗi `unknown`; footer `Cassandra · 1 partition · ≤ 60 dòng`, < 2 s |
| BR2 | Đắt | W41 | Growth & Marketing | Khách rớt khỏi phễu ở bước nào? | `fact_session_funnel` (+ `dim_date`, `dim_event_type`) | Parquet `gold/funnel_daily` | Phễu 3 tầng xem → giỏ → mua + bảng tỉ lệ chuyển đổi theo ngành; lọc khoảng ngày, ngành | Phễu 3 tầng giảm dần; đổi khoảng ngày hoặc ngành thì số đổi; footer `Parquet · số partition = số ngày đã chọn`, < 2 s |
| BR3 | Khang | W41 | Hàng hoá | Sản phẩm nào đang lên trong 15 phút qua? | Luồng: như BR1; cửa sổ 15 phút trượt mỗi phút, top-N tính trong `foreachBatch` | Cassandra `trending_products` | Bảng top 20 có mũi tên lên/xuống hạng so với cửa sổ trước; lọc cửa sổ | Khi replayer chạy, bảng đổi mỗi phút và mũi tên đúng so với cửa sổ trước; mỗi cửa sổ đúng 20 dòng, không trùng hạng; footer `Cassandra · 1 partition · 20 dòng`, < 2 s |
| BR4 | Khang | W40 | Growth & Marketing | Nhóm khách nào đáng đầu tư quảng cáo? | `stg_rfm_snapshot WHERE snapshot_date = <mốc>` (RFM đã tính trong tầng kho, đúng giá trị tại từng mốc; xem mục 7) | Parquet `gold/rfm_segments`, phân vùng theo `snapshot_date` | Heatmap RFM 5×5 + danh sách khách của ô đang chọn; lọc mốc snapshot, phân khúc | Heatmap đủ 25 ô có số; bấm một ô ra danh sách khách của ô đó; lọc mốc 7/14/21/28/30-11 thì số đổi; footer `Parquet`, < 2 s |
| BR5 | Nguyên | W41 | Growth & Marketing | Ai bỏ quên giỏ hàng? | Luồng: như BR1; phiên có `cart` mà 30 phút sau không có `purchase` | Cassandra `abandoned_carts` | Danh sách xếp giảm dần theo giá trị giỏ + nút "tạo chiến dịch" mô phỏng; lọc ngày, giá trị tối thiểu | Khi replayer chạy, danh sách tăng dần trong ngày và không bao giờ tự rỗng; lọc giá trị tối thiểu có tác dụng; bấm "tạo chiến dịch" hiện xác nhận; footer `Cassandra · 1 partition`, < 2 s |
| BR6 | Tín | W40 | Vận hành | SKU nào sắp hết hàng ở kho nào? | `fact_inventory_daily` + lượt mua trong `fact_event` (BR duy nhất sinh từ star rồi ghi sang Cassandra) | Cassandra `stockout_risk` | Bảng SKU tô màu theo số ngày còn hàng, đỏ khi < 3 ngày; lọc kho, ngưỡng ngày | Chọn kho 1–5 ra bảng xếp tăng dần theo số ngày còn hàng, có ít nhất một dòng đỏ; SKU không bán (9999) nằm cuối; footer `Cassandra · 1 partition`, < 2 s |
| BR7 | Nguyên | W40 | Hàng hoá | Mua A thì hay mua kèm gì? | `fact_event` (lượt mua, đồng xuất hiện theo phiên) + `dim_product` | Parquet `gold/product_affinity` | Ô tìm sản phẩm → 10 sản phẩm mua kèm kèm lift; lọc sản phẩm gốc | Nhập `1005115` ra tối đa 10 dòng xếp giảm dần theo lift; mã không có dữ liệu hiện trạng thái rỗng, không báo lỗi; footer `Parquet`, < 2 s |
| BR8 | Tín | W41 | Vận hành & Rủi ro | Tài khoản nào đặt đơn bất thường? | Luồng: như BR1; số đơn mỗi user trong cửa sổ 5 phút, gán mức độ | Cassandra `order_velocity_alerts` | Dòng thời gian cảnh báo theo mức độ, mở ra xem các đơn bên dưới; lọc ngày, mức độ | Khi replayer chạy, cảnh báo mới hiện trên đầu; lọc `high` chỉ còn `high`; mở một cảnh báo ra danh sách đơn; footer `Cassandra · 1 partition`, < 2 s |

## Quyết định và chỗ lệch đã chốt

1. **RFM chụp mỗi tuần**: 7, 14, 21, 28 và 30/11/2019 (5 mốc). Mỗi mốc tính các lần mua tới hết ngày đó. Phiên bản đầu tiên của mỗi người có hiệu lực từ 1/11.
2. **Gán phân khúc theo điểm R và F** (phủ đủ 25 ô, mỗi ô đúng một phân khúc):

   | Phân khúc | Điều kiện |
   |---|---|
   | `champion` | R 4–5 và F 4–5 |
   | `loyal` | R 3–5 và F 3–5, trừ ô `champion` |
   | `promising` | R 4–5 và F 1–2 |
   | `needs_attention` | R 3 và F 1–2 |
   | `at_risk` | R 1–2 và F 3–5 |
   | `hibernating` | R 1–2 và F 1–2 |
   | `no_purchase` | chưa mua lần nào |

3. **`dim_user` theo SYSTEM_DESIGN 5.4**: `valid_to` NOT NULL, bản hiện hành là 9999-12-31; có `version_no`; `user_sk = user_id * 10 + version_no` do Spark gán trong lượt tính phiên bản, không do Postgres sinh. `warehouse/ddl.sql` (nhánh `w39-warehouse-star`, commit `ec2abb9`) đã khớp cột với `data/warehouse/dim_user/`.
4. **Số mẫu theo repo**, không theo Drive: bronze 4,767,012 dòng / 258,390 user; silver 4,754,015 dòng / 258,330 user. Số 4,694,166 trên Drive là của mẫu cũ dùng hàm băm khác.
5. **Phát hiện cần nhóm quyết**: tới 30/11 có 31,005 người mua, trong đó 19,071 người (61.5%) chỉ mua đúng 1 lần. `ntile(5)` cho F (đúng như tracker) chia những người này vào F1–F3 theo thứ tự `user_id`, nên hai người giống hệt nhau có thể khác phân khúc. Phương án thay thế: F theo ngưỡng 1 / 2 / 3 / 4–5 / 6+ lần (mỗi bậc có 1,604 đến 19,071 người, heatmap vẫn đủ 25 ô). Hiện đang làm theo tracker; đổi chỉ cần sửa một biểu thức.
6. **Chuỗi tồn kho**: 12,731 sản phẩm có mua × 5 kho × 30 ngày = 1,909,650 dòng. `gen_inventory.py` dùng Spark vì bronze là Parquet và bộ thư viện đã ghim không có trình đọc Parquet nào khác.
7. **BR4 đọc `stg_rfm_snapshot`, không đọc `dim_user WHERE is_current`**. Mỗi phiên bản `dim_user` giữ giá trị của mốc sinh ra nó: đã đo, 23,198 / 31,005 dòng hiện hành có `recency_days` khác giá trị thật ở 30/11, và `is_current` không lọc được theo mốc. `stg_rfm_snapshot` có đủ 5 mốc với giá trị đúng tại từng mốc. `dim_user` vẫn là chiều của `fact_event` và dùng cho truy vấn "phân khúc tại thời điểm X" (`valid_from <= X <= valid_to`). Mục BR4 trong `docs/API_CONTRACT.md` và `serving/api/routers/br4.py` (ghi `is_current`, router ghi Postgres còn contract ghi Parquet) cần cập nhật theo.
8. **Thứ tự chạy**: `python processing/dim_user.py` chạy sau `batch_silver.py` và trước `batch_warehouse.py`. Khi có khung Spark chung cho tầng kho, khung chỉ cần import `build_rfm_snapshot`, `build_dim_user`, `with_user_sk`.
