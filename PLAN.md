# Lịch và cổng chặn — Nhóm 15

Tài liệu nhóm trên Drive: "README — Đọc file này trước", "ShopInsight — Tài liệu mô tả hệ thống",
"ShopInsight — Kế hoạch và Phân công", và "ShopInsight — Bảng theo dõi công việc" (hai phần:
Phần 1 W38-W42, Phần 2 W43-W46). Bảng theo dõi chỉ nằm trên Drive — cả bốn người điền trực tiếp
vào đó, repo không giữ bản sao. Mọi file nộp đặt tên theo **Nhóm 15**.

## Mốc cứng

| Mốc | Tuần ISO | Ngày |
|---|---|---|
| Nộp presentation (slide pdf + video) | W43 | 19-25/10/2026 |
| Thuyết trình trên lớp | W44 | 26/10-1/11/2026 |
| Nộp project (report + slide + video + sản phẩm) | W46 | 9-15/11/2026 |

## Ngân sách — SAU KHI THÊM TẦNG KHO DỮ LIỆU

25 giờ/người trên 9 tuần (W38–W46), tổng 100 giờ-nhóm.

**Dự trữ thật là 5.50h, không phải 9.25h.** Dòng "81.75h việc thật / 9.25h dự trữ /
9h cập nhật trạng thái" trong bản kế hoạch cũ là một câu văn xuôi chưa bao giờ được
đối chiếu với Bảng theo dõi công việc. Cộng lại theo cột "Loại" của chính Bảng theo
dõi: **Làm 85.50 + Async 9.00 + Dự trữ 5.50 = 100.00**. Hai tài liệu mô tả **cùng
một** lịch 100h — 36 ô giờ của bảng tuần khớp nhau từng ô — chỉ khác nhau ở chỗ bao
nhiêu giờ đã được gắn tên. 3.75h chênh lệch đã bị hấp thụ dần lúc viết Bảng theo dõi
ra thành từng dòng có định nghĩa XONG, và câu văn xuôi không được cập nhật theo.

Một dấu vết kiểm chứng được: kế hoạch cũ viết Kafka sẽ lấy từ "ô dự trữ 1h của Đắt ở
W45", nhưng ô dự trữ W45 của Đắt trong Bảng theo dõi chỉ có 0.75h.

**Bảng theo dõi đúng, câu ngân sách cũ sai.** Con số dùng từ nay là **5.50h**.

Tầng kho dữ liệu tốn **11.00h ròng** (12.50h gộp, trừ 1.50h logic gold của
BR2/BR4/BR7 nay dùng lại được từ các bảng fact):

| Hạng mục | Giờ |
|---|---|
| `batch_warehouse.py` khung chạy | 1.00 |
| dim_date + nạp lịch nghỉ CSV | 1.00 |
| dim_event_type + dim_warehouse | 0.50 |
| dim_product SCD2 theo giá + cột attributes lồng nhau | 2.00 |
| Sinh catalogue JSON tổng hợp | 1.00 |
| dim_user SCD2 theo phân khúc RFM | 1.50 |
| fact_event (transaction) + nối silver→star | 1.75 |
| fact_session_funnel (accumulating snapshot) | 1.50 |
| fact_inventory_daily (periodic snapshot) | 1.00 |
| Postgres DDL + nạp + GIN index trên JSONB + bằng chứng EXPLAIN | 1.25 |
| **Gộp** | **12.50** |
| trừ phần dùng lại (BR2/BR4/BR7, mỗi BR 0.50) | −1.50 |
| **Ròng** | **11.00** |

### Dự trữ về 0, và còn âm 5.50h

**5.50 − 11.00 = −5.50.** Dự trữ không thể âm, nên nói cho đúng:

> **Dự trữ tụt từ 5.50h xuống 0.00h, và nhóm vẫn thiếu 5.50h.** Việc thêm tầng
> kho không phải "lấy từ dự trữ" — nó tiêu sạch 100% dự trữ rồi cần **cắt thêm
> 5.50h việc đã có tên**. Sau đây dự án **không còn một giờ đệm nào**: mọi phát
> sinh đều phải trả bằng cắt scope hoặc dời hạn, không còn gì để rút.

Đây là con số phải nhớ. Bản sửa trước ghi −1.75h vì tin vào câu ngân sách cũ; con
số đó sai và đã bỏ.

