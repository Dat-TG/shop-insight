# Deck project ShopInsight: nội dung từng trang (Nhóm 15)

Deck là Claude Slides "Group15_ShopInsight_Project", 26 trang, chia theo 6 mục của report. Chỉ Đắt sửa deck,
thông qua Claude. Cả nhóm viết nội dung vào file này, rồi ở T25 Claude dựng slide từ đây. Hình kiến trúc ở trang 08
được vẽ lại từ F14: [figures/shopinsight_architecture.html](figures/shopinsight_architecture.html). Từ bản 22 (13/11
tối) hình đó được vẽ lại bằng khối và mũi tên của chính Slides, không còn là ảnh.

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

Ngày 13/11, vì sát hạn nộp, Claude soạn hộ các khối còn trống (lời thoại trang 05-07; trang 12-15, 18-19, 23-26)
từ REPORT.md, docs/evidence và code, theo yêu cầu của Đắt. Mỗi số trong các khối này có tệp và dòng nguồn ở dòng
"Số liệu", và đã được một lượt kiểm độc lập đối chiếu lại. Tín và Nguyên đọc lại khối của mình trước khi thu (T29);
muốn đổi chữ nào thì sửa thẳng ở đây. Cùng lượt đó trang 20 được sửa số partition (381, không phải 1) và trang 17,
22 được sửa vài chữ cho khớp evidence.

Bản 22 (13/11 tối, theo yêu cầu của Đắt): trang 05, 07, 08, 09, 10, 11 và 12 thay danh sách ý bằng sơ đồ (khối,
mũi tên, nhãn), mỗi sơ đồ được một lượt kiểm số liệu và một lượt kiểm hình độc lập; dòng "**Mặt slide:**" của các khối
đó ghi sơ đồ vẽ gì. Ý chính và lời thoại của các trang này không đổi. Tài liệu tham khảo (trang 26) tách thành mục
riêng. Dòng "Nguồn:" trên slide không dẫn REPORT.md nữa, vì báo cáo nộp là Google Doc của Khang và đánh số mục khác;
REPORT.md chỉ còn ở phần "Chi tiết" của dòng Số liệu, cho nhóm tra.

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

Số liệu: đo trên `data/raw/2019-Nov.csv` bằng `wc -l`, `ls -l`, `time` và `awk` (máy 12 nhân, 15 GB RAM, WSL2). Lệnh
đo của từng số ở REPORT.md, bảng "Nguồn số liệu của mục 1".

**Lời thoại:**
Đồ án dùng nhật ký hành vi của một sàn thương mại điện tử trong tháng mười một năm hai nghìn mười chín: sáu mươi
bảy triệu rưỡi sự kiện, nặng chín gigabyte. Dữ liệu thì đủ, nhưng hỏi thẳng vào nó thì quá chậm: tính doanh thu theo
ngành hàng mất năm mươi giây. Dữ liệu thô cũng chưa sạch: gần một phần ba sự kiện thiếu ngành hàng, và giờ ghi theo
UTC nên lệch ngày so với giờ Việt Nam. Vì vậy ShopInsight làm trước một lần những việc tốn kém, để mỗi màn hình chỉ
đọc đúng phần nhỏ nó cần.

**Số âm tiết:** 112

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

**Tiêu đề:** Tám câu hỏi nghiệp vụ chia làm hai nhịp: trả lời ngay khi sự kiện xảy ra, hoặc tính trên toàn bộ lịch sử

**Ý chính (tối đa 4):**
- Mỗi BR là một câu hỏi của một nhóm người dùng, có một màn hình riêng
- Bốn BR cần trả lời ngay (BR1, BR3, BR5, BR8): chạy theo luồng, ghi Cassandra
- Bốn BR cần toàn bộ lịch sử (BR2, BR4, BR6, BR7): chạy theo lô trên kho dữ liệu
- Mỗi thành viên giữ trọn hai BR, một theo lô và một theo luồng; hỏi thẳng nhật ký thô thì không câu nào xong dưới 2 giây

Số liệu: docs/BR_SCOPE.md (phạm vi, nguồn dữ liệu và người phụ trách của 8 BR). Chi tiết: REPORT.md §1.3, §2. Tiêu đề: hai nhịp (trả lời gần như ngay lúc sự kiện xảy ra, hoặc tính theo lô
trên toàn bộ lịch sử) là REPORT.md §1.2 dòng 28. Ý 1: REPORT.md §2 dòng 61 ("Mỗi yêu cầu trả lời một câu hỏi của một
nhóm người dùng ở mục 1.2 và có một màn hình riêng trên dashboard"). Ý 2 và 3: bảng BR ở REPORT.md §2 dòng 65-72 (cột
"Cách xử lý", "Nơi lưu kết quả") và dòng 74 (BR1, BR3, BR5, BR8 đọc luồng, ghi Cassandra; BR2, BR4, BR6, BR7 đọc kho
dữ liệu dạng mô hình chiều, riêng BR6 ghi Cassandra); cột "Nguồn" của docs/BR_SCOPE.md; trong code: `STREAMING_TABLES`
ở processing/streaming_gold.py dòng 112 (gmv_by_minute, trending_products, abandoned_carts, order_velocity_alerts),
processing/batch_gold.py dòng 4-6 (BR2, BR4, BR6) và processing/gold_br7.py dòng 13-14 (BR7 đọc data/warehouse). Ý 4:
REPORT.md §2 dòng 61 ("một yêu cầu xử lý theo lô và một yêu cầu xử lý thời gian thực") và cột "Phụ trách" của
docs/BR_SCOPE.md (Đắt BR1, BR2; Khang BR3, BR4; Nguyên BR5, BR7; Tín BR6, BR8); "không câu nào xong dưới 2 giây" là
REPORT.md §1.3 dòng 34: mọi câu hỏi phải quét cả tệp, đọc một lượt đã mất 25 giây (bảng "Nguồn số liệu của mục 1" dòng
52), doanh thu theo ngành hàng mất 50 giây (dòng 53). Lời thoại: "hai giây" là ngưỡng ở REPORT.md §1.1 dòng 15; "BR
một, ba, năm và tám" và "BR hai, bốn, sáu và bảy" là các mã ở REPORT.md §2 dòng 74; lời thoại không có số đo nào khác.

**Mặt slide:** sơ đồ hai cột: bốn BR thời gian thực (BR1, BR3, BR5, BR8) ghi Cassandra ở bên trái, bốn BR theo lô (BR2, BR4,
BR7 ghi Parquet cho DuckDB; BR6 ghi Cassandra) ở bên phải, cột giữa là người phụ trách mỗi hàng. Dòng cuối: "Hỏi thẳng
tệp CSV thô 9.0 GB thì không câu nào xong dưới 2 giây."

**Lời thoại:**
Mỗi yêu cầu nghiệp vụ, gọi tắt là BR, là câu hỏi của một nhóm người dùng và có một màn hình riêng. BR một, ba, năm và
tám cần trả lời ngay, nên chạy theo luồng, tức tính liên tục khi sự kiện tới, rồi ghi vào Cassandra, cơ sở dữ liệu tra
nhanh theo khoá. BR hai, bốn, sáu và bảy cần toàn bộ lịch sử, nên chạy theo lô trên kho dữ liệu. Mỗi thành viên giữ
trọn hai BR, một theo lô, một theo luồng. Hỏi thẳng nhật ký thô thì không câu nào xong dưới hai giây.

**Số âm tiết:** 108

---

## Trang 06 · Nhật ký sự kiện và đặc trưng Big Data · Nguyên

Nguồn gợi ý: REPORT.md §3.1 và đoạn đặc trưng Big Data cuối §3 (T04).

**Tiêu đề:** Nguồn chính là hơn sáu mươi bảy triệu sự kiện thật, lấy mẫu theo khách để lịch sử của mỗi khách còn nguyên

