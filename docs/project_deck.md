# Deck project ShopInsight: nội dung từng trang (Nhóm 15)

Deck là Claude Slides "Group15_ShopInsight_Project", 26 trang, chia theo 6 mục của report. Chỉ Đắt sửa deck,
thông qua Claude. Cả nhóm viết nội dung vào file này, rồi ở T25 Claude dựng slide từ đây. Hình kiến trúc ở trang 08
được vẽ lại từ F14: [figures/shopinsight_architecture.html](figures/shopinsight_architecture.html).

## Cách viết (T20, hạn T2 9/11)

- Mỗi người chỉ sửa các khối trang ghi tên mình. **Giữ nguyên dòng `## Trang NN · ...`** để 4 PR không xung đột,
  rồi tự merge PR của mình.
- **Tiêu đề:** một câu nêu ý chính của trang. Không dùng tên mục làm tiêu đề.
- **Ý chính:** tối đa 4 ý, mỗi ý một dòng ngắn. Không cần lo dàn trang.
- **Lời thoại:** viết đúng câu sẽ đọc khi quay. Phần slide của mỗi người dài khoảng 3 phút, tức khoảng 540 âm tiết
  ở tốc độ 3.0 âm tiết/giây. 3 phút còn lại là demo, theo kịch bản T16.
- **Số liệu:** ghi tên file evidence nguồn (`docs/evidence/perf_table.md`, `correctness_8br.txt`,
  `gate2b_screens.txt`...) thay vì tự chép số. Ở T25, số được lấy thẳng từ file đó.
- **Số âm tiết:** cuối mỗi khối, ghi số âm tiết của lời thoại trong khối.
- Thuật ngữ kỹ thuật giữ nguyên tiếng Anh: partition, row group, watermark, star schema...

## Phân công (theo T20, đổi thứ tự ngày 5/11)

Trang được xếp để mỗi người nói đúng 2 đoạn liền, cho bớt số lần cắt ghép khi quay (T29, T31):

| Thứ tự | Trang | Người | Nội dung |
|---|---|---|---|
| 1 | 01-04 | Khang | bìa, nội dung, bối cảnh, bốn nhóm người dùng |
| 2 | 05-07 | Nguyên | tám BR, hai trang nguồn dữ liệu |
| 3 | 08-11 | Đắt | kiến trúc, mô hình dữ liệu (2 trang), Spark |
| 4 | 12-15 | Tín | Cassandra, phương án thay thế, demo BR6, BR8 |
| 5 | 16-17 | Đắt | demo BR1, BR2 |
| 6 | 18-19 | Nguyên | demo BR5, BR7 |
| 7 | 20-22 | Khang | demo BR3, BR4, tính đúng đắn |
| 8 | 23-26 | Tín | hiệu năng, hữu dụng, kết luận, tài liệu tham khảo (trang 26 chỉ hiện) |

So với phân công T20 ban đầu, có hai trang đổi từ Nguyên sang Tín: Cassandra (trang 12) vì cả hai BR của Tín
(BR6, BR8) đều ghi Cassandra, và Kết luận (trang 25) vì nó nối ngay sau hai trang đánh giá của Tín. Mỗi người
vẫn nói khoảng 3 phút phần slide. Đắt quyết định ngày 5/11.

Trang 14-21 mở đầu đoạn demo của từng BR. Lời thoại ở đó ngắn: câu hỏi nghiệp vụ và vì sao màn hình trả lời
được câu hỏi đó. Thao tác demo nằm trong kịch bản T16.

---

## Trang 01 · Trang bìa · Khang

Nguồn gợi ý: điền họ tên đầy đủ và MSSV của bốn bạn (trên slide đang để trống).

**Tiêu đề:** ShopInsight: từ nhật ký hành vi mua sắm tới 8 màn hình trả lời dưới 2 giây

**Ý chính (tối đa 4):**
- Nhóm 15 · Data Engineering (CO5173) · HK1 2026–2027 · GV: PGS.TS. Võ Thị Ngọc Châu
- Bùi Quốc Khang 2670303 · Trịnh Trần Trung Tín 2313462
- Nguyễn Thị Quốc Nguyên 2670340 · Lê Công Đắt 2670260

