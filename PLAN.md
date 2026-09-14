# Lịch và cổng chặn — Nhóm 15

Tài liệu nhóm trên Drive: "README — Đọc file này trước", "ShopInsight — Kế hoạch và Phân công"
và "ShopInsight — Bảng theo dõi công việc". Mọi file nộp đặt tên theo **Nhóm 15**.

## Mốc cứng

| Mốc | Tuần ISO | Ngày |
|---|---|---|
| Nộp presentation (slide pdf + video) | W43 | 19-25/10/2026 |
| Thuyết trình trên lớp | W44 | 26/10-1/11/2026 |
| Nộp project (report + slide + video + sản phẩm) | W46 | 9-15/11/2026 |

## Ngân sách

25 giờ/người trên 9 tuần (W38–W46), tổng 100 giờ-nhóm: 81.75h việc thật,
9.25h dự trữ, 9h cập nhật trạng thái. Mọi tuần nằm trong băng 2-4h/người.

W38 là tuần gộp: vừa khởi động (repo, group ID, câu hỏi cho GV, tải dataset) vừa
dựng hạ tầng (bronze, silver, Cassandra, scaffold app). Không có tuần khởi động
riêng — cả nhóm có trọn một tuần để bắt nhịp thay vì bị chia đôi.

## Cả nhóm đi làm và đi học — thiết kế để gần như không phải họp

Chỉ có **hai lần** cả bốn người phải có mặt cùng lúc trong suốt đồ án: tập thuyết
trình 45 phút ở W43, và buổi thuyết trình trên lớp ở W44. Tổng cộng 1.75h/người.

Bốn cơ chế thay cho họp:

- **Checkpoint tuần là bài post, không phải cuộc gọi.** Thứ Tư trước 22:00 mỗi
  người post ba dòng vào nhóm: xong gì / kẹt gì / tuần sau làm gì, kèm review một
  PR của bạn. 15 phút, làm lúc nào trong ngày cũng được.
- **Học Spark bằng tài liệu.** Đắt viết `docs/SETUP_SPARK.md` + `processing/kata.py`
  (in ra một số kỳ vọng) + clip 5 phút ở W38. Ba người còn lại tự chạy rồi post kết
  quả.
- **Truyền nghề streaming bằng code mẫu.** BR1 của Đắt là bản tham chiếu, comment
  kỹ, kèm `docs/STREAMING_PATTERN.md`. BR3, BR5, BR8 copy đúng khung đó.
- **Gỡ kẹt bằng cờ đỏ.** Kẹt quá 48 giờ thì gắn cờ đỏ trong nhóm ngay, không đợi
  tới checkpoint. Người review trả lời trong 24 giờ.

Ba quy ước làm cho async chạy được: mọi bàn giao đi qua repo chứ không qua lời nói;
mỗi BR có sẵn **định nghĩa thế nào là XONG** viết từ W38; PR nhỏ, merge trong tuần,
không ai giữ nhánh quá bảy ngày.

## Phân công: mỗi người sở hữu 2 BR trọn vẹn

Không chia theo tầng. Mỗi người nhận hai BR và làm trọn query Spark → endpoint →
màn hình. Mỗi người một BR batch và một BR streaming.

| Người | BR batch | BR streaming | Phụ trách chung |
|---|---|---|---|
| Đắt | BR2 phễu chuyển đổi | BR1 GMV theo phút | Nền tảng: bronze, silver, schema, nền streaming, tài liệu hướng dẫn, đóng gói |
| Khang | BR4 RFM | BR3 top-N trending | Report 6 mục + bảng tồn kho + correctness |
| Nguyên | BR7 mua cùng nhau (W39) | BR5 giỏ hàng bỏ quên (W41) | Slide indexing + schema Cassandra + video + ground-truth |
| Tín | BR6 nguy cơ hết hàng (W40) | BR8 bất thường đặt đơn (W41) | App + benchmark + replayer + Postgres + UI + BR9 |