**Ý chính (tối đa 4):**
- REES46 tháng 11/2019, 9 cột; lấy mẫu 7% khách bằng giá trị băm của mã khách, giữ mọi sự kiện của khách đó
- Bảy quy tắc làm sạch, đổi sang giờ Việt Nam, ra tập làm việc 31 ngày
- Big Data: 9.0 GB; 4,767,012 sự kiện mẫu, 4,754,015 sau làm sạch; phát lại ×60 ~481 sự kiện/s; catalogue JSON lồng nhau
- Dữ liệu gốc có 38.4 giờ liền không có lượt mua; nhóm giữ nguyên và nói rõ

Số liệu: `data/raw/2019-Nov.csv`; docs/evidence/batch_timings.txt mục 2 (BRONZE OK, SILVER OK);
docs/evidence/correctness_8br.txt (lượt phát lại). Chi tiết: REPORT.md §3.1 và §3.5, bảng "Nguồn số liệu của mục 3". Tiêu đề: 67,501,979 sự kiện ở REPORT.md §3.1 dòng 146 và dòng
216 (`wc -l`); "thật" ở bảng nguồn dòng 139; lấy mẫu theo khách và giữ mọi sự kiện của khách ở đoạn "Lấy mẫu" dòng
160. Ý 1: REES46, tháng 11/2019 và 9 cột ở dòng 146-158 và dòng 216 (`head -1`), khớp 9 `StructField` ở
processing/schema.py dòng 44-52; quy tắc `pmod(hash(user_id), 100) < 7` ở dòng 160 và `SAMPLE_RULE` ở
ingestion/load_bronze.py dòng 71. Ý 2: bảy quy tắc ở dòng 169-176 và `clean()` ở processing/batch_silver.py dòng
131-177 (quy tắc 6 ở dòng 174-175); 31 ngày ở dòng 178 và dòng 222. Ý 3: 9.0 GB = 9,006,762,395 byte ở dòng 210 và
233; 4,767,012 là tập mẫu 7% ở tầng bronze, dòng 221 và 235; 4,754,015 ở dòng 222 và 237; "×60 ~481 sự kiện/s" là
`--speed 60`, 187,468 / (78 × 5 giây) = 480.7, ở dòng 210 và 239, nguồn docs/evidence/correctness_8br.txt dòng 15-16
(lượt phát lại 15:00–21:30 giờ Việt Nam ngày 17/11, ngày có nhiều lượt mua nhất; không phải tốc độ trung bình của cả
tháng hay tốc độ thật của sàn); catalogue JSON lồng nhau ở dòng 210 và 241. Ý 4: 38.4 giờ (14/11 18:09:37 tới 16/11
08:32:34 UTC) ở dòng 182 và 224. Đo lại bằng DuckDB ngày 13/11: bronze 4,767,012 dòng; silver 4,754,015 dòng, 31 ngày
`event_date`; data/stream_landing có 187,468 dòng trong 78 tệp, 08:00:00 tới 14:29:59 UTC; trên data/raw/2019-Nov.csv
khoảng trống dài nhất giữa hai lượt mua là 38.3825 giờ, đúng hai mốc trên. Lời thoại: "hơn sáu mươi bảy triệu" là
67,501,979; "chín cột" là 9 cột; "bảy phần trăm" là quy tắc `< 7` trên 100; "nên dữ liệu trải ra ba mươi mốt ngày" là
31 thư mục ngày của silver: sự kiện 17:00–24:00 UTC ngày 30/11 thuộc ngày 1/12 theo giờ Việt Nam (REPORT.md §3.1 dòng
178); "chín gigabyte" là 9.0 GB; "gần bốn triệu tám trăm nghìn dòng" là 4,767,012 của tập mẫu; "nhanh sáu mươi lần" là
`--speed 60`; "khoảng bốn trăm tám mươi mốt" là 480.7; "hơn ba mươi tám giờ" là 38.4 giờ.

**Lời thoại:**
Nguồn chính là hơn sáu mươi bảy triệu sự kiện thật, ghi trong chín cột. Nhóm lấy bảy phần trăm khách theo giá trị băm
của mã khách, giữ trọn lịch sử của họ. Bảy quy tắc làm sạch, có đổi sang giờ Việt Nam nên dữ liệu trải ra ba mươi mốt
ngày. Về Big Data: tệp gốc chín gigabyte, tập mẫu gần bốn triệu tám trăm nghìn dòng; phát lại nhanh sáu mươi lần,
khoảng bốn trăm tám mươi mốt sự kiện mỗi giây; catalogue sản phẩm là JSON lồng nhau. Tệp gốc có hơn ba mươi tám giờ
liền không một lượt mua; nhóm để nguyên.

**Số âm tiết:** 119

---

## Trang 07 · Ba nguồn bổ trợ: ngày lễ, catalogue, tồn kho · Nguyên

Nguồn gợi ý: REPORT.md §3.2, §3.3, §3.4.

**Tiêu đề:** Ba nguồn bổ trợ bù cho những gì nhật ký thô thiếu, và nhóm nói rõ nguồn nào là giả lập

**Ý chính (tối đa 4):**
- Lịch ngày lễ: 3 dòng viết tay, đưa vào git để mọi máy có cùng bảng thời gian
- Catalogue: thuộc tính sản phẩm sinh cố định từ mã sản phẩm, để so `jsonb` với `struct`
- Tồn kho: sinh theo lượt mua thật, để BR6 có dữ liệu mà tốc độ bán vẫn đúng nhu cầu
- Catalogue và tồn kho là giả lập, chỉ để minh hoạ kỹ thuật

Số liệu: seed/holidays_2019.csv; ingestion/gen_catalog.py; ingestion/gen_inventory.py. Chi tiết: REPORT.md §3.2, §3.3, §3.4. Tiêu đề: REPORT.md §3 dòng 135 (hai nguồn tự sinh là giả lập vì dữ liệu gốc không có thuộc
tính sản phẩm và tồn kho) và bảng nguồn dòng 139-142 (catalogue "Giả lập", tồn kho "Giả lập, bám theo lượt mua thật").
Ý 1: 3 dòng là dữ liệu của seed/holidays_2019.csv, cộng một dòng tiêu đề (Singles Day 11/11, Black Friday 29/11, Cyber
Monday 2/12), ở REPORT.md §3.2 dòng 186 và dòng 225; commit vào git ở §3.2 dòng 188 (`git ls-files seed/` ra
seed/holidays_2019.csv; nội dung của data/ bị loại khỏi git, xem .gitignore dòng 12 và 22;
serving/load_star_postgres.py dòng 39); "bảng thời gian" là `dim_date`, dựng từ tệp này bằng `load_holidays()` và
`build_dim_date_rows()` ở serving/load_star_postgres.py dòng 86 và 116-118, được gọi từ processing/batch_warehouse.py
dòng 195-205. Ý 2: §3.3 dòng 194 (hàm băm cố định từ mã sản phẩm; cột `jsonb` có chỉ mục GIN trong PostgreSQL, cột
`struct` trong Parquet); ingestion/gen_catalog.py: `_digest_ints()` ở dòng 29-30 lấy SHA-256 của `product_id`,
`build_attributes()` ở dòng 34 dựng thuộc tính từ đó. Ý 3: §3.4 dòng 198-206; ingestion/gen_inventory.py dựng tồn kho
từ lượt mua của silver: `purchases_by_warehouse()` dòng 30, `daily_sales()` dòng 36, `run_stock()` dòng 42, gọi ở dòng
109. Ý 4: catalogue "chỉ dùng để minh hoạ kỹ thuật lưu trữ" ở §3.3 dòng 194; cả hai nguồn tự sinh được gọi là "dữ liệu
minh hoạ" ở §3 dòng 135. Lời thoại: "ba dòng" là 3 dòng dữ liệu của seed/holidays_2019.csv; "BR sáu" là BR6; "bốn
nguồn" là bảng nguồn ở REPORT.md dòng 137-142.

**Mặt slide:** sơ đồ ba hàng, mỗi nguồn bổ trợ một hàng: nội dung, cách sinh, bảng star nhận nó, và dùng để làm gì
(lịch ngày lễ thật → `dim_date.is_holiday`; catalogue giả lập → `dim_product.attributes`; tồn kho giả lập từ lượt mua
thật của silver → `fact_inventory_daily`, 12,731 SKU đã bán × 5 kho × 30 ngày → BR6).