**Lời thoại:**
Dạ, em chào cô và các bạn. Nhóm mười lăm xin trình bày đồ án ShopInsight: một hệ thống biến nhật ký hành vi mua
sắm thành tám màn hình phân tích, màn hình nào cũng trả lời dưới hai giây.

**Số âm tiết:** 43

---

## Trang 02 · Nội dung và người trình bày · Khang

Nguồn gợi ý: slide đã có bảng 6 mục, người trình bày và số trang (theo phân công ở trên).

**Tiêu đề:** Bài đi theo đường của dữ liệu: từ bài toán, qua kiến trúc, tới demo và đánh giá

**Ý chính (tối đa 4):**
- Mục 1–3: bối cảnh, tám yêu cầu nghiệp vụ, bốn nguồn dữ liệu
- Mục 4: kiến trúc, mô hình dữ liệu, Spark, Cassandra và phương án thay thế
- Mục 5: demo tám màn hình
- Mục 6: đánh giá theo ba tiêu chí (đúng đắn, hiệu năng, hữu dụng) và kết luận

**Lời thoại:**
Bài đi theo đường đi của dữ liệu. Ba mục đầu nói về bài toán: bối cảnh, tám yêu cầu nghiệp vụ và bốn nguồn dữ
liệu. Mục bốn là kiến trúc và công nghệ, mục năm là demo tám màn hình, và mục sáu đánh giá xem hệ thống có đúng, có
nhanh và có dùng được không.

**Số âm tiết:** 60

---

## Trang 03 · Bối cảnh · Khang

Nguồn gợi ý: REPORT.md §1.1 Bối cảnh, §1.3 Vì sao không truy vấn thẳng nhật ký thô.

**Tiêu đề:** Nhật ký thô có đủ dữ liệu, nhưng hỏi thẳng vào nó thì quá chậm

**Ý chính (tối đa 4):**
- Nhật ký REES46 tháng 11/2019: 67,501,979 sự kiện, 9.0 GB CSV; mỗi sự kiện là một lần xem, thêm giỏ hoặc mua
- Hỏi thẳng tệp CSV: đọc một lượt mất 25 giây, doanh thu theo ngành hàng mất 50 giây, trong khi ngưỡng là 2 giây
- Dữ liệu thô chưa sạch: 32.4% sự kiện không có ngành hàng, giờ ghi theo UTC nên lệch ngày so với giờ Việt Nam
- ShopInsight làm trước một lần những việc tốn kém, để màn hình chỉ đọc phần nhỏ nó cần

Số liệu: REPORT.md, bảng "Nguồn số liệu của mục 1" (mỗi số kèm lệnh đo trên `data/raw/2019-Nov.csv`).

**Lời thoại:**
Đồ án dùng nhật ký hành vi của một sàn thương mại điện tử trong tháng mười một năm hai nghìn mười chín: sáu mươi
bảy triệu rưỡi sự kiện, nặng chín gigabyte. Dữ liệu thì đủ, nhưng hỏi thẳng vào nó thì quá chậm: tính doanh thu theo
ngành hàng mất năm mươi giây. Dữ liệu thô cũng chưa sạch: gần một phần ba sự kiện thiếu ngành hàng, và giờ ghi theo
UTC nên lệch ngày so với giờ Việt Nam. Vì vậy ShopInsight làm trước một lần những việc tốn kém, để mỗi màn hình chỉ
đọc đúng phần nhỏ nó cần.

**Số âm tiết:** 111

---

## Trang 04 · Bốn nhóm người dùng · Khang

Nguồn gợi ý: REPORT.md §1.2 Các bên liên quan.

**Tiêu đề:** Bốn nhóm người dùng, hai nhịp ra quyết định

**Ý chính (tối đa 4):**
- Ban điều hành: doanh thu từng phút (BR1)
- Tăng trưởng và marketing: phễu chuyển đổi, phân khúc khách, giỏ bỏ quên (BR2, BR4, BR5)
- Hàng hoá: sản phẩm đang tăng, sản phẩm mua kèm (BR3, BR7)
- Vận hành và rủi ro: nguy cơ hết hàng, đơn bất thường (BR6, BR8)

