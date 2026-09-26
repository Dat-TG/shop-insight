# Bảng 8 BR của nhóm 15

File này chốt 8 BR nhóm mình làm: ai làm, lấy dữ liệu ở đâu, màn hình hiện gì và khi nào thì coi là xong. BR9 (tra cứu ad-hoc) đã bỏ để có thời gian làm tầng kho. Tuần làm từng BR xem ở `PLAN.md`.

Mỗi người làm trọn 3 phần của BR mình: Spark, API và màn hình. Màn hình nào cũng phải có footer QueryMeta và tải dưới 2 giây, nên cột "Xong khi" không ghi lại ý này.

## Bảng BR

| BR | Ai làm | Ai cần | Câu hỏi | Lấy dữ liệu từ | Bảng kết quả | Màn hình | Xong khi |
|---|---|---|---|---|---|---|---|
| BR1 | Đắt | Ban điều hành | Doanh thu từng phút ra sao, ngành nào đang bán tốt? | Streaming (replayer đọc bronze) | Cassandra `gmv_by_minute` | 4 thẻ số và biểu đồ GMV 60 phút gần nhất, tự làm mới mỗi 10 giây. Lọc theo ngày, ngành | Chạy replayer thì biểu đồ tự cập nhật mà không cần F5, đổi ngành thì biểu đồ đổi theo, có đường `unknown` |
| BR2 | Đắt | Marketing | Khách bỏ đi ở bước nào: xem, thêm giỏ hay mua? | `fact_session_funnel` | Parquet `funnel_daily` | Phễu 3 bước và bảng tỉ lệ chuyển đổi theo ngành. Lọc theo khoảng ngày, ngành | Phễu giảm dần qua 3 bước, đổi khoảng ngày hoặc ngành thì số đổi |
| BR3 | Khang | Nhập hàng | Sản phẩm nào đang hot trong 15 phút qua? | Streaming, cửa sổ 15 phút trượt mỗi phút | Cassandra `trending_products` | Top 20 sản phẩm, có mũi tên lên xuống hạng. Lọc theo cửa sổ | Chạy replayer thì bảng đổi mỗi phút, mũi tên đúng so với cửa sổ trước, luôn đúng 20 dòng và không trùng hạng |
| BR4 | Khang | Marketing | Nhóm khách nào nên đầu tư quảng cáo? | `stg_rfm_snapshot` theo mốc được chọn | Parquet `rfm_segments` | Heatmap RFM 5x5, bấm một ô ra danh sách khách trong ô đó. Lọc theo mốc, phân khúc | Đủ 25 ô có số, bấm ô ra đúng danh sách khách của ô đó, đổi mốc thì số đổi |
| BR5 | Nguyên | Marketing | Ai bỏ quên giỏ hàng? | Streaming, phiên có thêm giỏ mà 30 phút sau vẫn chưa mua | Cassandra `abandoned_carts` | Danh sách giỏ bỏ quên, có nút "tạo chiến dịch". Lọc theo ngày, giá trị tối thiểu | Danh sách xếp giá trị giỏ giảm dần, tăng dần trong ngày và không tự rỗng, lọc giá trị tối thiểu được, bấm "tạo chiến dịch" có thông báo |
| BR6 | Tín | Vận hành | Sản phẩm nào sắp hết hàng ở kho nào? | `fact_inventory_daily` và lượt mua | Cassandra `stockout_risk` | Bảng sản phẩm theo số ngày còn hàng, dưới 3 ngày thì tô đỏ. Lọc theo kho, ngưỡng ngày | Chọn kho nào cũng ra bảng xếp số ngày còn hàng tăng dần, có dòng đỏ, sản phẩm không bán được (9999) nằm cuối |
| BR7 | Nguyên | Nhập hàng | Mua sản phẩm A thì người ta hay mua kèm gì? | `fact_event` (các lượt mua trong cùng phiên) | Parquet `product_affinity` | Ô tìm sản phẩm, ra 10 sản phẩm hay mua kèm | Nhập `1005115` ra tối đa 10 dòng xếp lift giảm dần, mã không có dữ liệu thì báo rỗng chứ không lỗi |
| BR8 | Tín | Vận hành | Tài khoản nào đặt đơn bất thường? | Streaming, đếm số đơn mỗi user trong 5 phút | Cassandra `order_velocity_alerts` | Danh sách cảnh báo theo mức độ, bấm vào xem các đơn. Lọc theo ngày, mức độ | Chạy replayer thì cảnh báo mới hiện lên đầu, lọc `high` thì chỉ còn `high`, bấm một cảnh báo ra danh sách đơn |

## Ghi chú

- RFM chụp mỗi tuần một lần, vào các ngày 7, 14, 21, 28 và 30/11. Mỗi lần chụp tính các lượt mua tới hết ngày đó, nên phân khúc mới có hiệu lực từ ngày hôm sau.
- Phân khúc gán theo điểm R và F:

  | Phân khúc | R | F |
  |---|---|---|
  | champion | 4-5 | 4-5 |
  | loyal | 3-5 | 3-5 (trừ các ô champion) |
  | promising | 4-5 | 1-2 |
  | needs_attention | 3 | 1-2 |
  | at_risk | 1-2 | 3-5 |
  | hibernating | 1-2 | 1-2 |
  | no_purchase | chưa mua lần nào | |

- `dim_user` làm theo SYSTEM_DESIGN mục 5.4. `valid_to` không tính ngày cuối (bằng `valid_from` của bản sau), giống `dim_product`.
- Tuần đầu (1-7/11) chưa có lần chụp nào trước đó, nên sự kiện trong tuần này mang phân khúc của lần chụp 7/11.
- Số liệu lấy theo repo (bronze 4,767,012 dòng). Số trên Drive là của mẫu cũ nên không dùng nữa.
- BR4 đọc `stg_rfm_snapshot` chứ không đọc bản hiện hành của `dim_user`, vì bản hiện hành giữ số liệu từ lúc nó được tạo nên recency bị cũ, và cũng không lọc theo mốc được. `stg_rfm_snapshot` đã chia thư mục theo mốc.
- `dim_user.py` chạy sau `batch_silver.py` và trước `batch_warehouse.py`.
- `gen_inventory.py` dùng Spark vì bronze lưu dạng Parquet.

## Cần nhóm quyết

- `ntile(5)` chia đều theo thứ hạng nên những người giống nhau vẫn bị tách ra nhiều bậc. Khoảng 60% người mua chỉ mua 1 lần: họ nằm rải từ F1 tới F4, và ở mốc 30/11 có 468 người mua 1 lần vẫn thành champion. R cũng bị vậy, ví dụ 6,075 người cùng mua cách đây 13 ngày bị tách ra 2 bậc. Mình đang làm theo tracker. Nếu đổi thì chia theo giá trị (ví dụ F theo số lần mua 1, 2, 3, 4-5, 6+), sửa nhanh thôi.
- Bảng phân khúc ở trên khác các ví dụ trong fixture BR4 của Tín (fixture ghi ô 444 là loyal, 111 là at_risk). Nhóm chốt một bảng để API và màn hình khớp dữ liệu thật.
- BR4 đọc `stg_rfm_snapshot` là khác `CLAUDE.md` và SYSTEM_DESIGN (đang ghi BR4 lấy `dim_user` bản hiện hành). Nếu nhóm đồng ý thì cần sửa hai file đó và thêm `dim_user.py` vào thứ tự chạy trong README.