5.50h phải lấy từ việc thật. Theo đúng thang cắt scope ở cuối tài liệu:

| Cắt gì | Giờ | Vì sao chấp nhận được |
|---|---|---|
| **Bỏ hẳn BR9** (W45 Tín) | 1.00 | Thang #2. BR9 là cái thứ 9/9, rubric chỉ đếm 8. Mất 0 điểm |
| Đánh bóng UI vòng 2 (W45 Tín) 1.25 → 0.50 | 0.75 | Thang #5. Giữ lại đúng phần đo lại 8 màn hình sau khi đổi sang star — đó là bằng chứng cho Gate 2b |
| Đánh bóng UI vòng 1 (W42 Tín) 0.75 → 0.50 | 0.25 | 0.50h đủ ship đúng bốn thứ rubric gọi tên: bộ lọc theo nhóm user, empty state, màu nhất quán, footer QueryMeta |
| Benchmark bỏ cấu hình "Parquet có/không partition" (W41 Tín) | 0.25 | Thang #3. Chứng minh partition pruning bằng một query plan lưu vào `docs/evidence/` thay vì 20 lần chạy. Chỗ trống được cấu hình "Postgres trên star" lấp vào |
| Vẽ biểu đồ so sánh (W42 Tín) 0.75 → 0.50 | 0.25 | Hệ quả của dòng trên: bớt một cấu hình để vẽ |
| Chuẩn bị khảo sát 5 người (W43 Tín) 0.50 → 0.25 | 0.25 | Evaluation of Technology 1/10 chấm việc tiêu chí có được **định nghĩa rõ** hay không, không chấm độ công phu của form |
| Video demo sản phẩm (W46 Nguyên) 2.00 → 1.50 | 0.50 | Quay một lần theo kịch bản trên máy demo của Đắt, một lượt dựng. Không có giờ quay lại |
| Slide project (W45 Nguyên) 1.50 → 1.25 | 0.25 | Dùng lại bộ slide presentation đã làm W40–W42; phần mới thật sự chỉ là một slide mô hình 3 mức |
| Kịch bản video demo (W45 Nguyên) 0.75 → 0.50 | 0.25 | Dùng lại cấu trúc kịch bản video presentation viết ở W40 |
| Ghi nhận nhận xét GV (W44 Nguyên) 0.50 → 0.25 | 0.25 | Ghi ngay trong buổi rồi post nhóm chat trong ngày |
| Slide mục 4 (W42 Nguyên) 0.75 → 0.50 | 0.25 | Cùng lý do với benchmark: lắp bằng chứng đã có sẵn thay vì tạo mới |
| Slide mục 1+2 (W40 Nguyên) 1.25 → 1.00 | 0.25 | Nội dung đã có sẵn trong report mục 1–2 của Khang; đây là công chép sang slide |
| Gom nguồn tham khảo (W39 Nguyên) — bỏ dòng | 0.25 | Gộp vào lúc viết slide: trích nguồn ngay khi dùng |
| Chụp ảnh 5 bảng Cassandra (W39 Nguyên) 0.50 → 0.25 | 0.25 | File `.cql` đã trả tiền ở W38; còn lại là một `docker exec` + một `DESCRIBE` + một ảnh |
| Đọc chéo PR (W39 Đắt) — bỏ dòng | 0.50 | **Trả tiền hai lần.** Dòng Async 0.25h đã ghi "kèm mở PR của một bạn và để lại ít nhất một nhận xét" |
| **TỔNG** | **5.50** | |

**Không lấy từ hai chỗ này:** 9.00h cập nhật trạng thái (chính là thứ thay cho toàn
bộ các buổi họp) và 1.75h/người họp bắt buộc (tập thuyết trình W43, thuyết trình
W44). **Không nâng ngân sách trên 25h/người** — nâng ngân sách là lúc kế hoạch bắt
đầu nói dối. Bỏ Kafka **không** giải phóng thêm giờ nào: Kafka vốn không có giờ đặt
trước.