**Lời thoại:**
Người dùng là bốn nhóm trong công ty. Ban điều hành theo dõi doanh thu từng phút. Bên marketing hỏi khách rời
đi ở bước nào, nhóm khách nào nên đầu tư, và ai bỏ quên giỏ hàng. Bên hàng hoá để ý sản phẩm nào đang lên và hay được
mua kèm gì. Còn vận hành cần biết sản phẩm nào sắp hết hàng và tài khoản nào đặt đơn bất thường. Một nửa số câu hỏi
cần trả lời gần như ngay lúc sự kiện xảy ra, nửa còn lại tính theo lô trên toàn bộ lịch sử. Tám câu hỏi này chính là
tám yêu cầu nghiệp vụ, trình bày ngay sau đây.

**Số âm tiết:** 118

---

## Trang 05 · Tám yêu cầu nghiệp vụ · Nguyên

Nguồn gợi ý: REPORT.md §2, docs/BR_SCOPE.md.

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

---

## Trang 06 · Nhật ký sự kiện và đặc trưng Big Data · Nguyên

Nguồn gợi ý: REPORT.md §3.1 và đoạn đặc trưng Big Data cuối §3 (T04).

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

---

## Trang 07 · Ba nguồn bổ trợ: ngày lễ, catalogue, tồn kho · Nguyên

Nguồn gợi ý: REPORT.md §3.2, §3.3, §3.4.

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

---

## Trang 08 · Kiến trúc tổng thể · Đắt

Nguồn gợi ý: REPORT.md §4.1; hình docs/figures/shopinsight_architecture.html, đã có trên slide. Ô PostgreSQL
ghi số đo T12 ở T25.

**Tiêu đề:** Hai nhánh xử lý, hai nơi lưu: Parquet cho 3 màn hình báo cáo, Cassandra cho 5 màn hình tra theo khoá

**Ý chính (tối đa 4):**
- Nhánh theo lô: Spark lấy mẫu 7% khách, làm sạch, dựng kho dữ liệu, ghi Parquet chia thư mục theo ngày
- Nhánh thời gian thực: phát lại log thành tệp JSON, Spark Structured Streaming tính ngay khi sự kiện tới
- DuckDB đọc Parquet cho BR2, BR4, BR7; Cassandra phục vụ BR1, BR3, BR5, BR8 từ luồng và BR6 từ lô
- PostgreSQL: bản dựng thứ hai của cùng kho dữ liệu, chỉ để so sánh, không phục vụ màn hình