**Lời thoại:**
Ba nguồn bổ trợ bù cho những gì nhật ký thô thiếu. Lịch ngày lễ là ba dòng viết tay, đưa vào git cùng mã nguồn để mọi
máy có cùng bảng thời gian. Catalogue có thuộc tính sinh cố định từ mã sản phẩm, để so hai kiểu cột lồng nhau, jsonb
và struct. Tồn kho sinh theo lượt mua thật, để BR sáu có dữ liệu mà tốc độ bán vẫn đúng nhu cầu. Catalogue và tồn kho
là giả lập, chỉ minh hoạ kỹ thuật. Tiếp theo là kiến trúc xử lý bốn nguồn này.

**Số âm tiết:** 105

---

## Trang 08 · Kiến trúc tổng thể · Đắt

Nguồn gợi ý: REPORT.md §4.1; hình docs/figures/shopinsight_architecture.html, đã có trên slide. Ô PostgreSQL
ghi số đo T12 ở T25.

**Tiêu đề:** Hai nhánh xử lý, hai nơi phục vụ màn hình: Parquet cho 3 màn hình báo cáo, Cassandra cho 5 màn hình tra theo khoá

**Ý chính (tối đa 4):**
- Nhánh theo lô: Spark lấy mẫu 7% khách, làm sạch, dựng kho dữ liệu, ghi Parquet chia thư mục theo ngày
- Nhánh thời gian thực: phát lại nhật ký thành tệp JSON, Spark Structured Streaming tính ngay khi sự kiện tới
- DuckDB đọc Parquet cho BR2, BR4, BR7; Cassandra phục vụ BR1, BR3, BR5, BR8 từ luồng và BR6 từ lô
- PostgreSQL: bản dựng thứ hai của cùng kho dữ liệu, chỉ để so sánh, không phục vụ màn hình

Số liệu: hình docs/figures/shopinsight_architecture.html; ô PostgreSQL lấy số từ
`benchmark/results/summary_20261110_010557.csv` (T25 ghi kèm giới hạn ở REPORT.md §4.4, "Bốn điều phải đọc kèm bảng
này"); hai bản kho dữ liệu có số dòng bằng nhau ở docs/evidence/pg_vs_parquet_counts.txt. Lời thoại: "bảy phần trăm"
là quy tắc lấy mẫu ở REPORT.md §3.1 và §4.1.

**Mặt slide:** sơ đồ kiến trúc: hàng trên là nhánh thời gian thực (phát lại → Structured Streaming → Cassandra), hàng dưới
là nhánh theo lô (CSV → Spark theo lô → Parquet), FastAPI (có DuckDB) ở giữa, 5 màn hình tra theo khoá và 3 màn hình
báo cáo bên phải, PostgreSQL nét đứt "chỉ để so sánh".

**Lời thoại:**
Kiến trúc gồm hai nhánh. Nhánh theo lô: Spark lấy mẫu bảy phần trăm khách, làm sạch, dựng kho dữ liệu, rồi lưu
Parquet, định dạng lưu theo cột, chia thư mục theo ngày, để DuckDB đọc cho ba màn hình báo cáo. Nhánh thời gian
thực: nhật ký được phát lại thành từng tệp JSON, Spark Structured Streaming tính ngay khi sự kiện tới rồi ghi vào
Cassandra. Cassandra phục vụ năm màn hình tra theo khoá, một trong số đó tính theo lô. PostgreSQL chỉ là bản thứ hai
của kho dữ liệu, để so sánh.

**Số âm tiết:** 110

---

## Trang 09 · Mô hình dữ liệu: mức khái niệm và mức logic · Đắt

Nguồn gợi ý: REPORT.md §4.4 (T15), SYSTEM_DESIGN §5.

**Tiêu đề:** Mười một thực thể nghiệp vụ thành một star schema: ba fact theo ba kiểu của Kimball, năm dimension

**Ý chính (tối đa 4):**
- Mức khái niệm: 11 thực thể; chỗ khó là giá sản phẩm và phân khúc khách đổi theo thời gian
- Ba fact: `fact_event` (transaction), `fact_session_funnel` (accumulating snapshot), `fact_inventory_daily` (periodic snapshot)
- `dim_product`, `dim_user` là SCD Type 2: mỗi sự kiện trỏ tới phiên bản có hiệu lực vào ngày của nó
- Ngành hàng, thương hiệu gộp vào `dim_product`: star, không phải snowflake; Cassandra thì ngược lại, mỗi câu hỏi một bảng

Số liệu: số dòng ở docs/evidence/batch_timings.txt mục 2 và pg_vs_parquet_counts.txt; SCD2 sạch ở
docs/evidence/t14_checks.txt; khoá nối ở warehouse/ddl.sql. Chi tiết: REPORT.md §4.4 (Hình 4.4a, Hình 4.4b, bảng ba fact,
bảng đặt cạnh Cassandra); SCD2 ở t14_checks.txt ("Run 1: scd2_integrity.py ..."). Lời thoại: "mười một thực thể" là Hình 4.4a.

**Mặt slide:** star schema: ba fact (nền xanh đậm, kèm kiểu Kimball, grain và số dòng), năm dimension (số dòng, SCD Type 2),
khoá nối ghi trên cạnh, `user_session` nét đứt giữa `fact_event` và `fact_session_funnel`; ô ghi chú "Star, không
phải snowflake".

**Lời thoại:**
Ở mức khái niệm có mười một thực thể. Chỗ khó là giá sản phẩm và phân khúc khách đổi theo thời gian. Ở mức logic là
một star schema: bảng fact ở giữa ghi việc đã xảy ra, các bảng dimension quanh nó mô tả ai, cái gì, khi nào. Ba fact
ứng với ba kiểu của Kimball: từng sự kiện, từng phiên qua phễu, và tồn kho mỗi ngày. Sản phẩm và khách hàng là SCD
Type hai, tức giá hay điểm RFM đổi thì thêm một phiên bản theo ngày, nên mỗi sự kiện trỏ tới đúng phiên bản của ngày
đó.

**Số âm tiết:** 115

---

## Trang 10 · Mô hình dữ liệu: mức vật lý · Đắt

Nguồn gợi ý: REPORT.md §4.4 (T15); evidence E1, E4, E5, explain_star_join.txt, gin_vs_seqscan.txt.

**Tiêu đề:** Ở mức vật lý, bỏ qua cả thư mục ngày có tác dụng, còn min/max của row group thì chưa

**Ý chính (tối đa 4):**
- Parquet (nơi lưu chính): mỗi fact chia partition theo ngày, lọc một ngày chỉ mở thư mục của ngày đó
- Row group chưa giúp: mỗi tệp chỉ một row group, `event_time` ghi kiểu INT96 nên không có min/max
- PostgreSQL (bản thứ hai): partition theo ngày hoặc theo kho; B-tree ghép (`event_date`, …), BRIN trên `event_time`, GIN trên `attributes`
- Số đo đi kèm giới hạn: GIN lợi ít vì bộ lọc khớp nhiều dòng; tắt pruning vẫn rẻ vì index dò nhanh các partition còn lại

Số liệu: benchmark/results/summary_20261110_010557.csv và plans_20261110_010557.txt (10/11, 3 lần khởi động + 20 lần đo,
p50); docs/evidence/presentation_parquet_run.txt mục 6 (20/10); warehouse/ddl.sql. Chi tiết: bảng số đo và "Bốn điều
phải đọc kèm bảng này" ở REPORT.md §4.4; footer Parquet ở presentation_parquet_run.txt mục 6 (fact_event: 31 tệp, mỗi
tệp 1 row group, `event_time` INT96 có min/max ở 0/31 chunk); "Lọc một giờ" là 12:00-13:00 ngày 29/11, DuckDB đọc
31/31 tệp, p50 5.891 ms (summary dòng 14). Nếu T25 đặt số GIN, pruning
bật/tắt, B-tree hay `gmv_by_minute` thiếu khoá lên slide thì ghi kèm giới hạn đó (B-tree là index tạm tạo riêng cho
benchmark). Không dùng thời gian của explain_star_join.txt (PostgreSQL lúc đó chỉ nạp 3 ngày) hay tên tệp trong
duckdb_zonemap.txt (tệp không còn). Lời thoại: "khoảng bốn mili giây" và "gần chín mươi mili giây" là p50 của
`postgres,event_time_one_hour,brin` (4.125 ms) và `seq_scan` (88.218 ms) trong summary.