### Nguyên tắc giữ cho bốn người chạy song song

**Ai cũng tự sinh được dữ liệu của mình.** `.gitignore` chặn `data/`, nên dữ liệu không
đi qua git. Thay vào đó mỗi người tự tải `2019-Oct.csv` về máy ở W38, rồi tự chạy
`load_bronze.py` và `batch_silver.py` ở **đầu W39**. Bốn máy ra đúng cùng một tập nhờ
công thức lấy mẫu tất định `pmod(hash(user_id),100) < 12`; mỗi người post số dòng bronze
vào nhóm để đối chiếu ngay ở W39 thay vì tới W44 mới vỡ.

**Thứ dùng chung luôn đi trước một tuần.** Đắt viết `load_bronze`/`batch_silver` ở W38 để
ba người chạy ở W39; dựng nền streaming ở W40 để ba BR streaming nằm trọn ở W41; viết
script khởi động ở W43 để Tín đo ở W44. Nguyên dựng ground-truth DuckDB ở W43 để Khang
đối chiếu ở W44. Không ai phải chờ trong cùng một tuần.

**Chỗ buộc phải chờ thì thay bằng dữ liệu giả.** Hợp đồng API của Tín ở W38 đóng băng tên
cột 8 bảng gold và kèm fixture JSON, nên ai cũng dựng được màn hình từ ngày đầu.

**Máy demo.** Mỗi người sinh gold trên máy mình nên không máy nào có đủ 8 bảng. Từ W43 máy
của Đắt là máy demo: đo hiệu năng W44, quay video W46, đóng gói W46 đều chạy ở đó.

Chỉ còn **hai chỗ phụ thuộc trong cùng tuần**, cả hai không tránh được: W38 Đắt đẩy
`kata.py` rồi ba người chạy (Đắt làm trong 2 ngày đầu), và W42 ba người quay video rồi
Nguyên ghép (kịch bản đã phát từ W40 nên quay được từ ngày đầu tuần).

## Lịch tuần

| Tuần | Ngày | Nội dung | Đắt | Khang | Nguyên | Tín |
|---|---|---|---|---|---|---|
| W38 | 14-20/9 | Khởi động + hạ tầng + ai cũng tự cài Spark | 3.75 | 2.75 | 2.75 | 3.25 |
| W39 | 21-27/9 | Ai cũng tự sinh dữ liệu + 3 BR batch (BR2, BR4, BR7) | 3.25 | 3.50 | 3.25 | 3.00 |
| W40 | 28/9-4/10 | Nền streaming + BR1, BR6 | 3.50 | 3.00 | 3.00 | 3.00 |
| W41 | 5-11/10 | Ba BR streaming còn lại (BR3, BR5, BR8) + benchmark | 2.50 | 3.00 | 3.00 | 3.00 |
| W42 | 12-18/10 | Đóng băng code, hoàn thiện slide, quay video | 3.50 | 2.75 | 3.75 | 3.00 |
| W43 | 19-25/10 | **NỘP PRESENTATION** + tập thuyết trình + dựng máy demo | 2.25 | 2.25 | 2.50 | 2.25 |
| W44 | 26/10-1/11 | **THUYẾT TRÌNH** + 3 nhóm thí nghiệm đánh giá | 1.50 | 3.00 | 1.75 | 2.75 |
| W45 | 2-8/11 | Report + hoàn thiện UI + BR9 | 2.50 | 2.75 | 2.50 | 2.50 |
| W46 | 9-15/11 | **NỘP PROJECT** | 2.25 | 2.00 | 2.50 | 2.25 |

Giờ đi theo rủi ro: nền 3h ở W38–W42 nơi có toàn bộ rủi ro kỹ thuật, rồi giảm dần
khi chỉ còn viết và đo. W43 nhẹ có chủ đích — đó là chỗ phục hồi nếu trượt cổng.

## Bốn cổng cứng — duyệt bằng hiện vật, không bằng cuộc họp