Số liệu: hình docs/figures/shopinsight_architecture.html; ô PostgreSQL lấy số từ
`benchmark/results/summary_20261110_010557.csv` (T25 ghi kèm giới hạn ở REPORT.md §4.4, "Bốn điều phải đọc kèm
bảng này"); hai bản kho dữ liệu có số dòng bằng nhau ở docs/evidence/pg_vs_parquet_counts.txt. Lời thoại: "bảy
phần trăm" là quy tắc lấy mẫu ở REPORT.md §3.1 và §4.1.

**Lời thoại:**
Đây là kiến trúc tổng thể, gồm hai nhánh. Nhánh theo lô: Spark lấy mẫu bảy phần trăm khách, làm sạch, dựng kho dữ
liệu, rồi lưu Parquet chia thư mục theo ngày, để DuckDB đọc cho ba màn hình báo cáo. Nhánh thời gian thực: nhật ký
được phát lại thành từng tệp JSON, Spark Structured Streaming tính ngay khi sự kiện tới rồi ghi vào Cassandra.
Cassandra phục vụ năm màn hình tra theo khoá, một trong số đó tính theo lô. PostgreSQL chỉ là bản thứ hai của kho
dữ liệu, để so sánh.

**Số âm tiết:** 110

---

## Trang 09 · Mô hình dữ liệu: mức khái niệm và mức logic · Đắt

Nguồn gợi ý: REPORT.md §4.4 (T15), SYSTEM_DESIGN §5.

**Tiêu đề:** Mười một thực thể nghiệp vụ thành một star schema: ba fact theo ba kiểu của Kimball, năm dimension dùng chung

**Ý chính (tối đa 4):**
- Mức khái niệm: 11 thực thể; chỗ khó là giá sản phẩm và phân khúc khách đổi theo thời gian
- Ba fact: `fact_event` (transaction), `fact_session_funnel` (accumulating snapshot), `fact_inventory_daily` (periodic snapshot)
- `dim_product`, `dim_user` là SCD Type 2: mỗi sự kiện trỏ tới phiên bản có hiệu lực vào ngày của nó
- Ngành hàng, thương hiệu gộp vào `dim_product`: star, không phải snowflake; Cassandra thì ngược lại, mỗi câu hỏi một bảng

Số liệu: REPORT.md §4.4 (Hình 4.4a, Hình 4.4b, bảng ba fact, bảng đặt cạnh Cassandra); số dòng của chín bảng ở
docs/evidence/batch_timings.txt mục 2 và pg_vs_parquet_counts.txt; SCD2 sạch ở docs/evidence/t14_checks.txt
("Run 1: scd2_integrity.py ..."). Lời thoại: "mười một thực thể" là Hình 4.4a.

**Lời thoại:**
Ở mức khái niệm có mười một thực thể. Chỗ khó là giá sản phẩm và phân khúc khách đổi theo thời gian. Ở mức logic là
một star schema: bảng fact ở giữa ghi việc đã xảy ra, các bảng dimension quanh nó mô tả ai, cái gì, khi nào. Ba fact
ứng với ba kiểu của Kimball: từng sự kiện, từng phiên qua phễu, và tồn kho mỗi ngày. Sản phẩm và khách hàng là SCD
Type 2, tức mỗi lần đổi giá hay đổi phân khúc thì thêm một phiên bản, nên sự kiện mang đúng giá của ngày đó.

**Số âm tiết:** 110

---

## Trang 10 · Mô hình dữ liệu: mức vật lý · Đắt

Nguồn gợi ý: REPORT.md §4.4 (T15); evidence E1, E4, E5, explain_star_join.txt, gin_vs_seqscan.txt.

**Tiêu đề:** Ở mức vật lý, bỏ qua cả thư mục ngày có tác dụng rõ, còn min/max của row group thì chưa

**Ý chính (tối đa 4):**
- Parquet (nơi lưu chính): mỗi fact chia partition theo ngày, lọc một ngày chỉ mở thư mục của ngày đó
- Row group chưa giúp: mỗi tệp chỉ một row group, `event_time` ghi kiểu INT96 nên không có min/max
- PostgreSQL (bản thứ hai): partition theo ngày hoặc theo kho; B-tree, BRIN trên `event_time`, GIN trên `attributes`
- Số đo đi kèm giới hạn: GIN lợi ít vì bộ lọc khớp nhiều dòng; tắt pruning vẫn rẻ vì index dò nhanh các partition còn lại

Số liệu: `benchmark/results/summary_20261110_010557.csv` và `plans_20261110_010557.txt` (lần đo 10/11, 3 lần khởi
động + 20 lần đo); bảng số đo và "Bốn điều phải đọc kèm bảng này" ở REPORT.md §4.4. Nếu T25 đặt số GIN, pruning
bật/tắt, B-tree hay `gmv_by_minute` thiếu khoá lên slide thì ghi kèm giới hạn đó (B-tree là index tạm tạo riêng cho
benchmark). Không dùng thời gian của explain_star_join.txt (PostgreSQL lúc đó chỉ nạp 3 ngày) hay tên tệp trong
duckdb_zonemap.txt (tệp không còn). Lời thoại: "khoảng bốn mili giây" và "gần chín mươi" là p50 của
`postgres,event_time_one_hour,brin` (4.125 ms) và `seq_scan` (88.218 ms) trong summary.

**Lời thoại:**
Ở mức vật lý, Parquet là nơi lưu chính. Mỗi fact chia partition theo ngày, tức mỗi ngày một thư mục, nên lọc một
ngày chỉ mở một thư mục. Row group, tức một khối dòng trong tệp, có ghi min max từng cột để bỏ qua khối không cần
đọc, nhưng ở đây chưa giúp được: mỗi tệp chỉ có một row group, và cột thời gian không có min max. Bản PostgreSQL có
thêm index. BRIN, loại index chỉ nhớ min max của từng nhóm trang, lấy một giờ sự kiện mất khoảng bốn mili giây, quét
cả bảng mất gần chín mươi.

**Số âm tiết:** 114

---

## Trang 11 · Spark: một engine cho nhánh theo lô và nhánh thời gian thực · Đắt

Nguồn gợi ý: REPORT.md §4.3; docs/evidence/batch_timings.txt (T02).

**Tiêu đề:** Một Spark cho cả hai nhánh: cùng API DataFrame, cùng một hàm làm sạch

**Ý chính (tối đa 4):**
- `local[*]`: một tiến trình trên một máy, dùng mọi nhân CPU; bảy job theo lô chạy nối tiếp từ CSV tới gold
- Structured Streaming: micro-batch mỗi 5 giây, watermark 10 phút, checkpoint để chạy tiếp đúng chỗ đã dừng
- Hai nhánh gọi chung `clean()` của `batch_silver.py`: bảy quy tắc làm sạch giống hệt nhau
- Ghi Cassandra trong `foreachBatch` bằng `cassandra-driver`, không dùng Spark Cassandra Connector

Số liệu: docs/evidence/batch_timings.txt mục 1 (thời gian từng job, ngày 3/11); docs/evidence/streaming_perf.txt
Run 1 (thời gian mỗi micro-batch: p50, p95, max). Lời thoại: "khoảng bảy phút" là tổng 426.5 giây của
batch_timings.txt; "chưa tới một giây" là p50 `triggerExecution` của bốn job ở Run 1 (587 tới 852 ms). Micro-batch
đầu tiên chậm hơn vì khởi động JVM (max 3,524 ms ở Run 1).

**Lời thoại:**
Cả hai nhánh chạy trên Spark ở chế độ local, một tiến trình dùng mọi nhân CPU. Bảy job theo lô chạy hết khoảng bảy
phút. Nhánh thời gian thực dùng Structured Streaming: cứ năm giây, Spark gom tệp mới thành một micro-batch, tức một
lô nhỏ. Watermark mười phút, tức mốc lùi mười phút sau sự kiện mới nhất, cho Spark biết cửa sổ nào đã đóng để xoá
trạng thái. Hai nhánh gọi chung một hàm làm sạch. Khi demo, một micro-batch thường xong chưa tới một giây.

**Số âm tiết:** 102

---

## Trang 12 · Cassandra: thiết kế khoá từ câu hỏi của màn hình · Tín

Nguồn gợi ý: REPORT.md §4.2, serving/cassandra_schema.cql.

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

---

## Trang 13 · Phương án thay thế và vì sao không chọn · Tín

Nguồn gợi ý: REPORT.md §4.5 (T22); số đo benchmark T12, T14 và E4.

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

---

## Trang 14 · BR6 · Nguy cơ hết hàng · Tín

Nguồn gợi ý: docs/BR_SCOPE.md BR6; ảnh docs/evidence/gate2b_br6.png (T14); thao tác demo theo kịch bản T16.

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

---

## Trang 15 · BR8 · Tài khoản đặt đơn bất thường · Tín

Nguồn gợi ý: docs/BR_SCOPE.md BR8; ảnh docs/evidence/gate2b_br8.png (T14); thao tác demo theo kịch bản T16.

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

---

## Trang 16 · BR1 · Doanh thu theo từng phút · Đắt

Nguồn gợi ý: docs/BR_SCOPE.md BR1; ảnh docs/evidence/gate2b_br1.png (T14); thao tác demo theo kịch bản T16.

**Tiêu đề:** BR1: doanh thu từng phút theo ngày và ngành hàng, mỗi lần làm mới chỉ đọc một partition

**Ý chính (tối đa 4):**
- Ban điều hành hỏi: GMV từng phút ra sao, ngành hàng nào đang dẫn?
- Structured Streaming cộng GMV và số đơn theo cửa sổ 1 phút, cho từng ngành hàng và một dòng `all`
- Cassandra `gmv_by_minute`, partition key `(event_date, category_l1)`: phút mới nhất nằm đầu partition
- Màn hình tự làm mới mỗi 10 giây; footer ghi 1 partition

Số liệu: docs/evidence/gate2b_curl_raw.txt (dòng BR1); docs/evidence/t09_t10_live_checks.txt (BR1 3/3); footer
trên ảnh gate2b_br1.png. Lời thoại: "chưa tới mười mili giây" là curl max 6.5 ms của BR1 trong gate2b_curl_raw.txt.

**Lời thoại:**
Với ban điều hành, câu hỏi là: doanh thu từng phút ra sao, ngành hàng nào đang dẫn? Spark cộng doanh thu từng phút
ngay trên luồng. Trong Cassandra, ngày và ngành hàng là partition key, phút mới nhất nằm đầu, nên mỗi lần làm mới
màn hình chỉ đọc một partition, chưa tới mười mili giây.

**Số âm tiết:** 64

---

## Trang 17 · BR2 · Phễu chuyển đổi · Đắt

Nguồn gợi ý: docs/BR_SCOPE.md BR2; ảnh docs/evidence/gate2b_br2.png (T14); thao tác demo theo kịch bản T16.

**Tiêu đề:** BR2: phễu xem, thêm giỏ, mua cho marketing thấy khách rời đi ở bước nào

**Ý chính (tối đa 4):**
- Marketing hỏi: khách rời đi ở bước nào: xem, thêm giỏ hay mua?
- `fact_session_funnel`: mỗi phiên một dòng, ghi bước xa nhất; ngành hàng qua `fact_event` và `dim_product`
- `batch_gold.py` tổng hợp sẵn `funnel_daily` theo ngày và ngành hàng; Parquet chia thư mục theo ngày, DuckDB đọc
- Lọc khoảng ngày và ngành hàng; footer ghi số partition ngày đã đọc

Số liệu: docs/evidence/gate2b_curl_raw.txt (dòng BR2); docs/evidence/t09_t10_live_checks.txt (BR2 2/2, số phiên ở
ba bước); footer trên ảnh gate2b_br2.png. Lời thoại: "khoảng sáu phần trăm" là 54,676 / 966,143 phiên mua so với
phiên xem, cả tháng, trong t09_t10_live_checks.txt; "ba mươi partition" và "khoảng hai mươi mili giây" là dòng BR2
của gate2b_curl_raw.txt (30 partition, curl p50 19.8 ms).

**Lời thoại:**
Với marketing, câu hỏi là: khách rời đi ở bước nào, xem, thêm giỏ hay mua? Phễu được tổng hợp sẵn từ fact phiên,
theo từng ngày và từng ngành hàng. Cả tháng, số phiên mua chỉ bằng khoảng sáu phần trăm số phiên xem. Màn hình đọc
ba mươi partition ngày bằng DuckDB, mất khoảng hai mươi mili giây.

**Số âm tiết:** 67

---

## Trang 18 · BR5 · Giỏ hàng bị bỏ quên · Nguyên

Nguồn gợi ý: docs/BR_SCOPE.md BR5; ảnh docs/evidence/gate2b_br5.png (T14); thao tác demo theo kịch bản T16.

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

---

## Trang 19 · BR7 · Sản phẩm thường được mua kèm · Nguyên

Nguồn gợi ý: docs/BR_SCOPE.md BR7; ảnh docs/evidence/gate2b_br7.png (T14); thao tác demo theo kịch bản T16.

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

---

## Trang 20 · BR3 · Sản phẩm đang tăng mạnh · Khang

Nguồn gợi ý: docs/BR_SCOPE.md BR3; ảnh docs/evidence/gate2b_br3.png (T14); thao tác demo theo kịch bản T16.

**Tiêu đề:** BR3: top 20 sản phẩm đang lên, tính lại mỗi phút ngay trên luồng sự kiện

**Ý chính (tối đa 4):**
- Hàng hoá hỏi: sản phẩm nào đang tăng mạnh trong 15 phút gần nhất?
- Spark Structured Streaming: cửa sổ 15 phút trượt mỗi phút, đếm lượt xem và thêm giỏ theo sản phẩm, lấy top 20
- Cassandra `trending_products`, khoá `(window_start, rank)`: một cửa sổ là một partition, đã xếp sẵn theo hạng
- Màn hình đọc 1 partition, 20 dòng; mũi tên so hạng với cửa sổ một phút trước

Số liệu: docs/evidence/gate1b_br3_run.txt; footer trên ảnh gate2b_br3.png (T14).

**Lời thoại:**
Với bộ phận hàng hoá, câu hỏi là: sản phẩm nào đang tăng mạnh trong mười lăm phút gần nhất? Spark đếm lượt
xem và thêm giỏ trong cửa sổ mười lăm phút, trượt mỗi phút, rồi lấy top hai mươi. Mỗi cửa sổ là một partition trong
Cassandra, đã xếp sẵn theo hạng, nên màn hình chỉ đọc đúng hai mươi dòng.

**Số âm tiết:** 67

---

## Trang 21 · BR4 · Phân khúc khách hàng theo RFM · Khang

Nguồn gợi ý: docs/BR_SCOPE.md BR4; ảnh docs/evidence/gate2b_br4.png (T14); thao tác demo theo kịch bản T16.

**Tiêu đề:** BR4: heatmap RFM 5×5 cho marketing biết nhóm khách nào nên đầu tư

**Ý chính (tối đa 4):**
- Marketing hỏi: phân khúc khách hàng nào nên được đầu tư quảng cáo?
- RFM: mỗi khách đã mua được chấm 1–5 theo độ gần (recency), tần suất (frequency) và giá trị (monetary)
- Lấy từ `dim_user` bản hiện hành (SCD loại 2, chấm lại mỗi tuần), ghi Parquet `rfm_segments`, đọc bằng DuckDB
- Heatmap theo recency × frequency; chọn một ô để xem danh sách khách trong ô

Số liệu: footer trên ảnh gate2b_br4.png (T14).

**Lời thoại:**
Với marketing, câu hỏi là: nhóm khách nào nên được đầu tư quảng cáo? Mỗi khách đã mua được chấm từ một tới năm
theo độ gần, tần suất và số tiền chi. Màn hình vẽ hai tiêu chí đầu thành bảng năm nhân năm, đọc thẳng từ Parquet bằng
DuckDB. Chọn một ô là ra danh sách khách của ô đó.

**Số âm tiết:** 67

---

## Trang 22 · Đánh giá: tính đúng đắn · Khang

Nguồn gợi ý: docs/evidence/correctness_8br.txt (T19).

**Tiêu đề:** So với một đáp án viết độc lập, cả 8 BR khớp 100%, trên ngưỡng 99%

**Ý chính (tối đa 4):**
- Đáp án viết lại bằng SQL DuckDB trên silver, không dùng code Spark; so từng dòng với đúng bảng mà màn hình đọc
- 8/8 BR khớp 100%; bốn BR luồng đo trên lượt phát lại 17/11, 15:00–21:30
- SCD2 sạch ở cả `dim_product` và `dim_user`: 0 khoảng chồng, 0 khoảng hở, đúng 1 dòng hiện hành mỗi khoá
- Giới hạn: số thô RFM trong danh sách khách của BR4 có thể là của lần chấm trước; điểm và phân khúc vẫn đúng

Số liệu: docs/evidence/correctness_8br.txt (bảng 8 dòng, phép thử watermark sai, SCD2, giới hạn BR4).

**Lời thoại:**
Để biết hệ thống tính đúng, nhóm em viết lại đáp án cho cả tám câu hỏi bằng SQL thuần trên dữ liệu đã làm sạch,
không dùng lại code Spark, rồi so từng dòng với đúng bảng mà màn hình đọc. Cả tám BR khớp một trăm phần trăm, trên
ngưỡng chín mươi chín phần trăm. Hai bảng chiều có lịch sử cũng sạch: không khoảng nào chồng hay hở, và mỗi khoá có
đúng một dòng hiện hành.

**Số âm tiết:** 83

---

## Trang 23 · Đánh giá: hiệu năng · Tín

Nguồn gợi ý: docs/evidence/perf_table.md, gate2b_screens.txt (T17), batch_timings.txt (T02), streaming_perf.txt (T14).

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

---

## Trang 24 · Đánh giá: tính hữu dụng · Tín

Nguồn gợi ý: docs/evidence/survey_responses.csv (T18).

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

---

## Trang 25 · Kết luận, giới hạn và hướng phát triển · Tín

Nguồn gợi ý: REPORT.md §6.4 (T24).

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

---

## Trang 26 · Tài liệu tham khảo · Tín

Nguồn gợi ý: trang này chỉ hiện, không đọc. Danh sách lấy từ mục Tài liệu tham khảo của REPORT.md (T28), nên
khối này không cần lời thoại.

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:** (không có)

**Số âm tiết:** 0

---

## Lỗi trình bày (không phải trang slide)

Dùng cho T26 (Tín rà PDF nháp). Lỗi nội dung thì sửa thẳng trong khối trang ở trên; nếu là số sai thì ghi số đúng
kèm tên file evidence ngay tại khối đó. Ở đây chỉ ghi lỗi trình bày (màu, bố cục, hình), mỗi lỗi một dòng: số
trang · lỗi · cách sửa đề xuất.

-