**Mặt slide:** Parquet bên trái (thư mục `event_date`, mỗi tệp 1 row group, `event_time` INT96 không có min/max), hai truy
vấn ở giữa ("Lọc một ngày" đọc 1/31 thư mục, 1.565 ms; "Lọc một giờ" đọc 31/31 tệp, 5.891 ms), PostgreSQL bên phải
(partition, index; BRIN 4.125 ms so với seq scan 88.218 ms).

**Lời thoại:**
Parquet là nơi lưu chính. Mỗi fact chia partition theo ngày, tức mỗi ngày một thư mục, nên lọc một ngày chỉ mở một
thư mục. Row group, tức một khối dòng trong tệp, có ghi min max từng cột để bỏ qua khối không cần đọc, nhưng ở đây
chưa giúp được: mỗi tệp chỉ có một row group, và cột thời gian không có min max. Bản PostgreSQL có thêm index. BRIN,
loại index chỉ nhớ min max của từng nhóm trang, lấy một giờ sự kiện mất khoảng bốn mili giây, quét cả bảng mất gần
chín mươi mili giây.

**Số âm tiết:** 114

---

## Trang 11 · Spark: một engine cho nhánh theo lô và nhánh thời gian thực · Đắt

Nguồn gợi ý: REPORT.md §4.3; docs/evidence/batch_timings.txt (T02).

**Tiêu đề:** Một Spark cho cả hai nhánh, cùng một hàm làm sạch

**Ý chính (tối đa 4):**
- `local[*]`: một tiến trình trên một máy, dùng mọi nhân CPU; bảy job theo lô chạy nối tiếp từ CSV tới gold
- Structured Streaming: micro-batch mỗi 5 giây, watermark 10 phút, checkpoint để chạy tiếp đúng chỗ đã dừng
- Hai nhánh gọi chung `clean()` của `batch_silver.py`: bảy quy tắc làm sạch giống hệt nhau
- Ghi Cassandra trong `foreachBatch` bằng `cassandra-driver`, không dùng Spark Cassandra Connector

Số liệu: docs/evidence/batch_timings.txt mục 1 (ngày 3/11); docs/evidence/streaming_perf.txt Run 1 và Run 2. Chi tiết:
batch_timings.txt mục 1 là thời gian từng job; streaming_perf.txt cho thời gian mỗi micro-batch (p50, p95, max). Lời thoại: "khoảng bảy phút" là tổng 426.5 giây của
batch_timings.txt; "chưa tới một giây" là p50 `triggerExecution` của bốn job: 587 tới 852 ms ở Run 1 (chưa chạy API
và giao diện), 562 tới 795 ms ở Run 2 (API, web và trình duyệt cùng chạy, đúng điều kiện demo). Micro-batch đầu tiên
chậm hơn vì khởi động JVM và truy vấn (max 3,524 ms ở Run 1).

**Mặt slide:** pipeline: hàng trên là nhánh thời gian thực (replayer → `streaming_gold.py` → `foreachBatch` → 4 bảng
Cassandra), hàng dưới là bảy job theo lô với số giây (tổng 426.5 s) và số dòng từng tầng, `clean()` ở giữa nối hai
nhánh.

**Lời thoại:**
Cả hai nhánh chạy trên Spark ở chế độ local, một tiến trình dùng mọi nhân CPU. Bảy job theo lô chạy hết khoảng bảy
phút. Nhánh thời gian thực dùng Structured Streaming: cứ năm giây, Spark gom tệp mới thành một micro-batch, tức một
lô nhỏ. Watermark mười phút, tức mốc trễ mười phút so với sự kiện mới nhất, cho Spark biết cửa sổ nào đã đóng để xoá
trạng thái. Hai nhánh gọi chung một hàm làm sạch. Khi demo, một micro-batch thường xong chưa tới một giây.

**Số âm tiết:** 104

---

## Trang 12 · Cassandra: thiết kế khoá từ câu hỏi của màn hình · Tín

Nguồn gợi ý: xem dòng Số liệu dưới đây.

**Tiêu đề:** Cassandra: khoá theo câu hỏi của màn hình

**Ý chính (tối đa 4):**
- Partition key chọn vùng đọc, clustering key xếp thứ tự trong vùng; 5 màn hình đọc 5 bảng Cassandra
- BR6 chia theo warehouse_id, xếp days_to_stockout rồi product_id; truy vấn theo sản phẩm thiếu partition key
- Hai câu hỏi khác nhau, benchmark p50: theo kho 1.113 ms/100 dòng, theo sản phẩm 81.089 ms/5 dòng, quét 63,655 dòng
- Dọn dòng cũ: BR6 xoá partition kho, BR3 xoá partition cửa sổ, BR5 upsert theo phiên, không xoá partition ngày

Số liệu: serving/cassandra_schema.cql; processing/batch_gold.py; processing/streaming_gold.py; benchmark/results/summary_20261110_010557.csv và plans_20261110_010557.txt. Benchmark trên máy Đắt ngày 10/11/2026, 3 warm-up + 20 lần đo. Hai biến thể stockout_risk là hai câu hỏi và số dòng kết quả khác nhau, không phải tăng tốc cùng một truy vấn. product_id thuộc clustering key, nhưng thiếu warehouse_id nên truy vấn cần ALLOW FILTERING.

**Mặt slide:** Bảng native 5 hàng: bảng phục vụ, partition key, clustering key. Phía dưới là hai cách truy cập BR6 và giới hạn so sánh, rồi dòng xử lý dữ liệu cũ.

**Lời thoại:**
Em nối tiếp phần thiết kế dữ liệu bằng Cassandra. Năm màn hình có năm bảng với khoá theo câu hỏi. Partition key chọn vùng dữ liệu, clustering key xếp sẵn các dòng trong vùng. BR6 chia theo kho và xếp số ngày còn hàng tăng dần. Hỏi theo sản phẩm mà thiếu kho phải quét bảng. Hai phép đo này trả kết quả khác nhau, chỉ minh hoạ cách truy cập. Khi khoá sắp xếp đổi, nhóm dọn dòng cũ riêng cho từng bảng để tránh trùng dữ liệu.

**Số âm tiết:** 90

---

## Trang 13 · Phương án thay thế và vì sao không chọn · Tín

Nguồn gợi ý: xem dòng Số liệu dưới đây.

**Tiêu đề:** Phương án thay thế: tốc độ và độ tươi

**Ý chính (tối đa 4):**
- Cùng câu hỏi BR1 (120 dòng), p50: Cassandra gold 2.2 ms, PostgreSQL star 2.0 ms, DuckDB trên Parquet star 12.1 ms
- Mẫu 7% khách, máy Khang ngày 8/11/2026; các thiết kế dữ liệu khác nhau, không suy ra ưu thế nội tại của engine
- Pipeline hiện tại chọn Cassandra cho độ tươi: ghi sau mỗi micro-batch 5 giây; bản star dựng theo lô
- BR2/BR4/BR7 đọc Parquet bằng DuckDB ngay trong API. Kafka, connector, Delta/Iceberg, Neo4j mới cân nhắc, chưa đo

Số liệu: docs/evidence/report_engine_compare.txt, Q1 (08/11/2026, máy Khang, f690021, 3 warm-up + 20 timed, p50 client execute + fetch); docs/REPORT.md §4.5; processing/streaming_gold.py. Không trộn Q1 với benchmark máy Đắt ngày 10/11. Cassandra đọc gold tính sẵn, PostgreSQL và DuckDB tính từ star. PostgreSQL cũng có thể nhận cập nhật liên tục nếu đổi thiết kế pipeline.

**Mặt slide:** Bảng native 3 cách trả lời BR1 với p50. Hai dòng giải thích độ tươi và lý do đọc Parquet.