| Cổng | Hạn | Điều kiện xanh | Nếu đỏ |
|---|---|---|---|
| Gate 1 | Cuối W40 | BR1 + BR3 chạy trên Structured Streaming, có ảnh chụp log micro-batch và hàng trong Cassandra | Cắt BR3 sang batch, giữ BR1 làm bằng chứng có streaming |
| Gate 2 | Cuối W41 | Cả 8 BR demo được **và mỗi màn hình < 2s** — Đắt đo bằng footer QueryMeta và tuyên bố cổng | Bỏ Kafka, dùng tuần đệm W43 hoàn thành nốt BR |
| Gate 3 | Cuối W42 | Video presentation đã ghép và edit xong | Dùng trọn W43 quay lại, cắt phần đánh bóng slide |
| Gate 4 | Cuối W44 | Đủ ba bộ số liệu: correctness, performance, effectiveness | Report mục 6 viết bằng số sơ bộ, đo lại trong W45 |

Điều kiện mỗi cổng phải là một hiện vật xem được — ảnh chụp, file, bảng số — post
vào nhóm chat. Không ai phải họp để duyệt cổng, và cũng không ai được tuyên bố
"chạy được" mà không kèm hiện vật.

Gate 2 bắt đo dưới 2 giây ngay từ W41: để tới W44 mới phát hiện partition key sai
thì không còn tuần nào để sửa, vì sau W42 không ai còn dòng code nào trong lịch.

Trượt cổng nào thì tiêu vào tuần đệm W43, không dời sang sau khi thuyết trình.

## Cổng chặn Kafka

Kafka không nằm trên đường găng vì rubric không cho điểm cho việc "có Kafka", nên
lịch **không đặt trước giờ nào cho nó**. Nếu cuối W41 cả 8 BR đã xong thì lấy từ ô
dự trữ 1h của Đắt ở W45. Gate 2 đỏ thì bỏ, không mất gì.

Việc làm cho lần swap này rẻ: tách hàm đọc nguồn ra `processing/source.py` từ W40.

## Phương án cắt scope nếu trượt cổng

1. Bỏ Kafka — vốn không có giờ đặt trước nên bỏ là miễn phí
2. Bỏ BR9. **Không bỏ DuckDB** — DuckDB phục vụ trực tiếp bốn màn hình BR2, BR4,
   BR7, BR9, không phải chỉ để benchmark
3. Giảm dataset xuống 3 triệu dòng, vẫn giữ quy tắc lấy mẫu theo user trên trọn tháng
4. Giảm số màn hình được đánh bóng, giữ đủ 8 màn hình chạy được. Không đổi React
   sang framework khác giữa chừng — đổi công nghệ ở tuần trượt cổng là đổi rủi ro
   lấy rủi ro
5. Chỉ giữ 2/8 BR chạy streaming, còn lại batch hết

Ưu tiên tuyệt đối: **8 BR demo được > hiệu năng đẹp**.

## Ba thứ đừng tiêu thời gian vào

- Thêm công nghệ quản lý dữ liệu thứ ba — tiêu chí Technology Content chấm độ sâu
  (cần >3 ví dụ minh hoạ), không chấm số lượng công nghệ
- Dataset lớn hơn — 5 triệu dòng đã đủ cho mọi kết luận benchmark
- Tối ưu hiệu năng sau khi đã có số — mục tiêu phần evaluation là đo và giải
  thích chênh lệch, không phải làm đẹp con số

## Cách rubric quyết định ưu tiên

