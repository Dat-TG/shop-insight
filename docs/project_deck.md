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

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

---

## Trang 09 · Mô hình dữ liệu: mức khái niệm và mức logic · Đắt

Nguồn gợi ý: REPORT.md §4.4 (T15), SYSTEM_DESIGN §5.

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

---

## Trang 10 · Mô hình dữ liệu: mức vật lý · Đắt

Nguồn gợi ý: REPORT.md §4.4 (T15); evidence E1, E4, E5, explain_star_join.txt, gin_vs_seqscan.txt.

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

---

## Trang 11 · Spark: một engine cho nhánh theo lô và nhánh thời gian thực · Đắt

Nguồn gợi ý: REPORT.md §4.3; docs/evidence/batch_timings.txt (T02).

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

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

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

---

## Trang 17 · BR2 · Phễu chuyển đổi · Đắt

Nguồn gợi ý: docs/BR_SCOPE.md BR2; ảnh docs/evidence/gate2b_br2.png (T14); thao tác demo theo kịch bản T16.

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

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