**Lời thoại:**
Nhóm cũng đo PostgreSQL và DuckDB trên cùng star schema. Với câu hỏi doanh thu từng phút, PostgreSQL khoảng hai mili giây, Cassandra hai phẩy hai. Ở mẫu bảy phần trăm, cả hai đều nhanh. Nhóm chọn Cassandra cho nhánh luồng vì dữ liệu được ghi sau mỗi micro-batch, còn bản star được dựng theo lô. BR2, BR4 và BR7 dùng Parquet vì Spark ghi trực tiếp, DuckDB đọc ngay trong API. Các công nghệ còn lại mới được cân nhắc, chưa có số đo.

**Số âm tiết:** 85

---

## Trang 14 · BR6 · Nguy cơ hết hàng · Tín

Nguồn gợi ý: xem dòng Số liệu dưới đây.

**Tiêu đề:** BR6 · Nguy cơ hết hàng

**Ý chính (tối đa 4):**
- Vận hành hỏi: sản phẩm nào sắp hết hàng, ở kho nào?
- Số ngày còn hàng = tồn giả lập / tốc độ bán TB 7 ngày từ lượt mua thật; snapshot cuối 30/11/2019
- stockout_risk chia theo kho, xếp số ngày tăng dần. Mỗi kho trả 100 dòng gấp nhất và tối đa 5 dòng không bán
- Demo Kho 1, max_days=3 (≤3); tô đỏ khi <3. Thẻ số chỉ đếm phần trả về, không đại diện cả 63,655 cặp SKU-kho

Số liệu: docs/evidence/gate2b_br6.png (ảnh thật có sẵn, máy Đắt, 10/11/2026); docs/BR_SCOPE.md BR6; serving/api/routers/br6.py; web/src/pages/BR6Page.tsx; processing/batch_gold.py; processing/batch_warehouse.py. 9999 là sentinel không có lượt bán trong 7 ngày. Footer ảnh 28.77 ms là một lần tải, không phải p95. Phiên này thiếu dữ liệu và .venv, Docker chưa chạy, nên không có ảnh chụp lại ứng dụng.

**Mặt slide:** Ảnh BR6 thật từ repo, cắt phần đầu để đọc rõ bộ lọc, thẻ số và vài dòng. Bên phải là nhánh theo lô, công thức, thao tác và giới hạn thẻ số.

**Lời thoại:**
BR6 trả lời: sản phẩm nào sắp hết hàng, ở kho nào? Hệ thống lấy tồn kho giả lập chia cho tốc độ bán trung bình bảy ngày từ lượt mua thật. Kết quả của ngày cuối được ghi theo từng kho vào Cassandra, sản phẩm gấp nhất đứng trước. Các thẻ số chỉ đếm phần dữ liệu được trả về, nên không đại diện toàn bộ tồn kho.

**Số âm tiết:** 69

---

## Trang 15 · BR8 · Tài khoản đặt đơn bất thường · Tín

Nguồn gợi ý: xem dòng Số liệu dưới đây.

**Tiêu đề:** BR8 · Tài khoản đặt đơn bất thường

**Ý chính (tối đa 4):**
- Nhánh luồng tổng hợp sự kiện purchase theo user trong cửa sổ 5 phút cố định (tumbling)
- Mức cảnh báo: low 1 lượt mua, medium 2-3, high ≥4; tín hiệu hỗ trợ rà soát, chưa kết luận gian lận
- Mở dòng cho biết tổng cửa sổ: số lượt mua, tổng giá trị, giá trị trung bình; không phải danh sách từng đơn
- Demo ngày 17/11/2019, severity=high. Ảnh có sẵn ở all severity sau replay 15:00-21:30

Số liệu: docs/evidence/gate2b_br8.png (ảnh thật có sẵn, máy Đắt, 10/11/2026); docs/BR_SCOPE.md BR8; serving/cassandra_schema.cql; processing/streaming_gold.py; serving/api/routers/br8.py; web/src/pages/BR8Page.tsx; docs/evidence/t09_t10_live_checks.txt. PR #37 đổi ngưỡng, PR #41 chốt mở tổng cửa sổ. Chữ rolling trên ảnh là nhãn cũ; code là tumbling. order_count đếm sự kiện purchase, log không có order_id. LIMIT hiện tại 15,000 theo code, không dùng 5,000 của mô tả PR cũ.

**Mặt slide:** Ảnh BR8 thật từ repo, cắt phần đầu và vùng mở tổng cửa sổ. Bên phải ghi đúng cửa sổ cố định, ngưỡng, thao tác demo và phạm vi cảnh báo.

**Lời thoại:**
BR8 tìm tài khoản có nhiều lượt mua trong một cửa sổ năm phút cố định. Một lượt là low, hai tới ba là medium, từ bốn là high. Màn hình lọc theo ngày và mức độ. Khi mở một dòng, ta xem số lượt mua và tổng giá trị của cửa sổ đó. Đây là tín hiệu cần kiểm tra thêm, chưa phải kết luận gian lận.

**Số âm tiết:** 68

---

## Trang 16 · BR1 · Doanh thu theo từng phút · Đắt

Nguồn gợi ý: docs/BR_SCOPE.md BR1; ảnh docs/evidence/gate2b_br1.png (T14); thao tác demo theo kịch bản T16.

**Tiêu đề:** BR1: doanh thu từng phút theo ngày và ngành hàng, mỗi lần làm mới chỉ đọc một partition

**Ý chính (tối đa 4):**
- Ban điều hành hỏi: GMV từng phút ra sao, ngành hàng nào đang dẫn?
- Structured Streaming cộng GMV và số đơn theo cửa sổ 1 phút, cho từng ngành hàng và một dòng `all`
- Cassandra `gmv_by_minute`, partition key `(event_date, category_l1)`: phút mới nhất nằm đầu partition
- Màn hình tự làm mới mỗi 10 giây; footer ghi 1 partition

Số liệu: docs/evidence/gate2b_curl_raw.txt (dòng BR1); docs/evidence/t09_t10_live_checks.txt (BR1 3/3); footer trên
ảnh gate2b_br1.png. Lời thoại: "chưa tới mười mili giây" là curl max 6.5 ms của BR1 trong gate2b_curl_raw.txt: thời
gian gọi API, không phải thời gian vẽ màn hình (nếu T25 đặt số này lên slide thì ghi là API).

**Lời thoại:**
Với ban điều hành, câu hỏi là: GMV, tức tổng giá trị đơn hàng, từng phút ra sao, ngành hàng nào đang dẫn? Spark tính
nó ngay trên luồng. Trong Cassandra, ngày và ngành hàng là partition key, phút mới nhất nằm đầu, nên mỗi lần làm mới
màn hình chỉ đọc một partition, chưa tới mười mili giây.

**Số âm tiết:** 68

---

## Trang 17 · BR2 · Phễu chuyển đổi · Đắt

Nguồn gợi ý: docs/BR_SCOPE.md BR2; ảnh docs/evidence/gate2b_br2.png (T14); thao tác demo theo kịch bản T16.

**Tiêu đề:** BR2: phễu xem, thêm giỏ, mua cho marketing thấy khách rời đi ở bước nào

**Ý chính (tối đa 4):**
- Marketing hỏi: khách rời đi ở bước nào: xem, thêm giỏ hay mua?
- `fact_session_funnel`: mỗi phiên một dòng, ghi bước xa nhất; ngành hàng qua `fact_event` và `dim_product`
- `batch_gold.py` tổng hợp sẵn `funnel_daily` theo ngày và ngành hàng; Parquet chia thư mục theo ngày, DuckDB đọc
- Lọc khoảng ngày và ngành hàng; footer ghi số partition ngày đã đọc

Số liệu: docs/evidence/gate2b_curl_raw.txt (dòng BR2); docs/evidence/t09_t10_live_checks.txt (BR2 2/2, số phiên ở ba
bước); footer trên ảnh gate2b_br2.png. Lời thoại: "khoảng sáu phần trăm" là 54,676 / 966,143 phiên mua so với phiên
xem, cả tháng, trong t09_t10_live_checks.txt; "ba mươi partition" và "khoảng hai mươi mili giây" là dòng BR2 của
gate2b_curl_raw.txt (30 partition, curl p50 19.8 ms).