| Tiêu chí | Trọng số | Hệ quả lên code |
|---|---|---|
| Application Implementation | 8/10 | Công thức `4/n` mỗi BR demo thành công, n=4 nên mỗi BR ~1 điểm. Phải đủ 8 BR |
| Technology Content | 4/10 | Cần >3 ví dụ minh hoạ: code snippet, schema CQL, query plan, screenshot. Lưu vào `docs/evidence/` |
| Evaluation of Technology | 1/10 | Cần >85% tiêu chí đánh giá định nghĩa rõ: metric / cách đo / công cụ / ngưỡng |
| User Interface Design | 2/10 | Bộ lọc theo từng nhóm user, empty state, màu nhất quán, footer QueryMeta |
| Report / Slide structure | 1/10, 2/10 | Bị trừ nếu >7 mục hoặc <4 mục. Chốt 6 mục report, 5 mục slide |

Các trọng số là cách nhóm đọc đề bài; xác nhận lại khi GV trả lời ba câu hỏi.

## Ba tiêu chí đánh giá phải đo (W44)

| Tiêu chí | Metric | Cách đo | Ngưỡng | Chủ trì |
|---|---|---|---|---|
| Data correctness | % khớp ground-truth | Chạy cùng logic bằng DuckDB, đối chiếu từng BR | >= 99% | Khang |
| Performance | Throughput events/s, latency p95, thời gian batch | Benchmark harness, 4 cấu hình, mỗi truy vấn **>= 20 lần** | So sánh tương đối | Tín |
| Effectiveness | Thời gian phản hồi mỗi BR + mức hài lòng | Đo trên UI + mini survey 5 người dùng thử | < 2s mỗi màn hình | Tín |

Cần ít nhất 20 lần chạy mỗi truy vấn thì p95 mới có nghĩa. Bộ ground-truth DuckDB
do Nguyên dựng song song trong W44, tách khỏi phần chạy đối chiếu của Khang để hai
người không phải chờ nhau.

## Bốn cấu hình benchmark

| Cấu hình | Kỹ thuật indexing minh hoạ | Dùng cho |
|---|---|---|
| Postgres có / không index | B-tree, BRIN, partial, composite | Slide mục 2 + alternative #1 |
| Cassandra đúng / sai partition key | LSM-tree, SSTable, Bloom filter | Slide mục 3 + giải pháp chính |
| Parquet có / không partition | Min-max stats, partition pruning | Slide mục 4 |
| DuckDB trên Parquet | Vectorized scan, zone map | Alternative #2 + ground-truth |

Postgres nạp từ **silver**, không phải CSV thô — nếu không thì benchmark và phép
đối chiếu correctness đang so hai tập dữ liệu khác nhau.

## Ba câu hỏi cần gửi GV

Gửi ngay đầu W38, hạn nhận trả lời 20/9. Không trả lời thì chốt mặc định video
10 phút, không hỏi lại.

1. Thời lượng video mâu thuẫn trong đề: phần mô tả ghi presentation video "tối đa
   20 phút" và project video "20-30 phút", nhưng bảng rubric ở cả hai phần đều
   chấm theo mốc 10 phút. Tiêu chí này 1/10.
2. Domain eCommerce đã được gán duy nhất cho nhóm chưa? **Đây là câu duy nhất có
   hậu quả không đảo ngược được** — trùng domain thì phải đổi đề tài.
3. Cách hiểu công thức `4/n/10` cho phần Application Implementation.

## Bốn chỗ dễ sai về kỹ thuật

- **`batch_silver.py` đổi giờ sang UTC+7 thì phải tính lại `event_date` từ giờ mới.** Giữ
  `event_date` cũ sẽ gán sai ngày cho sự kiện 17:00-24:00 UTC, làm lệch BR1, BR2, BR6.
- **BR3 không xếp hạng được trên streaming DataFrame** — top-N phải tính trong `foreachBatch`.
- **`stockout_risk` và `abandoned_carts` xử lý KHÁC NHAU.** `stockout_risk` là batch ghi lại
  toàn bộ nên xoá cả partition rồi insert. `abandoned_carts` là streaming nên chỉ xoá đúng
  dòng cũ của `user_session` đó — xoá cả partition sẽ xoá sạch giỏ của micro-batch trước.
- **`category_l1` không được null** vì nằm trong partition key của `gmv_by_minute`.
