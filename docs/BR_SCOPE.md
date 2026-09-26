# Bảng 8 BR của nhóm 15

File này chốt 8 BR nhóm mình làm: ai làm, tuần nào, lấy dữ liệu ở đâu, màn hình hiện gì và khi nào thì coi là xong. BR9 (tra cứu ad-hoc) đã bỏ để có thời gian làm tầng kho.

Mỗi người làm trọn 3 phần của BR mình: Spark, API và màn hình. Màn hình nào cũng phải có footer QueryMeta và tải dưới 2 giây, nên cột "Xong khi" không ghi lại ý này.

## Bảng BR

| BR | Ai làm | Tuần | Ai cần | Câu hỏi | Lấy dữ liệu từ | Bảng kết quả | Màn hình | Xong khi |
|---|---|---|---|---|---|---|---|---|
| BR1 | Đắt | W40 | Ban điều hành | Doanh thu từng phút ra sao, ngành nào đang bán tốt? | Streaming (replayer đọc bronze) | Cassandra `gmv_by_minute` | 4 thẻ số và biểu đồ GMV 60 phút gần nhất, tự làm mới mỗi 10 giây | Chạy replayer thì biểu đồ tự cập nhật, đổi ngành thì biểu đồ đổi theo |
| BR2 | Đắt | W41 | Marketing | Khách bỏ đi ở bước nào: xem, thêm giỏ hay mua? | `fact_session_funnel` | Parquet `funnel_daily` | Phễu 3 bước và bảng tỉ lệ chuyển đổi theo ngành | Phễu giảm dần qua 3 bước, đổi ngày hoặc ngành thì số đổi |
| BR3 | Khang | W41 | Nhập hàng | Sản phẩm nào đang hot trong 15 phút qua? | Streaming, cửa sổ 15 phút trượt mỗi phút | Cassandra `trending_products` | Top 20 sản phẩm, có mũi tên lên xuống hạng | Chạy replayer thì bảng đổi mỗi phút, luôn đúng 20 dòng, không trùng hạng |
| BR4 | Khang | W40 | Marketing | Nhóm khách nào nên đầu tư quảng cáo? | `stg_rfm_snapshot` theo mốc được chọn | Parquet `rfm_segments` | Heatmap RFM 5x5, bấm một ô ra danh sách khách trong ô đó | Đủ 25 ô có số, bấm ô ra danh sách, đổi mốc thì số đổi |
| BR5 | Nguyên | W41 | Marketing | Ai bỏ quên giỏ hàng? | Streaming, phiên có thêm giỏ mà 30 phút sau vẫn chưa mua | Cassandra `abandoned_carts` | Danh sách giỏ xếp theo giá trị giảm dần, có nút "tạo chiến dịch" | Danh sách tăng dần trong ngày và không tự rỗng, lọc theo giá trị được |
| BR6 | Tín | W40 | Vận hành | Sản phẩm nào sắp hết hàng ở kho nào? | `fact_inventory_daily` và lượt mua | Cassandra `stockout_risk` | Bảng sản phẩm theo số ngày còn hàng, dưới 3 ngày thì tô đỏ | Chọn kho nào cũng ra bảng, có dòng đỏ, sản phẩm không bán được nằm cuối |
| BR7 | Nguyên | W40 | Nhập hàng | Mua sản phẩm A thì người ta hay mua kèm gì? | `fact_event` (các lượt mua trong cùng phiên) | Parquet `product_affinity` | Ô tìm sản phẩm, ra 10 sản phẩm hay mua kèm | Nhập `1005115` ra tối đa 10 dòng xếp theo lift, mã không có dữ liệu thì báo rỗng chứ không lỗi |
| BR8 | Tín | W41 | Vận hành | Tài khoản nào đặt đơn bất thường? | Streaming, đếm số đơn mỗi user trong 5 phút | Cassandra `order_velocity_alerts` | Danh sách cảnh báo theo mức độ, bấm vào xem các đơn | Chạy replayer thì cảnh báo mới hiện lên đầu, lọc theo mức độ được |

## Ghi chú

- RFM chụp mỗi tuần một lần, vào các ngày 7, 14, 21, 28 và 30/11.
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

- `dim_user` làm theo SYSTEM_DESIGN mục 5.4, `ddl.sql` của Tín đã khớp.
- Số liệu lấy theo repo (bronze 4,767,012 dòng). Số trên Drive là của mẫu cũ nên không dùng nữa.
- BR4 đọc `stg_rfm_snapshot` chứ không đọc bản hiện hành của `dim_user`. Bản hiện hành giữ số liệu từ lúc nó được tạo nên recency bị cũ, và cũng không lọc theo mốc được. Phần BR4 trong API contract cần sửa theo.
- `dim_user.py` chạy sau `batch_silver.py` và trước `batch_warehouse.py`.
- `gen_inventory.py` dùng Spark vì bronze lưu dạng Parquet.

## Cần nhóm quyết

- Khoảng 60% người mua chỉ mua đúng 1 lần, nên chia F bằng `ntile(5)` như tracker sẽ xếp những người này vào F1, F2, F3 dù họ giống nhau. Mình đang làm theo tracker. Nếu nhóm thấy nên đổi thì chia F theo số lần mua (1, 2, 3, 4-5, 6+), sửa nhanh thôi.