**Lời thoại:**
Với marketing, câu hỏi là: khách rời đi ở bước nào, xem, thêm giỏ hay mua? Phễu được tổng hợp sẵn từ fact session
funnel, theo ngày và ngành hàng. Cả tháng, số phiên mua chỉ bằng khoảng sáu phần trăm số phiên xem. Phễu cả tháng đọc ba
mươi partition ngày bằng DuckDB; khi đã nóng, mất khoảng hai mươi mili giây.

**Số âm tiết:** 70

---

## Trang 18 · BR5 · Giỏ hàng bị bỏ quên · Nguyên

Nguồn gợi ý: docs/BR_SCOPE.md BR5; ảnh docs/evidence/gate2b_br5.png (T14); thao tác demo theo kịch bản T16.

**Tiêu đề:** BR5: giỏ bỏ quên được tìm trên luồng sau 30 phút không mua, ghi upsert theo phiên nên danh sách không tự rỗng

**Ý chính (tối đa 4):**
- Marketing hỏi: khách nào bỏ quên giỏ hàng?
- `streaming_gold.py`: `session_window` 30 phút theo `user_session`; phiên có thêm giỏ mà không mua là giỏ bỏ quên
- Cassandra `abandoned_carts`, khoá `((event_date), user_session)`; `cart_value` là cột thường nên upsert không cần xoá
- Phát lại 17/11, 15:00–21:30: 2,600 giỏ, API tự xếp giá trị giảm dần, hiện 200 giỏ đầu; footer 1 partition, p50 9.6 ms

Số liệu: docs/evidence/gate2b_screens.txt (dòng BR5), gate2a_br5_run.txt, ảnh gate2b_br5.png; REPORT.md §2.5, §4.2, §5.2. Tiêu
đề và Ý chính: "30 phút" là `session_window("event_time", "30 minutes")` ở processing/streaming_gold.py dòng 394 (cũng
là BR_SCOPE.md dòng 13 và REPORT.md §2.5 dòng 102); "có thêm giỏ mà không mua" là điều kiện `has_cart == 1` và
`has_purchase == 0` ở streaming_gold.py dòng 404; khoá `((event_date), user_session)` ở serving/cassandra_schema.cql
dòng 35; upsert, không xoá: docstring `start_br5` ở streaming_gold.py dòng 342-347 và REPORT.md §4.2 dòng 344; "Phát
lại 17/11, 15:00–21:30" là trạng thái lúc đo ở gate2b_screens.txt dòng 7 (78 tệp, 187,468 sự kiện) và endpoint
`?event_date=2019-11-17` ở gate2b_curl_raw.txt dòng 27; "API tự xếp giá trị giảm dần" là serving/api/routers/br5.py
dòng 93 (API_CONTRACT.md dòng 434: sắp xếp ở API, không phải thứ tự của Cassandra); "200 giỏ đầu" là `MAX_ROWS = 200`
ở web/src/pages/BR5Page.tsx dòng 12, dòng "Showing the 200 highest of 2,600 carts" trên ảnh gate2b_br5.png và
REPORT.md §5.2 dòng 812; "2,600 giỏ" là cột rows của dòng BR5 ở gate2b_curl_raw.txt dòng 20, khớp footer ảnh
gate2b_br5.png (1 partition, 2,600 rows) và REPORT.md §5.2 dòng 791; "1 partition" và "p50 9.6 ms" là dòng BR5 của
gate2b_screens.txt dòng 44 (meta p50 9.6, meta p95 11.9, curl p50 23.3, curl p95 61.3). 9.6 ms là QueryMeta.ms, tức số
ms in ở footer: br5.py chốt thời gian ở dòng 76, trước khi xếp ở dòng 93, nên nó chỉ là lần đọc Cassandra; nếu T25 cần
thời gian cả vòng HTTP (gồm xếp và JSON) thì dùng curl p50 23.3 ms. Footer trên ảnh ghi 38.381 ms vì đó là một lần tải
trang, thường là lần đầu còn lạnh (gate2b_screens.txt dòng 35-37). Lời thoại: "ba mươi phút" là streaming_gold.py dòng
394; "phiên kết thúc sau ba mươi phút không có sự kiện" là chú thích ở dòng 390-393; "cùng phiên thì ghi đè cùng dòng"
là docstring dòng 342-344 và REPORT.md §4.2 dòng 344 ("cùng một phiên luôn ghi đè cùng một dòng"); "không cần xoá và
danh sách không tự rỗng" là docstring dòng 344-347, REPORT.md §4.2 dòng 344 và cột "Xong khi" của BR5 ở BR_SCOPE.md
dòng 13 ("tăng dần trong ngày và không tự rỗng"). Lời thoại không có số liệu nào khác.

**Lời thoại:**
Cũng với marketing, câu hỏi là: khách nào bỏ quên giỏ hàng? Spark dùng session window, tức phiên kết thúc sau ba mươi
phút không có sự kiện. Phiên có thêm giỏ mà không mua là giỏ bỏ quên. Giỏ được ghi vào Cassandra kiểu upsert, tức cùng
phiên thì ghi đè cùng dòng, nên không cần xoá và danh sách không tự rỗng.

**Số âm tiết:** 71

---

## Trang 19 · BR7 · Sản phẩm thường được mua kèm · Nguyên

Nguồn gợi ý: docs/BR_SCOPE.md BR7; ảnh docs/evidence/gate2b_br7.png (T14); thao tác demo theo kịch bản T16.

**Tiêu đề:** BR7: cặp sản phẩm mua cùng phiên được đếm sẵn theo lô, xếp theo lift và đặt cạnh số phiên mua cùng

**Ý chính (tối đa 4):**
- Hàng hoá hỏi: khách mua sản phẩm A thường mua kèm gì?
- `gold_br7.py` (Spark, theo lô): lượt mua trong `fact_event`, ghép từng cặp sản phẩm cùng phiên, tính support và lift
- Giữ sản phẩm ≥ 20 phiên, cặp ≥ 3 phiên, lift > 1: Parquet `product_affinity`, 314 dòng cả hai chiều, DuckDB đọc
- Nhập `1005115`: 10 dòng xếp lift giảm dần, kèm số phiên mua cùng; footer 2 partition (2 tệp), 10 dòng, p50 9.6 ms