**Cắt xong thì mất gì.** Không mất gì rubric đếm, trừ phần đánh bóng. Cụ thể: màn
hình thứ 9 biến mất (0 điểm); giờ làm UI giảm từ 2.00h xuống 1.00h — đây là chỗ duy
nhất thật sự có nguy cơ mất một phần điểm (UI Design 2/10); khẳng định về partition
pruning dựa trên một query plan thay vì 20 lần chạy; video demo quay một lần. Mọi
thứ mà cổng hoặc phần evaluation phụ thuộc vào đều **còn nguyên**, và hai chỗ còn
**phình ra**: bằng chứng EXPLAIN của Nguyên (thêm star-join plan + GIN) và phần
correctness của Khang (thêm kiểm toàn vẹn khoảng SCD2).

**Khang bị cắt 0.00h** — 1.25h dự trữ của bạn đã đủ trả cho 1.00h việc tầng kho.
0.25h còn lại được cam kết trước cho phương án chuyển `fact_event` sang Khang nếu
Đắt trượt ở checkpoint W39.

**Một contingency đang thiếu tiền.** Phương án de-risk "chuyển `fact_event` sang
Khang" đáng 0.75h, mà chỗ duy nhất có giờ là 0.25h dự trữ dư của Khang. Tức là mới
được một phần ba. **Chốt trước, không đợi tới W39:** nếu cờ đỏ bật, Đắt bỏ
`fact_session_funnel` (thang cắt #7, BR2 quay lại đọc silver) chứ không để
`fact_event` trượt — vì `fact_event` là thứ mà dimension của cả ba người kia cắm vào.

**Một lỗi có sẵn, không phải do lần sửa này.** Dòng "Mọi tuần nằm trong băng
2-4h/người" đã sai từ trước: bảng cũ có W44 Đắt 1.50 và Nguyên 1.75, hai ô dưới
sàn 2h. Bảng mới sửa cả hai bằng cách kéo 0.75h việc report từ W45/W46 về W44.

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
  + `docs/SPARK_GUIDE_VI.md` (hướng dẫn tiếng Việt, giải thích từng bước và từng file —
  thay cho clip, đã bỏ) ở W38. Ba người còn lại tự chạy rồi post kết quả `KATA OK`.
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
| Đắt | BR2 phễu chuyển đổi | BR1 GMV theo phút | Nền tảng: bronze, silver, schema, **driver tầng kho**, nền streaming + replayer, tài liệu hướng dẫn, đóng gói |
| Khang | BR4 RFM | BR3 top-N trending | Report 6 mục + **dim_user SCD2 + stg_rfm_snapshot** + correctness |
| Nguyên | BR7 mua cùng nhau | BR5 giỏ hàng bỏ quên | Slide indexing + schema Cassandra + video + ground-truth + **dim_product SCD2 + catalogue JSON** |
| Tín | BR6 nguy cơ hết hàng | BR8 bất thường đặt đơn | App + benchmark + **Postgres star + DDL + GIN + nạp star (bước 6)** + UI |

### Chia tầng kho: bốn người làm song song, không ai chờ ai

Tầng kho là việc dùng chung, nhưng vẫn cắt được thành bốn mảnh độc lập vì các
dimension không phụ thuộc lẫn nhau:

| Người | Mảnh W39 | Phụ thuộc |
|---|---|---|
| Đắt | `batch_warehouse.py` khung chạy + `fact_event` | không |
| Khang | `stg_rfm_snapshot` + `dim_user` SCD2 | chỉ cần silver |
| Nguyên | `gen_catalog.py` + `dim_product` SCD2 | chỉ cần silver |
| Tín | `warehouse/ddl.sql` + nạp Postgres + GIN + `dim_date`/`dim_event_type`/`dim_warehouse` | lịch nghỉ CSV (tự viết) |

`fact_session_funnel` và `fact_inventory_daily` nằm ở W40 vì chúng cần dimension
đã xong. Đắt đẩy khung `batch_warehouse.py` trong 2 ngày đầu W39 để ba người cắm
mảnh của mình vào.

### Nguyên tắc giữ cho bốn người chạy song song

**Ai cũng tự sinh được dữ liệu của mình.** `.gitignore` chặn `data/`, nên dữ liệu không
đi qua git. Thay vào đó mỗi người tự tải `2019-Nov.csv` về máy ở W38, rồi tự chạy
`load_bronze.py` và `batch_silver.py` ở **đầu W39**. Bốn máy ra đúng cùng một tập nhờ
công thức lấy mẫu tất định `pmod(hash(user_id),100) < 7`; mỗi người post số dòng bronze
vào nhóm để đối chiếu ngay ở W39 thay vì tới W44 mới vỡ.

**Lịch nghỉ đi qua git, KHÔNG nằm trong `data/`.** `seed/holidays_2019.csv` là file
duy nhất viết tay chứ không sinh ra được, nên nó phải đi qua git. Đặt trong `data/`
là bị `.gitignore` nuốt im lặng và bốn máy ra bốn `dim_date` khác nhau.

**Thứ dùng chung luôn đi trước một tuần.** Đắt viết `load_bronze`/`batch_silver` ở W38 để
ba người chạy ở W39; dựng nền streaming ở W40 để ba BR streaming nằm trọn ở W41; viết
script khởi động ở W43 để Tín đo ở W44. Nguyên dựng ground-truth DuckDB ở W43 để Khang
đối chiếu ở W44. Không ai phải chờ trong cùng một tuần.

**Chỗ buộc phải chờ thì thay bằng dữ liệu giả.** Hợp đồng API của Tín ở W38 đóng băng tên
cột 8 bảng gold và kèm fixture JSON, nên ai cũng dựng được màn hình từ ngày đầu.

**Máy demo.** Mỗi người sinh gold trên máy mình nên không máy nào có đủ 8 bảng. Từ W43 máy
của Đắt là máy demo: đo hiệu năng W44, quay video W46, đóng gói W46 đều chạy ở đó.

## Lịch tuần — BẢN SỬA

| Tuần | Ngày | Nội dung | Đắt | Khang | Nguyên | Tín |
|---|---|---|---|---|---|---|
| W38 | 14-20/9 | Khởi động + hạ tầng + ai cũng tự cài Spark (JDK 21, Python, PySpark 4.1.3, Docker) | 3.75 | 2.75 | 2.75 | 3.25 |
| W39 | 21-27/9 | Ai cũng tự sinh dữ liệu + **TẦNG KHO**: 5 dim (2 cái SCD2), 2 nguồn mới, DDL Postgres | 3.75 | 3.75 | 3.75 | 3.75 |
| W40 | 28/9-4/10 | Nền streaming + replayer + BR1, BR6 + **2 fact còn lại** + BR4, BR7 tràn sang + nạp star vào Postgres | 4.00 | 3.75 | 3.50 | 3.75 |
| W41 | 5-11/10 | Ba BR streaming (BR3, BR5, BR8) + **BR2 tràn sang** + benchmark | 2.75 | 3.00 | 3.00 | 3.00 |
| W42 | 12-18/10 | Đóng băng code, đo <2s (Gate 2b), hoàn thiện slide, quay video | 2.75 | 2.25 | 3.00 | 2.25 |
| W43 | 19-25/10 | **NỘP PRESENTATION** + ghép video (Gate 3) + tập thuyết trình + dựng máy demo | 2.00 | 2.00 | 2.50 | 2.25 |
| W44 | 26/10-1/11 | **THUYẾT TRÌNH** + 3 nhóm thí nghiệm đánh giá | 2.00 | 3.00 | 2.00 | 2.75 |
| W45 | 2-8/11 | Report 6 mục (thêm mục thiết kế 3 mức) + hoàn thiện UI — **BR9 đã cắt** | 2.00 | 2.50 | 2.25 | 2.00 |
| W46 | 9-15/11 | **NỘP PROJECT** | 2.00 | 2.00 | 2.25 | 2.00 |
| **Tổng** | | | **25.00** | **25.00** | **25.00** | **25.00** |

Tổng theo tuần: 12.50 · 15.00 · 15.00 · 11.75 · 10.25 · 8.75 · 9.75 · 8.75 · 8.25
= 100.00h. **Cả 36 ô đều nằm trong băng 2.00–4.00h** — ô cao nhất 4.00 (Đắt W40), ô
thấp nhất 2.00. Đã kiểm từng ô.

**Sửa ngày 28/9, không đổi tổng giờ của ai.** Rà Bảng theo dõi với repo thấy hai việc W40
chưa dòng nào trả giờ. (1) `ingestion/replayer.py` chưa có, mà nền streaming, BR1 và
Gate 1a cần nó ngay đầu W40 → Đắt viết trong dòng nền streaming (1.00 → 1.25h), trả bằng
dòng "đặt bộ nhớ Spark" W41 (0.25 → 0h), vì `conf/spark-defaults.conf` đã đặt
`spark.driver.memory` từ W38. (2) Bước 6 của `batch_warehouse.py` (nạp star vào
Postgres) và bảng phẳng từ silver cho benchmark → dòng mới của Tín ở W40, 0.50h, trả
bằng dòng dựng bộ đo W40 (1.00 → 0.50h; tuần này bộ đo chỉ cần chạy thử một cấu hình).

Nhưng compliant trên giấy không có nghĩa là an toàn: **Đắt chạy 3.75 / 3.75 / 4.00
suốt W38–W40** — ba tuần liền ở 94–100% trần — trong khi ôm cả hai chỗ bàn giao then
chốt (batch_silver + khung tầng kho cho W39, bản mẫu streaming cho W41). Tín cũng
3.75/3.75 ở W39–W40. **Phương án giảm tải đã thoả thuận trước:** nếu checkpoint thứ
Tư W39 thấy Đắt trượt, chuyển `fact_event` (0.75h) sang Khang ngay, không bàn lại.

## Bốn cổng cứng — CẢ BỐN ĐỀU CÓ RỦI RO

| Cổng | Hạn cũ | Hạn đề nghị | Điều kiện xanh | Nếu đỏ |
|---|---|---|---|---|
| Gate 1 | Cuối W40 | **Tách đôi** | W40: BR1 chạy Structured Streaming, ảnh log micro-batch + hàng trong `gmv_by_minute`. W41: thêm BR3 | Giữ BR1 làm bằng chứng có streaming, BR3 chuyển batch |
| Gate 2 | Cuối W41 | **Tách đôi** | W41 (2a): cả 8 BR demo được. W42 (2b): mỗi màn hình < 2s, đã đo bằng QueryMeta | Bỏ Kafka; không còn tuần đệm để lùi tiếp |
| Gate 3 | Cuối W42 | **Thứ Tư W43** | Video presentation đã ghép và edit xong | Cắt phần đánh bóng slide; hạn W43 là hạn cứng, không lùi nữa |
| Gate 4 | Cuối W44 | Cuối W44, nhận 2/3 | correctness + performance ở W44; effectiveness (survey 5 người) được phép rơi sang W45 | Report mục 6 viết bằng số sơ bộ |

### Ba cổng gánh chịu nhiều nhất: Gate 1, Gate 2, Gate 3

**Gate 1 đã sai từ trước, không phải do lần sửa này.** Cổng đòi BR3 vào cuối W40,
nhưng lịch (cả bản cũ lẫn bản mới) xếp BR3 ở W41 và chưa bao giờ đặt giờ cho BR3 ở
W40. Cổng luôn đòi một BR sớm hơn một tuần so với lúc nó tồn tại — chỉ sống được vì
W40 trước đây nhẹ. Giờ W40 lên 14.75h nên chỗ hở đó lộ ra. Sửa bằng cách tách cổng
theo đúng thứ đang thật sự được dựng, gần như miễn phí.

**Gate 2 là cổng căng nhất.** BR2 không còn xong ở W39; bảo vệ băng giờ của Đắt đẩy
nó khỏi W40 (nếu ép vào W40 Đắt lên 5.25h, vượt trần 31%) sang W41. Nên BR2 nằm
đúng tuần với BR3, BR5, BR8 — cả 8 BR xong đúng ngày cổng đóng, không còn biên nào.
Tệ hơn: lưới an toàn cũ của Gate 2 là "dùng tuần đệm W43", mà W43 giờ chỉ còn 8.75h
và dự trữ toàn dự án là 0.00h. Vì vậy phải tách 2a/2b và đo trước lúc đóng băng code.

**Gate 3 bị ghim vào mốc ngoài.** Nộp presentation ở W43 là hạn cứng. Gate 3 lùi
được tới thứ Tư W43 và **không lùi thêm được nữa**. Giữ được vì kịch bản video phát
từ W40 và BR1/BR4/BR6/BR7 xong hết cuối W40, nên quay được từ ngày đầu W42.

**Gate 4 rủi ro nhưng nhẹ nhất** — nó nằm sau buổi thuyết trình, có sẵn phương án
lùi viết trong kế hoạch, và có trọn W45 phía sau. Khối lượng đo có tăng: correctness
giờ phải kiểm cả tính toàn vẹn SCD Type 2 (khoảng valid_from/valid_to không chồng
nhau, đúng một dòng is_current mỗi khoá tự nhiên, trên cả dim_product lẫn dim_user).

Điều kiện mỗi cổng phải là một hiện vật xem được — ảnh chụp, file, bảng số — post
vào nhóm chat. Không ai phải họp để duyệt cổng, và cũng không ai được tuyên bố
"chạy được" mà không kèm hiện vật.

Trượt cổng nào thì **không còn tuần đệm để tiêu**. Phải cắt scope theo thang bên dưới.

## Cổng chặn Kafka

Kafka không nằm trên đường găng vì rubric không cho điểm cho việc "có Kafka", nên
lịch **không đặt trước giờ nào cho nó**. Trước đây nếu cuối W41 xong hết thì lấy từ
ô dự trữ 1h của Đắt ở W45 — **ô đó không còn nữa**. Kafka giờ chỉ làm được nếu một
cổng về xanh sớm và giải phóng giờ. Gate 2 đỏ thì bỏ, không mất gì.

Việc làm cho lần swap này rẻ: tách hàm đọc nguồn ra `processing/source.py` từ W40.

## Phương án cắt scope nếu trượt cổng

1. Bỏ Kafka — vốn không có giờ đặt trước nên bỏ là miễn phí
2. ~~Bỏ BR9~~ — **đã cắt rồi**, dùng để trả cho tầng kho. Không cắt lại được nữa
3. Giảm benchmark từ 4 cấu hình xuống 3: bỏ "Parquet có/không partition", chứng minh
   partition pruning bằng một query plan trong `docs/evidence/` thay vì 20 lần chạy
4. Giảm dataset xuống 3 triệu dòng, vẫn giữ quy tắc lấy mẫu theo user trên trọn tháng
5. Giảm số màn hình được đánh bóng, giữ đủ 8 màn hình chạy được. Không đổi React
   sang framework khác giữa chừng — đổi công nghệ ở tuần trượt cổng là đổi rủi ro
   lấy rủi ro
6. Chỉ giữ 2/8 BR chạy streaming, còn lại batch hết
7. **Cuối cùng mới đụng tới tầng kho**: nếu buộc phải, giữ 5 dim + `fact_event`, bỏ
   `fact_session_funnel` và `fact_inventory_daily`, BR2/BR6 quay lại đọc silver. Mất
   phần "ba loại fact của Kimball" nhưng giữ được 8 BR

Ưu tiên tuyệt đối: **8 BR demo được > hiệu năng đẹp**.

## Ba thứ đừng tiêu thời gian vào

- Thêm công nghệ quản lý dữ liệu thứ ba — tiêu chí Technology Content chấm độ sâu
  (cần >3 ví dụ minh hoạ), không chấm số lượng công nghệ. Đã cân nhắc Neo4j cho BR7
  và **bác bỏ**; lý do ghi trong report, xem SYSTEM_DESIGN.md mục 5.7
- Dataset lớn hơn — 5 triệu dòng đã đủ cho mọi kết luận benchmark
- Tối ưu hiệu năng sau khi đã có số — mục tiêu phần evaluation là đo và giải
  thích chênh lệch, không phải làm đẹp con số

## Cách rubric quyết định ưu tiên

| Tiêu chí | Trọng số | Hệ quả lên code |
|---|---|---|
| Application Implementation | 8/10 | Công thức `4/n` mỗi BR demo thành công, n=4 nên mỗi BR ~1 điểm. Phải đủ 8 BR |
| Technology Content | 4/10 | Cần >3 ví dụ minh hoạ: code snippet, schema CQL, **DDL star + query plan star-join + GIN index**, screenshot. Lưu vào `docs/evidence/` |
| Evaluation of Technology | 1/10 | Cần >85% tiêu chí đánh giá định nghĩa rõ: metric / cách đo / công cụ / ngưỡng |
| User Interface Design | 2/10 | Bộ lọc theo từng nhóm user, empty state, màu nhất quán, footer QueryMeta |
| Report / Slide structure | 1/10, 2/10 | Bị trừ nếu >7 mục hoặc <4 mục. Chốt 6 mục report, 5 mục slide |

Các trọng số là cách nhóm đọc đề bài; xác nhận lại khi GV trả lời ba câu hỏi.

Tầng kho trả điểm ở Technology Content: mô hình dữ liệu ba mức (conceptual ERD /
logical star đối chiếu Cassandra / physical partitioning + index) là đúng thứ tiêu
chí này đòi, và nó cho benchmark một phép so sánh công bằng thật sự.

## Ba tiêu chí đánh giá phải đo (W44)

| Tiêu chí | Metric | Cách đo | Ngưỡng | Chủ trì |
|---|---|---|---|---|
| Data correctness | % khớp ground-truth + **toàn vẹn SCD2** | Chạy cùng logic bằng DuckDB, đối chiếu từng BR; kiểm khoảng SCD2 không chồng nhau và đúng 1 dòng is_current | >= 99% | Khang |
| Performance | Throughput events/s, latency p95, thời gian batch | Benchmark harness, mỗi truy vấn **>= 20 lần** | So sánh tương đối | Tín |
| Effectiveness | Thời gian phản hồi mỗi BR + mức hài lòng | Đo trên UI + mini survey 5 người dùng thử | < 2s mỗi màn hình | Tín |

Cần ít nhất 20 lần chạy mỗi truy vấn thì p95 mới có nghĩa. Bộ ground-truth DuckDB
do Nguyên dựng song song trong W44, tách khỏi phần chạy đối chiếu của Khang để hai
người không phải chờ nhau.

## Cấu hình benchmark

| Cấu hình | Kỹ thuật indexing minh hoạ | Dùng cho |
|---|---|---|
| Postgres bảng phẳng, có / không index | B-tree, BRIN, partial, composite | Slide mục 2 + alternative #1 |
| **Postgres trên star schema** | **Declarative partitioning, GIN trên JSONB, star-join plan** | **Slide mục 2 + đối chứng công bằng với DuckDB** |
| Cassandra đúng / sai partition key | LSM-tree, SSTable, Bloom filter | Slide mục 3 + giải pháp chính |
| Parquet có / không partition | Min-max stats, partition pruning | Slide mục 4 (cắt được nếu trượt cổng) |
| DuckDB trên Parquet star | Vectorized scan, zone map, struct projection | Alternative #2 + ground-truth |

Postgres nạp từ **silver** (bảng phẳng) và từ **star** (mô hình chiều), không phải
CSV thô — nếu không thì benchmark và phép đối chiếu correctness đang so hai tập dữ
liệu khác nhau. DuckDB trên Parquet star đối đầu Postgres trên cùng star chính là
phép so sánh "cùng mô hình logic, khác engine" mà trước đây thiếu.

## Ba câu hỏi cần gửi GV

Gửi ngay đầu W38, hạn nhận trả lời 20/9. Không trả lời thì chốt mặc định video
10 phút, không hỏi lại.

1. Thời lượng video mâu thuẫn trong đề: phần mô tả ghi presentation video "tối đa
   20 phút" và project video "20-30 phút", nhưng bảng rubric ở cả hai phần đều
   chấm theo mốc 10 phút. Tiêu chí này 1/10.
2. Domain eCommerce đã được gán duy nhất cho nhóm chưa? **Đây là câu duy nhất có
   hậu quả không đảo ngược được** — trùng domain thì phải đổi đề tài.
3. Cách hiểu công thức `4/n/10` cho phần Application Implementation.

## Những chỗ dễ sai về kỹ thuật

Danh sách này dài ra sau đợt rà soát. Mỗi dòng đều đã đo trên file thật hoặc kiểm
bằng tài liệu, không phải phỏng đoán.

- **`batch_silver.py` đổi giờ sang UTC+7 thì phải tính lại `event_date` từ giờ mới.** Giữ
  `event_date` cũ sẽ gán sai ngày cho sự kiện 17:00-24:00 UTC, làm lệch BR1, BR2, BR6.
  **Job streaming cũng phải đổi giờ y hệt** — quên là `gmv_by_minute.event_date` theo
  UTC còn `funnel_daily.event_date` theo UTC+7, hai màn hình cãi nhau về ngày.
- **`category_l1` không được null** vì nằm trong partition key của `gmv_by_minute`.
  Đã đo trên file thật: **32.4% số dòng có `category_code` rỗng** (21,898,171 / 67,501,979).
  Silver phải điền `'unknown'` cho `category_l1/l2/l3` đúng như đang làm với `brand`.
  Không điền thì một phần ba lệnh insert BR1 fail và GMV thiếu khoảng một phần ba.
- **`days_to_stockout` cũng không được null** — nó là clustering column của
  `stockout_risk`. `stock_on_hand / velocity_7d` trả NULL khi velocity bằng 0, mà đã đo:
  chỉ 12,659 / 127,693 sản phẩm (mẫu cũ — đo lại ở W39 trên mẫu Spark 129,899 sản phẩm)
  có phát sinh mua trong cả tháng, tức ~90% SKU velocity
  bằng 0 vĩnh viễn. Dùng `when(velocity_7d > 0, ...).otherwise(9999.0)`.
- **BR3 không xếp hạng được trên streaming DataFrame** — top-N phải tính trong `foreachBatch`.
- **BA bảng Cassandra để lại dòng rác, xử lý KHÁC NHAU:**
  - `stockout_risk` — batch ghi lại toàn bộ → xoá cả partition `WHERE warehouse_id = ?` rồi insert
  - `trending_products` — streaming, mỗi window phát lại nhiều lần → xoá
    `WHERE window_start = ?` rồi insert top-N mới. Bảng này trước đây bị bỏ sót
  - `abandoned_carts` — **đã đổi khoá**. Khoá cũ `((event_date), cart_value, user_session)`
    không xoá được một dòng vì Cassandra chỉ xoá theo tiền tố clustering, mà muốn xoá
    phải biết `cart_value` CŨ — đúng cái giá trị vừa đổi. Khoá mới
    `((event_date), user_session)` làm upsert tự idempotent, không cần xoá gì. Đổi lại
    mất tính "đã sắp sẵn theo cart_value trên đĩa", API tự sort vài nghìn dòng
- **`replayer.py` đọc `data/bronze/`, KHÔNG đọc `data/raw/2019-Nov.csv`.** File thô có
  3,696,117 user, bronze chỉ có 258,390 user trong rổ 7%. Đọc nhầm file thô thì phía
  streaming ăn tập dữ liệu lớn gấp 14 lần phía batch, và ngưỡng correctness >= 99%
  thành bất khả thi ngay từ đầu.
- **Job streaming KHÔNG ghi vào silver.** Silver chỉ có một writer là `batch_silver.py`.
  Ghi hai nơi thì hoặc Spark sinh `_spark_metadata/` làm chính Spark không thấy file
  của batch (DuckDB vẫn thấy → hai bên lệch nhau), hoặc nhân đôi dòng vì replayer phát
  lại đúng những sự kiện batch đã ghi. Chạy demo lần hai là BR2, BR4, BR7 sai số gấp đôi.
- **PySpark 3.5.x SEGFAULT trên Python 3.14** — cloudpickle 2.x bên trong nó gọi
  `pickle._getattribute` đã đổi ở 3.14, mà cloudpickle chính là thứ serialize mọi hàm
  Python gửi sang worker (UDF, lambda của RDD). Sửa ở W40: `foreachBatch` ở chế độ
  `local[*]` là callback py4j chạy trên driver, **không** qua cloudpickle. Pin
  `pyspark==4.1.3` + OpenJDK 21.
- **`spark.executor.memory` vô tác dụng trong `local[*]`** (driver chính là executor), và
  `.config("spark.driver.memory", ...)` trên `SparkSession.builder` chỉ có tác dụng khi
  chính builder đó khởi động JVM; JVM đã chạy sẵn (pyspark shell, notebook, session đã
  `stop()` trước đó) thì bị bỏ qua — sau `stop()` còn bỏ qua IM LẶNG, `getConf()` vẫn báo
  `6g` trong khi heap chỉ 1 GB (đã đo trên 4.1.3). Đặt trong `conf/spark-defaults.conf`.
- **SCD2: dùng `IS DISTINCT FROM`, không dùng `<>`.** `dim_product` an toàn vì `price`
  NOT NULL, nhưng `dim_user.rfm_cell` NULL với người chưa mua bao giờ (88% ở snapshot
  đầu), mà `NULL <> NULL` ra NULL chứ không ra true → sinh version mới mỗi snapshot cho
  mọi người chưa mua.
- **Đừng range-join fact với dimension SCD2.** `ON product_id = ... AND event_time BETWEEN
  valid_from AND valid_to` sinh 305,663,175 dòng trung gian, gấp 65 lần bảng fact, và
  riêng sản phẩm 1005115 chiếm 25%. Gán `product_sk` ngay trong window pass phát hiện
  đổi giá.