Số liệu: docs/evidence/gate2b_screens.txt (dòng BR7), batch_timings.txt, ảnh gate2b_br7.png; REPORT.md §2.7, §5.2. Ý chính:
lượt mua lấy từ `fact_event` với `event_type_key` = 3 (processing/gold_br7.py dòng 17 và 22-36; `distinct()` ở dòng 35
cho mỗi cặp phiên và sản phẩm một dòng), rồi ghép cặp trong cùng `user_session` ở dòng 47-56; support = `co_count` /
số phiên có mua, lift = `co_count` × số phiên có mua / (n_a × n_b), ở dòng 41 và 67-68 (định nghĩa ở REPORT.md §2.7
dòng 114, API_CONTRACT.md dòng 554); "≥ 20 phiên" và "cặp ≥ 3 phiên" là `MIN_PRODUCT_SESSIONS` và `MIN_CO_COUNT` ở
dòng 18-19 (`co_count` đếm số phiên có cả hai sản phẩm, vì giỏ đã distinct; màn hình in nó ở cột "Sessions together");
"lift > 1" ở dòng 70; "cả hai chiều" là bản đảo chiều và `unionByName` ở dòng 72-79; "314 dòng" là `affinity rows 314`
ở docs/evidence/batch_timings.txt dòng 202, khớp correctness_8br.txt dòng 189 (314/314). Ngày 13/11 đếm lại bằng
DuckDB trên data/gold/product_affinity cũng ra 314 dòng, 98 sản phẩm gốc, và `1005115` có 15 cặp. Thứ tự `lift DESC,
co_count DESC` ở serving/api/routers/br7.py dòng 60 (commit 03ffd63 "T09: BR7 sorts by lift descending", vào main qua
PR #39); đầu bảng ghi "Ranked by lift · sessions break ties · lift above 1" ở web/src/pages/BR7Page.tsx dòng 163.
"`1005115`, 10 dòng" là cột "Xong khi" ở BR_SCOPE.md dòng 15, `TOP_N = 10` ở br7.py dòng 25 và footer ảnh
gate2b_br7.png (10.8 ms, Parquet, 2 partitions, 10 rows). "2 partition" và "p50 9.6 ms" là dòng BR7 của
gate2b_screens.txt dòng 46 (meta p50 9.6, meta p95 11.7, curl p50 22.8, curl p95 28.3). "2 partition" là số tệp
Parquet trong thư mục `product_affinity` mà br7.py đếm (dòng 44-46; hiện có hai tệp part-00000 và part-00001), không
phải thư mục ngày. 9.6 ms là QueryMeta.ms, đo quanh truy vấn DuckDB ở br7.py dòng 34-38. Lời thoại: "đếm sẵn theo lô"
là REPORT.md §2.7 dòng 116 (bảng cặp phải tính trước trên toàn tập dữ liệu); "lift, tức số lần mua cùng so với số lần
kỳ vọng nếu mua độc lập" là REPORT.md §2.7 dòng 114; "xếp theo lift, kèm số phiên mua cùng" là br7.py dòng 60 và các
cột Sessions together, Lift trên ảnh gate2b_br7.png; "lift cao trên vài phiên chưa chắc là quy luật" là REPORT.md §5.2
dòng 820 (1005230 có lift 4.07 nhưng chỉ mua cùng trong 3 phiên, còn 1004249 mua cùng 26 phiên với lift 1.72, khớp
ảnh). Lời thoại không có số liệu nào.

**Lời thoại:**
Với bộ phận hàng hoá, câu hỏi là: khách mua một sản phẩm thì thường mua kèm gì? Spark đếm sẵn theo lô từng cặp sản
phẩm mua trong cùng một phiên, rồi tính lift, tức số lần mua cùng so với số lần kỳ vọng nếu mua độc lập. Màn hình xếp
theo lift, kèm số phiên mua cùng, vì lift cao trên vài phiên chưa chắc là quy luật.

**Số âm tiết:** 71

---

## Trang 20 · BR3 · Sản phẩm đang tăng mạnh · Khang

Nguồn gợi ý: docs/BR_SCOPE.md BR3; ảnh docs/evidence/gate2b_br3.png (T14); thao tác demo theo kịch bản T16.

**Tiêu đề:** BR3: top 20 sản phẩm đang lên, tính lại mỗi phút ngay trên luồng sự kiện

**Ý chính (tối đa 4):**
- Hàng hoá hỏi: sản phẩm nào đang tăng mạnh trong 15 phút gần nhất?
- Spark Structured Streaming: cửa sổ 15 phút trượt mỗi phút, đếm lượt xem và thêm giỏ theo sản phẩm, lấy top 20
- Cassandra `trending_products`, khoá `(window_start, rank)`: một cửa sổ là một partition, đã xếp sẵn theo hạng
- Footer ghi 381 partition, 40 dòng: đọc khoá mọi cửa sổ để tìm cửa sổ mới nhất, rồi đọc nó và cửa sổ một phút trước

Số liệu: docs/evidence/gate2b_screens.txt (dòng BR3 và ghi chú BR3 ở "other calls"); REPORT.md §4.2 và §6.2. Ý 4: "381 partition, 40 dòng" là footer của ảnh gate2b_br3.png, giải thích ở ghi chú BR3 của gate2b_screens.txt: màn hình gọi hai lần nối tiếp (web/src/pages/BR3Page.tsx, fetchTrending). Lần gọi cửa sổ mới nhất báo 380 partition vì đếm cả danh sách khoá đọc bằng `SELECT DISTINCT window_start`, cộng 1 partition được đọc (serving/api/routers/br3.py). Lần gọi cửa sổ một phút trước đọc 1 partition. Lời thoại: "đọc khoá của mọi cửa sổ" là REPORT.md §4.2 ("API đọc danh sách khoá bằng SELECT DISTINCT window_start"). Ý 2, 3: processing/streaming_gold.py (cửa sổ 15 phút trượt 1 phút, top 20 theo lượt xem rồi lượt thêm giỏ) và serving/cassandra_schema.cql (`PRIMARY KEY (window_start, rank)`).

**Lời thoại:**
Cũng với bộ phận hàng hoá, câu hỏi là: sản phẩm nào đang tăng mạnh trong mười lăm phút gần nhất? Spark đếm lượt
xem và thêm giỏ trong cửa sổ mười lăm phút, trượt mỗi phút, rồi lấy top hai mươi. Mỗi cửa sổ là một partition trong
Cassandra, đã xếp sẵn theo hạng. Muốn tìm cửa sổ mới nhất thì phải đọc khoá của mọi cửa sổ.

**Số âm tiết:** 73

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

**Số âm tiết:** 65

---

## Trang 22 · Đánh giá: tính đúng đắn · Khang

Nguồn gợi ý: docs/evidence/correctness_8br.txt (T19).

**Tiêu đề:** So với một đáp án viết độc lập, cả 8 BR khớp 100%, trên ngưỡng 99%

**Ý chính (tối đa 4):**
- Đáp án viết bằng SQL DuckDB trên silver (BR6: tồn kho), không dùng code Spark; so từng dòng với đúng bảng màn hình đọc
- 8/8 BR khớp 100%; bốn BR luồng đo trên lượt phát lại 17/11, 15:00–21:30
- SCD2 sạch ở cả `dim_product` và `dim_user`: 0 khoảng chồng, 0 khoảng hở, đúng 1 dòng hiện hành mỗi khoá
- Giới hạn: số thô RFM trong danh sách khách của BR4 có thể là của lần chấm trước; điểm và phân khúc vẫn đúng

Số liệu: docs/evidence/correctness_8br.txt (bảng 8 dòng, phép thử watermark sai, SCD2, giới hạn BR4).

**Lời thoại:**
Để biết hệ thống tính đúng, nhóm em viết lại đáp án cho cả tám câu hỏi bằng SQL thuần trên dữ liệu đã làm sạch và tồn kho,
không dùng lại code Spark, rồi so từng dòng với đúng bảng mà màn hình đọc. Cả tám BR khớp một trăm phần trăm, trên
ngưỡng chín mươi chín phần trăm. Hai bảng chiều có lịch sử cũng sạch: không khoảng nào chồng hay hở, và mỗi khoá có
đúng một dòng hiện hành.

**Số âm tiết:** 87

---

## Trang 23 · Đánh giá: hiệu năng · Tín

Nguồn gợi ý: xem dòng Số liệu dưới đây.

**Tiêu đề:** Hiệu năng trong phạm vi máy demo

**Ý chính (tối đa 4):**
- Mỗi endpoint: 3 warm-up + 20 lần đo; API = QueryMeta.ms, HTTP = curl time_total kể cả JSON, chưa tính vẽ React
- API p95 cao nhất 40.0 ms (BR4), HTTP p95 cao nhất 63.9 ms (BR8). BR4 đo 5 lời gọi tuần tự; request phụ chưa đo lặp hết
- Streaming Run 1 theo kịp nguồn cấp 480.7 sự kiện/s; micro-batch p50 587-852 ms, chu kỳ 5 s; chưa thử quá tải
- Theo lô 426.5 s từ CSV tới gold (03/11). Số API/stream đo 10/11 trên máy Đắt, mẫu 7% khách

Số liệu: docs/evidence/gate2b_screens.txt; gate2b_curl_raw.txt; perf_table.md; streaming_perf.txt Run 1; batch_timings.txt. 10/11: main 02b22f1, máy Đắt 20 logical cores/15 GB RAM/WSL2; silver 4,754,015 dòng. Batch: 03/11, aa65472, 7 job. p95 nearest rank. BR4 đo từng R score rồi lấy worst per column, không phải timing browser end-to-end. BR2 thêm 15 request, BR3 thêm cửa sổ trước, BR7 thêm anchors chưa đo lặp toàn bộ. Không so trực tiếp 63.9 ms của mẫu với 50s quét toàn bộ CSV.

**Mặt slide:** Bảng native đủ 8 BR với API/HTTP p95. Bên phải là phương pháp, ngưỡng 2,000 ms, streaming và batch. Ghi giới hạn request phụ và React ngay mặt slide.

**Lời thoại:**
Về hiệu năng, mỗi endpoint được làm nóng ba lần rồi đo hai mươi lần. HTTP p95 nằm từ sáu phẩy một tới sáu mươi ba phẩy chín mili giây. Số này gồm truyền JSON, chưa tính vẽ React. Nhánh luồng theo kịp nguồn phát lại khoảng bốn trăm tám mươi mốt sự kiện mỗi giây, chưa thử quá tải. Nhánh theo lô mất khoảng bảy phút và chạy trước khi người dùng mở màn hình.

**Số âm tiết:** 76

---

## Trang 24 · Đánh giá: tính hữu dụng · Tín

Nguồn gợi ý: xem dòng Số liệu dưới đây.

**Tiêu đề:** Tính hữu dụng và giới hạn bằng chứng

**Ý chính (tối đa 4):**
- 8 câu hỏi có màn hình tương ứng và bộ lọc theo nghiệp vụ
- Điều hướng theo 4 nhóm người dùng; QueryMeta hiện ms, kho, partition và số dòng
- Khảo sát 5 người/4 tác vụ vẫn là kế hoạch, chưa có survey_responses.csv trong main
- Chưa đo mức hài lòng, thời gian tác vụ và tỉ lệ hoàn thành; không báo điểm hoặc tỉ lệ giả

Số liệu: docs/BR_SCOPE.md; web/src/App.tsx; web/src/components/QueryMeta.tsx; docs/EVALUATION_SURVEY.md; docs/REPORT.md §6.3, §6.4. Main f9bfab9 không có docs/evidence/survey_responses.csv. PR #51 và #52 ghi rõ chưa thực hiện khảo sát. Các SLO 4.0/5, 4.2/5, 100% là mục tiêu, không phải kết quả.

**Mặt slide:** Hai cột: bằng chứng chức năng đã có và khảo sát còn thiếu. Dòng kết luận giới hạn ở khả năng trả lời câu hỏi, chưa kết luận người dùng hài lòng.

**Lời thoại:**
Về tính hữu dụng, tám câu hỏi đã có màn hình tương ứng, thanh điều hướng chia theo bốn nhóm nghiệp vụ. Bộ lọc giúp thu hẹp dữ liệu, còn dòng chân màn hình cho biết thời gian truy vấn và số partition đã đọc. Tuy nhiên, đây mới là đối chiếu chức năng. Khảo sát năm người với bốn tác vụ vẫn chưa thực hiện, nên nhóm chưa có điểm hài lòng hay tỉ lệ hoàn thành tác vụ.

**Số âm tiết:** 80

---

## Trang 25 · Kết luận, giới hạn và hướng phát triển · Tín

Nguồn gợi ý: xem dòng Số liệu dưới đây.

**Tiêu đề:** Kết quả, giới hạn và bước tiếp theo

**Ý chính (tối đa 4):**
- 8/8 BR khớp 100% trong tập kiểm của nhóm; HTTP p95 cao nhất 63.9 ms ở các endpoint đã đo, chưa gồm vẽ React
- Giới hạn: một máy, Cassandra 1 node, mẫu 7% khách; replay, chưa thử quá tải hoặc luồng đến trễ thật
- Tồn kho/catalogue giả lập; thẻ BR6 đếm phần trả về; chưa khảo sát và chưa xác thực/phân quyền
- Tiếp theo: khảo sát, endpoint đếm đầy đủ, Kafka (rà source, replayer, checkpoint) rồi đo dữ liệu đủ trên cụm nhiều node

Số liệu: docs/evidence/correctness_8br.txt mục T19 và t14_checks.txt (10/11/2026); docs/evidence/gate2b_screens.txt; docs/REPORT.md §6.4; processing/source.py; PR #52. 100% chỉ là trong tập so sánh đã nêu, không suy rộng mọi điều kiện. Giới hạn BR4 vẫn còn: số thô của khách có thể thuộc lần chấm trước, điểm/phân khúc đúng. Kafka không được mô tả là chỉ sửa một file.

**Mặt slide:** Kết quả ở đầu, bảng native ghép giới hạn với bước tiếp theo. Kết luận chỉ nằm trong phạm vi bằng chứng đã đo.

**Lời thoại:**
ShopInsight đã nối dữ liệu với tám câu hỏi nghiệp vụ. Tám BR khớp đáp án độc lập trong phép kiểm của nhóm, và các lượt HTTP được đo đều dưới hai giây. Kết quả chỉ đúng trong phạm vi một máy, mẫu bảy phần trăm khách và luồng phát lại. Tồn kho là giả lập, khảo sát còn thiếu. Bước tiếp theo là khảo sát người dùng, bổ sung thẻ đếm đầy đủ, rồi thử luồng Kafka và cụm nhiều máy. Em cảm ơn cô và các bạn.

**Số âm tiết:** 89

---

## Trang 26 · Tài liệu tham khảo · Tín

Nguồn gợi ý: trang này chỉ hiện, không đọc. Danh sách lấy từ mục Tài liệu tham khảo của báo cáo nộp (Google Doc của
Khang, 18 mục, đúng thứ tự của Doc; REPORT.md chỉ có 12 mục, thứ tự khác), nên khối này không cần lời thoại.

**Tiêu đề:** Tài liệu tham khảo

**Ý chính (tối đa 4):** (trang này là danh sách, không giới hạn 4 ý)
- [1] M. Kechinov (REES46), eCommerce behavior data from multi category store, Kaggle
- [2] A. M. Hughes, Strategic Database Marketing, Probus Publishing, 1994
- [3] R. Agrawal et al., Mining association rules between sets of items in large databases, ACM SIGMOD, 1993
- [4] S. Brin et al., Dynamic itemset counting and implication rules for market basket data, ACM SIGMOD, 1997
- [5] Databricks, What is the medallion lakehouse architecture?, docs.databricks.com/aws/en/lakehouse/medallion
- [6] R. Kimball, M. Ross, The Data Warehouse Toolkit, 3rd ed., Wiley, 2013
- [7] Apache Software Foundation, Apache Parquet: File format, parquet.apache.org/docs/file-format/
- [8] PostgreSQL Global Development Group, PostgreSQL 16 Documentation, Sec. 5.11, Ch. 11, postgresql.org/docs/16/
- [9] M. Raasveldt, H. Mühleisen, DuckDB: An embeddable analytical database, ACM SIGMOD, 2019
- [10] A. Lakshman, P. Malik, Cassandra: A decentralized structured storage system, ACM SIGOPS OSR, 2010
- [11] M. Kleppmann, Designing Data-Intensive Applications, O'Reilly Media, 2017
- [12] M. Zaharia et al., Apache Spark: A unified engine for big data processing, Communications of the ACM, 2016
- [13] M. Armbrust et al., Structured Streaming: A declarative API for real-time applications..., ACM SIGMOD, 2018
- [14] Apache Software Foundation, Structured Streaming Programming Guide: watermarking, spark.apache.org/docs/latest/
- [15] N. Marz, J. Warren, Big Data: Principles and Best Practices of Scalable Realtime Data Systems, Manning, 2015
- [16] J. Kreps, Questioning the Lambda Architecture, O'Reilly Radar, 2014
- [17] W. H. Inmon, Building the Data Warehouse, 4th ed., Wiley, 2005
- [18] M. Armbrust, A. Ghodsi, R. Xin, M. Zaharia, Lakehouse: A new generation of open platforms..., CIDR, 2021

Số liệu: Mục Tài liệu tham khảo của báo cáo nộp (Google Doc của Khang, đọc ngày 13/11/2026), 18 mục theo đúng thứ tự của Doc.

**Lời thoại:** (không có)

**Số âm tiết:** 0

---

## Lỗi trình bày (không phải trang slide)

Dùng cho T26 (Tín rà PDF nháp). Lỗi nội dung thì sửa thẳng trong khối trang ở trên; nếu là số sai thì ghi số đúng
kèm tên file evidence ngay tại khối đó. Ở đây chỉ ghi lỗi trình bày (màu, bố cục, hình), mỗi lỗi một dòng: số
trang · lỗi · cách sửa đề xuất.

-
