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

Nguồn gợi ý: điền họ tên đầy đủ và MSHV của bốn bạn (trên slide đang để trống).

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
Bài trình bày đi theo đường của dữ liệu: bài toán, nguồn dữ liệu, kiến trúc, demo tám màn hình, rồi đánh giá xem hệ
thống có đúng, có nhanh và có dùng được không.

**Số âm tiết:** 36

---

## Trang 03 · Bối cảnh · Khang

Nguồn gợi ý: REPORT.md §1.1 Bối cảnh, §1.3 Vì sao không truy vấn thẳng nhật ký thô.

**Tiêu đề:** Nhật ký thô có đủ dữ liệu, nhưng câu nào cũng phải quét lại cả 9.0 GB và làm sạch lại từ đầu

**Ý chính (tối đa 4):**
- Nhật ký REES46 tháng 11/2019: 67,501,979 sự kiện, 9.0 GB CSV; mỗi sự kiện là một lần xem, thêm giỏ hoặc mua
- Hỏi thẳng tệp CSV: doanh thu theo ngành hàng mất 50 giây với awk đơn luồng, khoảng 2–9 giây với DuckDB song song, vì câu nào cũng quét lại cả 9.0 GB; ngưỡng là 2 giây
- Dữ liệu thô chưa sạch: 32.4% sự kiện không có tên ngành hàng, giờ ghi theo UTC nên lệch ngày so với giờ Việt Nam
- ShopInsight làm trước một lần những việc tốn kém, để màn hình chỉ đọc phần nhỏ nó cần

Số liệu: đo trên `data/raw/2019-Nov.csv` bằng `wc -l`, `ls -l`, `time` và `awk` (máy 12 nhân, 15 GB RAM, WSL2); DuckDB:
`docs/evidence/review_20261113/r1_raw_scan_timing.txt` (máy 20 nhân). Lệnh đo của từng số ở REPORT.md, bảng "Nguồn số
liệu của mục 1". "Khoảng 2–9 giây" là DuckDB 1.5.5 chạy câu doanh thu theo ngành hàng trên cả tệp: 9.05 s ở lần đầu,
khi page cache mới có 0.4 GB, và 1.73 s khi cả tệp đã nằm trong page cache (r1_raw_scan_timing.txt dòng 10-13 và 26-29).
"Tên ngành hàng" là cột `category_code`; `category_id` thì sự kiện nào cũng có.

**Lời thoại:**
Đồ án dùng nhật ký hành vi của một sàn thương mại điện tử trong tháng mười một năm hai nghìn mười chín: sáu mươi bảy
triệu rưỡi sự kiện, nặng chín gigabyte. Dữ liệu thì đủ, nhưng hỏi thẳng vào nó thì câu nào cũng phải quét lại cả tệp:
doanh thu theo ngành hàng mất năm mươi giây với awk chạy một luồng, và khoảng hai tới chín giây với DuckDB chạy song
song. Dữ liệu thô cũng chưa sạch: gần một phần ba sự kiện thiếu tên ngành hàng, và giờ ghi theo UTC nên lệch ngày so
với giờ Việt Nam. Vì vậy ShopInsight làm trước một lần những việc tốn kém, để mỗi màn hình chỉ đọc đúng phần nhỏ nó
cần.

**Số âm tiết:** 134

---

## Trang 04 · Bốn nhóm người dùng · Khang

Nguồn gợi ý: REPORT.md §1.2 Các bên liên quan.

**Tiêu đề:** Bốn nhóm người dùng, hai nhịp ra quyết định

**Ý chính (tối đa 4):**
- Ban điều hành: doanh thu từng phút (BR1)
- Tăng trưởng và marketing: phễu chuyển đổi, phân khúc khách, giỏ bỏ quên (BR2, BR4, BR5)
- Hàng hoá: sản phẩm đang được quan tâm, sản phẩm mua kèm (BR3, BR7)
- Vận hành và rủi ro: nguy cơ hết hàng, đơn bất thường (BR6, BR8)

Số liệu: các câu hỏi và BR của từng nhóm là bảng REPORT.md §1.2 dòng 21-26 và bảng BR ở §2 dòng 65-72; hai nhịp
(BR1, BR3, BR5, BR8 thời gian thực; BR2, BR4, BR6, BR7 theo lô) là §1.2 dòng 28 và §2 dòng 74. Trang không có số đo.

**Mặt slide (bản 26, 14/11):** bốn hàng theo đúng thứ tự lời thoại. Mỗi hàng mở bằng một khối navy có icon Lucide và
tên nhóm, rồi tới mỗi BR một ô chứa câu hỏi trong ngoặc kép: BR1 "Doanh thu từng phút ra sao, ngành hàng nào đang kéo
doanh thu?"; BR2 "Khách rời đi ở bước nào?", BR4 "Nhóm khách nào nên đầu tư?", BR5 "Ai bỏ quên giỏ hàng?"; BR3 "Sản
phẩm nào đang được quan tâm?", BR7 "Khách mua sản phẩm A thường mua kèm gì?"; BR6 "Sản phẩm nào sắp hết hàng, ở kho
nào?", BR8 "Tài khoản nào đặt đơn bất thường?". Viền cam kèm icon tia sét là thời gian thực, viền xanh kèm icon đồng hồ
quay ngược là theo lô. Dòng cuối: "Hai nhịp cho 8 câu hỏi: thời gian thực · 4 BR trả lời gần như ngay lúc sự kiện xảy
ra | theo lô · 4 BR tính trên toàn bộ lịch sử". Không lặp sơ đồ hai cột của trang 05 (không có người phụ trách, không
có nơi lưu).

**Lời thoại:**
Người dùng là bốn nhóm trong công ty. Ban điều hành theo dõi doanh thu từng phút. Bên marketing hỏi khách rời đi ở
bước nào, nhóm khách nào nên đầu tư, và ai bỏ quên giỏ hàng. Bên hàng hoá muốn biết sản phẩm nào đang được quan tâm và
hay được mua kèm gì. Còn vận hành cần biết sản phẩm nào sắp hết hàng và tài khoản nào đặt đơn bất thường. Một nửa số
câu hỏi cần trả lời gần như ngay lúc sự kiện xảy ra, nửa còn lại tính theo lô trên toàn bộ lịch sử. Tám câu hỏi này
chính là tám yêu cầu nghiệp vụ mà bạn Nguyên sẽ trình bày ngay sau đây.

**Số âm tiết:** 124

---

## Trang 05 · Tám yêu cầu nghiệp vụ · Nguyên

Nguồn gợi ý: REPORT.md §2, docs/BR_SCOPE.md.

**Tiêu đề:** Tám câu hỏi nghiệp vụ chia làm hai nhịp: trả lời ngay khi sự kiện xảy ra, hoặc tính trên toàn bộ lịch sử

**Ý chính (tối đa 4):**
- Mỗi BR là một câu hỏi của một nhóm người dùng, có một màn hình riêng
- Bốn BR cần trả lời ngay (BR1, BR3, BR5, BR8): chạy theo luồng, ghi Cassandra
- Bốn BR cần toàn bộ lịch sử (BR2, BR4, BR6, BR7): chạy theo lô trên kho dữ liệu
- Mỗi thành viên giữ trọn hai BR, một theo lô và một theo luồng; hỏi thẳng tệp CSV thô 9.0 GB thì câu nào cũng phải quét lại cả tệp chưa làm sạch

Số liệu: docs/BR_SCOPE.md (phạm vi, nguồn dữ liệu và người phụ trách của 8 BR). Chi tiết: REPORT.md §1.3, §2. Tiêu đề: hai nhịp (trả lời gần như ngay lúc sự kiện xảy ra, hoặc tính theo lô
trên toàn bộ lịch sử) là REPORT.md §1.2 dòng 28. Ý 1: REPORT.md §2 dòng 61 ("Mỗi yêu cầu trả lời một câu hỏi của một
nhóm người dùng ở mục 1.2 và có một màn hình riêng trên dashboard"). Ý 2 và 3: bảng BR ở REPORT.md §2 dòng 65-72 (cột
"Cách xử lý", "Nơi lưu kết quả") và dòng 74 (BR1, BR3, BR5, BR8 đọc luồng, ghi Cassandra; BR2, BR4, BR6, BR7 đọc kho
dữ liệu dạng mô hình chiều, riêng BR6 ghi Cassandra); cột "Nguồn" của docs/BR_SCOPE.md; trong code: `STREAMING_TABLES`
ở processing/streaming_gold.py dòng 112 (gmv_by_minute, trending_products, abandoned_carts, order_velocity_alerts),
processing/batch_gold.py dòng 4-6 (BR2, BR4, BR6) và processing/gold_br7.py dòng 13-14 (BR7 đọc data/warehouse). Ý 4:
REPORT.md §2 dòng 61 ("một yêu cầu xử lý theo lô và một yêu cầu xử lý thời gian thực") và cột "Phụ trách" của
docs/BR_SCOPE.md (Đắt BR1, BR2; Khang BR3, BR4; Nguyên BR5, BR7; Tín BR6, BR8); "câu nào cũng phải quét lại cả tệp
chưa làm sạch" là REPORT.md §1.3 dòng 34 (mọi câu hỏi phải quét cả tệp). Câu này không còn nói "không câu nào xong dưới
2 giây": DuckDB song song quét cả tệp mất 1.73–9.05 giây (docs/evidence/review_20261113/r1_raw_scan_timing.txt, trang
03). Lời thoại: "chín gigabyte" là 9,006,762,395 byte của data/raw/2019-Nov.csv (r1_raw_scan_timing.txt dòng 4); "BR
một, ba, năm và tám" và "BR hai, bốn, sáu và bảy" là các mã ở REPORT.md §2 dòng 74; lời thoại không có số đo nào khác.

**Mặt slide:** sơ đồ hai cột: bốn BR thời gian thực (BR1, BR3, BR5, BR8) ghi Cassandra ở bên trái, bốn BR theo lô (BR2, BR4,
BR7 ghi Parquet cho DuckDB; BR6 ghi Cassandra) ở bên phải, cột giữa là người phụ trách mỗi hàng; ô BR3 ghi "Sản phẩm
đang được quan tâm". Dòng cuối: "Hỏi thẳng tệp CSV thô 9.0 GB thì câu nào cũng phải quét lại cả tệp chưa làm sạch."

**Lời thoại:**
Mỗi yêu cầu nghiệp vụ, gọi tắt là BR, là câu hỏi của một nhóm người dùng và có một màn hình riêng. BR một, ba, năm và
tám cần trả lời ngay, nên chạy theo luồng, tức tính liên tục khi sự kiện tới, rồi ghi vào Cassandra, cơ sở dữ liệu tra
nhanh theo khoá. BR hai, bốn, sáu và bảy cần toàn bộ lịch sử, nên chạy theo lô trên kho dữ liệu. Mỗi thành viên giữ
trọn hai BR, một theo lô, một theo luồng. Còn nếu hỏi thẳng nhật ký thô thì câu nào cũng phải quét lại cả chín
gigabyte dữ liệu chưa làm sạch.

**Số âm tiết:** 120

---

## Trang 06 · Nhật ký sự kiện và đặc trưng Big Data · Nguyên

Nguồn gợi ý: REPORT.md §3.1 và đoạn đặc trưng Big Data cuối §3 (T04).

**Tiêu đề:** Nguồn chính là 67.5 triệu sự kiện thật, lấy mẫu theo khách để lịch sử của mỗi khách còn nguyên

**Ý chính (tối đa 4):**
- REES46 tháng 11/2019, 9 cột; lấy mẫu 7% khách bằng giá trị băm của mã khách, giữ mọi sự kiện của khách đó
- Bảy quy tắc làm sạch, đổi sang giờ Việt Nam, dữ liệu trải ra 31 ngày
- Big Data: 9.0 GB; 4,767,012 sự kiện mẫu, 4,754,015 sau làm sạch; phát lại ×60 chiều tối ngày đông nhất (17/11/2019): ~481 sự kiện/s, gấp 4.2 lần cả sàn thật (114.1/s); catalogue JSON lồng nhau
- Dữ liệu gốc có 38.4 giờ liền không có lượt mua: đặc điểm của nguồn, không phải lỗi pipeline

Số liệu: `data/raw/2019-Nov.csv`; docs/evidence/batch_timings.txt mục 2 (BRONZE OK, SILVER OK);
docs/evidence/streaming_perf.txt (lượt phát lại, 480.7 sự kiện/s); docs/evidence/review_20261113/r1_raw_profile.txt mục 4
(tốc độ thật). Chi tiết: REPORT.md §3.1 và §3.5, bảng "Nguồn số liệu của mục 3". Tiêu đề: 67,501,979 sự kiện ở REPORT.md §3.1 dòng 146 và dòng
216 (`wc -l`); "thật" ở bảng nguồn dòng 139; lấy mẫu theo khách và giữ mọi sự kiện của khách ở đoạn "Lấy mẫu" dòng
160. Ý 1: REES46, tháng 11/2019 và 9 cột ở dòng 146-158 và dòng 216 (`head -1`), khớp 9 `StructField` ở
processing/schema.py dòng 44-52; quy tắc `pmod(hash(user_id), 100) < 7` ở dòng 160 và `SAMPLE_RULE` ở
ingestion/load_bronze.py dòng 71. Ý 2: bảy quy tắc ở dòng 169-176 và `clean()` ở processing/batch_silver.py dòng
131-177 (quy tắc 6 ở dòng 174-175); 31 ngày ở dòng 178 và dòng 222. Ý 3: 9.0 GB = 9,006,762,395 byte ở dòng 210 và
233; 4,767,012 là tập mẫu 7% ở tầng bronze, dòng 221 và 235; 4,754,015 ở dòng 222 và 237; "×60 ~481 sự kiện/s" là
`--speed 60`, 187,468 / (78 × 5 giây) = 480.7, ở dòng 210 và 239, nguồn docs/evidence/streaming_perf.txt dòng 25
("offered rate 480.7 rows/s", Run 1); khung phát lại 15:00–21:30 giờ Việt Nam ngày 17/11 ở correctness_8br.txt dòng
15-16. "Ngày đông nhất (17/11/2019)" là ngày có nhiều lượt mua nhất tháng, 166,319 lượt trên cả tệp gốc
(docs/evidence/review_20261113/r1_raw_profile.txt mục 1, dòng 21 và 36). "Cả sàn thật (114.1/s)" là cả tệp gốc trong
cùng khung 17/11 08:00–14:30 UTC: 2,670,632 sự kiện / 23,400 giây (r1_raw_profile.txt mục 4, dòng 49); "gấp 4.2 lần"
là 480.7 / 114.1 = 4.21: 481 là tốc độ của bản phát lại mẫu 7% nhanh gấp 60 lần, không phải tốc độ thật của sàn.
Catalogue JSON lồng nhau ở dòng 210 và 241. Ý 4: 38.4 giờ (14/11 18:09:37 tới 16/11 08:32:34 UTC) ở dòng 182 và 224;
"đặc điểm của nguồn, không phải lỗi pipeline" vì khoảng trống này có ngay trên tệp CSV gốc, trước mọi bước xử lý (đo
lại bên dưới). Đo lại bằng DuckDB ngày 13/11: bronze 4,767,012 dòng; silver 4,754,015 dòng, 31 ngày
`event_date`; data/stream_landing có 187,468 dòng trong 78 tệp, 08:00:00 tới 14:29:59 UTC; trên data/raw/2019-Nov.csv
khoảng trống dài nhất giữa hai lượt mua là 38.3825 giờ, đúng hai mốc trên. Lời thoại: "sáu mươi bảy triệu rưỡi" là
67,501,979; "chín cột" là 9 cột; "bảy phần trăm" là quy tắc `< 7` trên 100; "dữ liệu trải ra ba mươi mốt ngày" là
31 thư mục ngày của silver: sự kiện 17:00–24:00 UTC ngày 30/11 thuộc ngày 1/12 theo giờ Việt Nam (REPORT.md §3.1 dòng
178); "chín gigabyte" là 9.0 GB; "gần bốn triệu tám trăm nghìn dòng" là 4,767,012 của tập mẫu; "ngày mười bảy, ngày
đông nhất tháng" là 17/11 (r1_raw_profile.txt dòng 36); "nhanh gấp sáu mươi lần" là `--speed 60`; "khoảng bốn trăm tám
mươi mốt" là 480.7; "khoảng một trăm mười bốn" là 114.1 (r1_raw_profile.txt dòng 49); "gấp hơn bốn lần thực tế" là
480.7 / 114.1 = 4.21; "hơn ba mươi tám giờ" là 38.4 giờ.

**Lời thoại:**
Nguồn chính là sáu mươi bảy triệu rưỡi sự kiện thật, ghi trong chín cột. Nhóm lấy bảy phần trăm khách theo giá trị băm
của mã khách, giữ trọn lịch sử của họ. Sau bảy quy tắc làm sạch và bước đổi sang giờ Việt Nam, dữ liệu trải ra ba mươi
mốt ngày. Về Big Data: tệp gốc chín gigabyte, tập mẫu gần bốn triệu tám trăm nghìn dòng. Khi demo, nhóm phát lại chiều
tối ngày mười bảy, ngày đông nhất tháng, nhanh gấp sáu mươi lần, được khoảng bốn trăm tám mươi mốt sự kiện mỗi giây.
Lúc ấy cả sàn thật chỉ có khoảng một trăm mười bốn sự kiện mỗi giây, nên luồng phải chịu tải gấp hơn bốn lần thực tế.
Catalogue sản phẩm là JSON lồng nhau. Tệp gốc có hơn ba mươi tám giờ liền không một lượt mua; nhóm để nguyên.

**Số âm tiết:** 162

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
máy có cùng bảng thời gian. Catalogue có thuộc tính sinh từ mã sản phẩm nên luôn ra giống nhau, để so hai kiểu cột
lồng nhau, jsonb và struct. Tồn kho sinh theo lượt mua thật, để BR sáu có dữ liệu mà tốc độ bán vẫn đúng nhu cầu.
Catalogue và tồn kho là giả lập, chỉ minh hoạ kỹ thuật. Tiếp theo, bạn Đắt sẽ trình bày kiến trúc xử lý bốn nguồn này.

**Số âm tiết:** 112

---

## Trang 08 · Kiến trúc tổng thể · Đắt

Nguồn gợi ý: REPORT.md §4.1; hình docs/figures/shopinsight_architecture.html, đã có trên slide. Ô PostgreSQL
ghi số đo T12 ở T25.

**Tiêu đề:** Hai nhánh xử lý, hai nơi phục vụ màn hình: Parquet cho 3 màn hình báo cáo, Cassandra cho 5 màn hình tra theo khoá

**Ý chính (tối đa 4):**
- Nhánh theo lô: Spark lấy mẫu 7% khách, làm sạch, dựng kho dữ liệu, ghi Parquet chia thư mục theo ngày
- Nhánh thời gian thực: phát lại nhật ký thành tệp JSON, Spark Structured Streaming tính ngay khi sự kiện tới
- DuckDB đọc Parquet cho BR2, BR4, BR7; Cassandra phục vụ BR1, BR3, BR5, BR8 từ luồng và BR6 từ lô
- PostgreSQL: bản dựng thứ hai của cùng kho dữ liệu, làm phương án thay thế để so sánh, không phục vụ màn hình

Số liệu: hình docs/figures/shopinsight_architecture.html; ô PostgreSQL lấy số từ
`benchmark/results/summary_20261110_010557.csv` (T25 ghi kèm giới hạn ở REPORT.md §4.4, "Bốn điều phải đọc kèm bảng
này"); hai bản kho dữ liệu có số dòng bằng nhau ở docs/evidence/pg_vs_parquet_counts.txt. Lời thoại: "bảy phần trăm"
là quy tắc lấy mẫu ở REPORT.md §3.1 và §4.1.

**Mặt slide:** sơ đồ kiến trúc: hàng trên là nhánh thời gian thực (phát lại → Structured Streaming → Cassandra), hàng dưới
là nhánh theo lô (CSV → Spark theo lô → Parquet), FastAPI (có DuckDB) ở giữa, 5 màn hình tra theo khoá và 3 màn hình
báo cáo bên phải, PostgreSQL nét đứt "cùng 8 bảng star, phương án thay thế" (nhãn trên đường nét đứt: "phương án thay
thế").

**Lời thoại:**
Kiến trúc gồm hai nhánh. Nhánh theo lô: Spark lấy mẫu bảy phần trăm khách, làm sạch, dựng kho dữ liệu, rồi lưu
Parquet, định dạng lưu theo cột, chia thư mục theo ngày, để DuckDB đọc cho ba màn hình báo cáo. Nhánh thời gian thực:
nhật ký được phát lại thành từng tệp JSON, Spark Structured Streaming tính ngay khi sự kiện tới rồi ghi vào Cassandra.
Cassandra phục vụ năm màn hình tra theo khoá, riêng BR sáu tính theo lô. PostgreSQL chứa bản thứ hai của chính kho dữ
liệu này, làm phương án thay thế để so sánh.

**Số âm tiết:** 116

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
Ở mức khái niệm có mười một thực thể. Ở mức logic là một star schema: bảng fact ở giữa ghi việc đã xảy ra, các bảng
dimension quanh nó mô tả ai, cái gì, khi nào. Ba fact theo ba kiểu của Kimball: từng sự kiện, từng phiên qua phễu, và
tồn kho mỗi ngày. Sản phẩm và khách hàng là SCD Type hai: đổi thì thêm phiên bản, sự kiện cũ vẫn trỏ tới bản cũ. Sản
phẩm thêm phiên bản khi giá cuối ngày đổi. Khách thì thêm phiên bản khi điểm RFM đổi; RFM là lần mua gần nhất, tần
suất và số tiền chi, chấm lại mỗi tuần.

**Số âm tiết:** 125

---

## Trang 10 · Mô hình dữ liệu: mức vật lý · Đắt

Nguồn gợi ý: REPORT.md §4.4 (T15); evidence E1, E4, E5, explain_star_join.txt, gin_vs_seqscan.txt.

**Tiêu đề:** Ở mức vật lý, lọc một ngày chỉ mở 1/31 thư mục; BRIN lọc một giờ nhanh gấp ~21 lần quét cả bảng

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
duckdb_zonemap.txt (tệp không còn). Tiêu đề: "1/31 thư mục" là "Lọc một ngày" ở trên; "nhanh gấp ~21 lần" là 88.218 /
4.125 = 21.4, p50 của `seq_scan` chia cho p50 của `postgres,event_time_one_hour,brin` trong summary. Lời thoại:
"khoảng bốn mili giây" và "gần chín mươi mili giây" là p50 của `postgres,event_time_one_hour,brin` (4.125 ms) và
`seq_scan` (88.218 ms) trong summary; "Spark ghi cột thời gian theo kiểu timestamp cũ" là
`spark.sql.parquet.outputTimestampType = INT96` ở presentation_parquet_run.txt dòng 28, không có min/max vì INT96
không có thứ tự sắp xếp (dòng 316-318); "cách sửa thì đã rõ" là `spark.sql.parquet.outputTimestampType=TIMESTAMP_MICROS`
ở dòng 319.

**Mặt slide:** Parquet bên trái (thư mục `event_date`, mỗi tệp 1 row group, `event_time` INT96 không có min/max), hai truy
vấn ở giữa ("Lọc một ngày" đọc 1/31 thư mục, 1.565 ms; "Lọc một giờ" đọc 31/31 tệp, 5.891 ms), PostgreSQL bên phải
(partition, index; BRIN 4.125 ms so với seq scan 88.218 ms).

**Lời thoại:**
Parquet là nơi lưu chính. Mỗi fact chia partition theo ngày, tức mỗi ngày một thư mục, nên lọc một ngày chỉ mở một thư
mục. Row group, tức một khối dòng trong tệp, có ghi min max từng cột để bỏ qua khối không cần đọc. Ở đây mỗi tệp chỉ
có một row group, và Spark ghi cột thời gian theo kiểu timestamp cũ nên cột này không có min max. Cách sửa thì đã rõ,
nhưng không màn hình nào lọc theo giờ, nên nhóm giữ nguyên. Bản PostgreSQL có thêm index. BRIN, loại index chỉ nhớ min
max của từng nhóm trang, lọc một giờ sự kiện mất khoảng bốn mili giây, quét cả bảng mất gần chín mươi mili giây.

**Số âm tiết:** 138

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
Cả hai nhánh chạy trên Spark ở chế độ local, mỗi script một tiến trình dùng mọi nhân CPU. Bảy job theo lô chạy hết
khoảng bảy phút. Nhánh thời gian thực dùng Structured Streaming: cứ năm giây, Spark gom tệp mới thành một micro-batch,
tức một lô nhỏ. Watermark mười phút, tức Spark chờ sự kiện trễ thêm mười phút rồi mới đóng cửa sổ. Hai nhánh gọi chung
một hàm làm sạch. Khi demo, một micro-batch thường xong chưa tới một giây. Luồng ghi kết quả vào Cassandra, phần này
bạn Tín sẽ trình bày.

**Số âm tiết:** 112

---

## Trang 12 · Cassandra: thiết kế khoá từ câu hỏi của màn hình · Tín

Nguồn gợi ý: REPORT.md §4.2, serving/cassandra_schema.cql.

**Tiêu đề:** Cassandra chỉ đọc nhanh khi hỏi theo partition key: mỗi màn hình một bảng, khoá chọn theo câu hỏi của màn hình đó

**Ý chính (tối đa 4):**
- Partition key chọn partition, clustering key xếp sẵn dòng; không có phép nối, lọc ngoài khoá phải quét cả bảng
- Ngược với star schema (trang 09): 5 màn hình, 5 bảng; thêm câu hỏi là thêm một bảng và một đường ghi
- `stockout_risk` (benchmark 10/11, p50): hỏi một kho 1.1 ms; hỏi một sản phẩm 81.1 ms, đọc cả 63,655 dòng để trả 5
- Ba bảng để lại dòng cũ, ba cách dọn: xoá partition kho (BR6), xoá partition cửa sổ (BR3), upsert không xoá (BR5)

Số liệu: serving/cassandra_schema.cql; benchmark/results/summary_20261110_010557.csv và plans_20261110_010557.txt (10/11,
p50). Chi tiết: REPORT.md §4.2 và §4.4 (bảng số đo). Tiêu
đề: "mỗi màn hình một bảng" là năm router Cassandra, mỗi router chỉ đọc một bảng (serving/api/routers/br1.py dòng 49
`gmv_by_minute`; br3.py dòng 46 và 52-53 `trending_products`; br5.py dòng 43-44 và 66 `abandoned_carts`; br6.py dòng
77-94 `stockout_risk`; br8.py dòng 52-53 và 69 `order_velocity_alerts`); "khoá chọn theo câu hỏi của màn hình đó" là
tên REPORT.md §4.2 (dòng 308, "thiết kế ngược từ câu hỏi"). Ý chính 1: REPORT.md §4.2 dòng 312-316 (partition key quyết định phân vùng, clustering key quyết định
thứ tự có sẵn trên đĩa, không có phép nối, lọc cột ngoài khoá phải quét cả bảng và cần `ALLOW FILTERING`). Ý chính 2:
"5 bảng" là năm CREATE TABLE ở serving/cassandra_schema.cql dòng 6, 16, 28, 39, 49; "thêm một bảng và một đường ghi"
là REPORT.md §4.2 dòng 328; star schema là trang 09. Ý chính 3: summary_20261110_010557.csv dòng 21
(`cassandra,stockout_risk,right_key`, p50 1.113 ms, 100 dòng) và dòng 22 (`wrong_key`, p50 81.089 ms, 5 dòng); hai câu
truy vấn (`WHERE warehouse_id = 1 LIMIT 100` và `WHERE product_id = 1002540 ALLOW FILTERING`) và "Read 63655 live
rows" ở benchmark/results/plans_20261110_010557.txt dòng 1780-1804; 63,655 cũng là số dòng của cả bảng lúc đo
(benchmark/results/env_20261110_010557.txt dòng 28); REPORT.md §4.4 dòng 632-633; làm tròn 1.1 và 81.1 như REPORT.md
§4.5 dòng 656-657; "10/11" là ngày chạy benchmark năm 2026 (REPORT.md dòng 613), không phải ngày của dữ liệu. Ý chính
4: REPORT.md §4.2 dòng 341-346; code: `DELETE FROM stockout_risk WHERE warehouse_id = ?` ở processing/batch_gold.py
dòng 352, `DELETE FROM trending_products WHERE window_start = ?` ở processing/streaming_gold.py dòng 247, khoá
`((event_date), user_session)` của abandoned_carts ở serving/cassandra_schema.cql dòng 35 (upsert, không xoá). Lời
thoại: "khoảng một mili giây" là p50 1.113 ms (summary dòng 21); "phải quét cả bảng" là seq scan đọc 63,655 dòng,
bằng cả bảng (plans dòng 1803-1804, env dòng 28); "chậm hơn khoảng bảy mươi ba lần" là 81.089 / 1.113 = 72.9,
REPORT.md §4.4 dòng 638; "khi giá trị trong khoá đổi, dòng cũ vẫn nằm lại" là REPORT.md §4.2 dòng 341 (cột khoá sắp
xếp đổi giá trị giữa hai lần ghi thì dòng cũ vẫn nằm đó).

**Mặt slide:** năm thẻ bảng (partition key, clustering key, cách dọn dòng cũ, viền cam = ghi từ luồng, xanh = theo lô) và
phép so khoá đúng/khoá sai trên `stockout_risk` (1.1 ms so với 81.1 ms, quét cả 63,655 dòng).

**Lời thoại:**
Cassandra không có phép nối, chỉ đọc nhanh khi hỏi theo partition key, tức khoá quyết định dòng nằm ở partition nào.
Vì vậy, khác với star schema, mỗi câu hỏi có một bảng riêng, khoá chọn theo chính câu hỏi đó. Bảng nguy cơ hết hàng
chia partition theo kho: hỏi một kho mất khoảng một mili giây, hỏi một sản phẩm phải quét cả bảng, chậm hơn khoảng bảy
mươi ba lần. Khi giá trị trong khoá đổi, dòng cũ vẫn nằm lại, nên ba bảng có ba cách dọn riêng.

**Số âm tiết:** 103

---

## Trang 13 · Phương án thay thế và vì sao không chọn · Tín

Nguồn gợi ý: REPORT.md §4.5 (T22); số đo benchmark T12, T14 và E4.

**Tiêu đề:** Ở mẫu 7%, PostgreSQL trả lời câu BR1 nhanh ngang Cassandra: freshness đến từ luồng tính trước, không từ engine

**Ý chính (tối đa 4):**
- Câu hỏi BR1, p50: Cassandra 2.2 ms đọc bảng gold đã tính trước; trên star schema, PostgreSQL 2.0 ms, DuckDB 12.1 ms
- Freshness: luồng ghi sau mỗi micro-batch 5 giây, còn dựng lại kho dữ liệu và nạp PostgreSQL mất 273 giây; Cassandra được chọn để chia việc đọc ghi ra nhiều node; bước tiếp theo là đo lợi thế này trên một cụm
- BR2, BR4, BR7 đọc Parquet: Spark ghi thẳng, `fact_event` nhỏ hơn bản PostgreSQL (kể cả index) khoảng 6.4 lần, DuckDB chạy trong API
- Đã cân nhắc và gác lại: Kafka (cần thêm broker), Spark Cassandra Connector (jar phải khớp phiên bản Spark, Scala), Delta Lake/Iceberg (ngoài phạm vi), Neo4j (bảng cặp của BR7 chỉ có 314 dòng)

Số liệu: docs/evidence/report_engine_compare.txt (Q1 ở mục 3, dung lượng ở mục 2); docs/evidence/batch_timings.txt. Chi
tiết: REPORT.md §4.5. Tiêu đề: "nhanh ngang Cassandra" là REPORT.md §4.5 dòng 670; "mẫu 7%" là dòng 649; "freshness đến từ luồng tính trước, không từ engine" là đoạn cuối mục 4.5.3 của báo cáo nộp (Google Doc của Khang): tính
sẵn trên luồng và đặt bảng tính sẵn ở Cassandra là hai quyết định riêng, và một luồng Spark upsert vào PostgreSQL nhiều
khả năng cũng cập nhật kịp và nhanh như vậy; REPORT.md dòng 670 còn cách viết cũ. Ý chính 1: report_engine_compare.txt
dòng 40-44 (mục 3, Q1, p50: PostgreSQL 2.0, DuckDB 12.1, Cassandra 2.2 ms; Cassandra đọc `gmv_by_minute`, 1 partition,
120 dòng; PostgreSQL và DuckDB trả cùng 120 dòng); bảng "Cùng một câu hỏi, ba cách trả lời" ở REPORT.md dòng 662-668;
đo trên máy của Khang ngày 8/11, `main` tại f690021, 3 lần khởi động + 20 lần đo (report_engine_compare.txt dòng 6-12;
REPORT.md dòng 736). Ý chính 2: "5 giây" là `TRIGGER = "5 seconds"` ở processing/streaming_gold.py dòng 103 và
REPORT.md dòng 655; "273 giây" là batch_warehouse.py ở docs/evidence/batch_timings.txt dòng 27 (gồm chín bảng và bước
nạp PostgreSQL, REPORT.md dòng 645); "Cassandra được chọn để chia việc đọc ghi ra nhiều node; bước tiếp theo là đo lợi
thế này trên một cụm" là cùng đoạn mục 4.5.3 của Google Doc (mở rộng việc ghi và đọc theo khoá phân vùng trên nhiều
node [10], điều đồ án chưa kiểm chứng được với một node). Ý chính 3: REPORT.md §4.5 dòng 672 (ba lý do không nằm ở tốc độ); "khoảng 6.4 lần" là
(459.7 + 309.6) / 119.4 = 6.44, tức `fact_event` ở Parquet so với bảng cộng index ở PostgreSQL; chỉ so bảng thì 459.7 /
119.4 = 3.85 lần (report_engine_compare.txt dòng 29, mục 2; REPORT.md dòng 742); ba màn hình đọc Parquet là các dòng
"Parquet via DuckDB" ở gate2b_screens.txt dòng 41, 43, 46. Ý chính 4: REPORT.md §4.5 "Bốn phương án không đo", dòng
676-680: jar phải khớp phiên bản Spark và Scala ở dòng 678, Delta Lake/Iceberg nằm ngoài các công nghệ nhóm được dùng
ở dòng 679, bảng cặp của BR7 chỉ có 314 dòng ở dòng 680 (hàng BR7 của bảng chín hàng, REPORT.md dòng 848); "cần thêm
broker" thì REPORT.md không viết, dòng 677 nêu lý do khác (thư mục tệp cho phát lại y hệt, phép đối chiếu ở mục 6.1
cần điều đó). Lời thoại: "khoảng hai mili giây" là PostgreSQL p50 2.0 ms (report_engine_compare.txt dòng 41); "nhanh
ngang Cassandra" là Cassandra p50 2.2 ms (dòng 43) và REPORT.md dòng 670; "ở cỡ dữ liệu này" là mẫu 7% (dòng 649); "số
của phút vừa xong hiện ra ngay" là REPORT.md dòng 670 (kho dữ liệu dựng theo lô nên chưa có phút vừa xảy ra, còn luồng
ghi sau mỗi micro-batch); "chia được việc đọc ghi ra nhiều node theo partition key" và "lợi thế này phải chạy cả một
cụm mới đo được" là đoạn cuối mục 4.5.3 của Google Doc; "ba
màn hình báo cáo" là BR2, BR4, BR7 (REPORT.md dòng 672); hai lý do chọn Parquet trong lời thoại là lý do thứ nhất
("Spark ghi Parquet trực tiếp") và lý do thứ ba ("DuckDB chạy ngay trong tiến trình của API, không cần một máy chủ cơ sở
dữ liệu") ở dòng 672.

**Lời thoại:**
Nhóm đo hai phương án thay thế trên cùng star schema: PostgreSQL, và DuckDB đọc Parquet. Với câu hỏi doanh thu từng
phút, PostgreSQL mất khoảng hai mili giây, nhanh ngang Cassandra. Vậy ở cỡ dữ liệu này, tính trước trên luồng không
làm câu trả lời nhanh hơn; thứ nó mang lại là freshness, tức dữ liệu trên màn hình mới tới đâu: số của phút vừa xong
hiện ra ngay. Nhóm chọn Cassandra vì nó chia được việc đọc ghi ra nhiều node theo partition key; lợi thế này phải chạy
cả một cụm mới đo được. Ba màn hình báo cáo đọc Parquet, vì Spark ghi thẳng ra Parquet, và DuckDB không cần máy chủ
riêng.

**Số âm tiết:** 134

---

## Trang 14 · BR6 · Nguy cơ hết hàng · Tín

Nguồn gợi ý: docs/BR_SCOPE.md BR6; ảnh docs/evidence/gate2b_br6.png (T14); thao tác demo theo kịch bản T16.

**Tiêu đề:** BR6: sản phẩm sắp hết hàng ở từng kho, tính theo lô rồi ghi Cassandra, gấp nhất nằm đầu partition

**Ý chính (tối đa 4):**
- Vận hành hỏi: sản phẩm nào sắp hết hàng, ở kho nào?
- `batch_warehouse.py`: ngày còn hàng = tồn (giả lập) / tốc độ bán TB 7 ngày; `batch_gold.py` lấy ngày cuối, 30/11
- Cassandra `stockout_risk`, partition key `(warehouse_id)`, xếp theo `days_to_stockout`; xoá cả partition rồi ghi lại
- Mỗi kho 100 dòng gấp nhất + ≤5 dòng không bán trong 7 ngày (9999); đỏ dưới 3 ngày; footer 5 partition, p50 14.9 ms (API)

Số liệu: docs/evidence/gate2b_screens.txt (dòng BR6), br6_br8_fix_20261114.txt, gate2b_br6.png; REPORT.md §2.6, §3.4, §4.2,
§5.2; docs/BR_SCOPE.md BR6. Chú thích ảnh trên slide: "Ảnh 14/11/2026, một lần tải; số đo: gate2b_screens.txt,
br6_br8_fix_20261114.txt".
Tiêu đề và Ý chính 1: câu hỏi là cột "Câu hỏi nghiệp vụ" ở dòng BR6 của docs/BR_SCOPE.md (dòng 14) và bảng mục 2 của
REPORT.md (dòng 70); "tính theo lô rồi ghi Cassandra" là REPORT.md mục 2 dòng 74 và §4.5 dòng 674; "gấp nhất nằm đầu
partition" là khoá sắp xếp `days_to_stockout` (serving/cassandra_schema.cql dòng 45, chiều tăng mặc định) và docstring
serving/api/routers/br6.py dòng 39-40. Ý chính 2: `days_to_stockout` = `stock_on_hand` / `velocity_7d`, với
`velocity_7d` = tổng lượng bán 7 ngày / 7, được tính khi dựng `fact_inventory_daily` ở processing/batch_warehouse.py
dòng 513-531 (lượng bán là lượt mua của silver, dòng 484-500); `run_br6` trong processing/batch_gold.py lấy
`snapshot_date` lớn nhất của mỗi kho (dòng 328-330) và thay NULL bằng 9999.0 (dòng 335); ngày cuối là 30/11:
`LAST_SNAP` ở batch_warehouse.py dòng 479, đo lại bằng DuckDB trên data/warehouse/fact_inventory_daily (max
`snapshot_date` = 2019-11-30, 30 ngày); tồn kho giả lập nhưng lượng bán là lượt mua thật: REPORT.md §3.4 (dòng
196-206). Ý chính 3: khoá ở serving/cassandra_schema.cql dòng 39-46; xoá cả partition rồi ghi lại ở batch_gold.py dòng
352 và 364, REPORT.md §4.2 dòng 342. Ý chính 4: 100 và 5 là `_LIMIT_PER_WAREHOUSE` (dòng 69) và
`_NO_SALES_PER_WAREHOUSE` (dòng 71) trong serving/api/routers/br6.py; 9999 nghĩa là không bán trong 7 ngày: REPORT.md
§2.6 dòng 108; "đỏ dưới 3 ngày" là `CRITICAL_DAYS = 3` ở web/src/pages/BR6Page.tsx dòng 15; "5 partition" và "p50 14.9
ms" là cột partitions và meta_p50 của dòng BR6 trong gate2b_screens.txt (dòng 45). Lời thoại: "số ngày còn hàng bằng
tồn kho giả lập chia cho lượng bán trung bình bảy ngày" là `days_to_stockout` = `stock_on_hand` / `velocity_7d`,
REPORT.md §2.6 dòng 108 (code: batch_warehouse.py dòng 521); "ngày ba mươi tháng mười một" là ngày cuối 30/11 ở Ý
chính 2; "năm trăm sáu mươi sáu cặp sản phẩm và kho còn hàng dưới ba ngày" là `critical` = 566 của
`GET /api/br6/summary`, khớp tổng cqlsh `days_to_stockout < 3` trên năm kho (br6_br8_fix_20261114.txt dòng 10-11);
"danh sách chỉ cần đọc những dòng gấp nhất" là khoá sắp xếp `days_to_stockout` và `_LIMIT_PER_WAREHOUSE` (Ý chính 3
và 4); "thẻ số thì đếm trên toàn bảng, bằng một lượt gọi API riêng" là `GET /api/br6/summary`, thêm ngày 14/11
(br6_br8_fix_20261114.txt dòng 5; serving/api/routers/br6.py dòng 21 và 207-208; web/src/pages/BR6Page.tsx dòng 46 và
91), `total` = 63,655 (dòng 10); "khi cache đã nóng, mỗi lượt gọi thường mất dưới năm mươi mili giây" là curl p95 của
20 lần đo sau 3 lần làm nóng: 44.7 ms cho summary, 21.4 ms cho danh sách (br6_br8_fix_20261114.txt dòng 21-22). Ảnh
trên slide (chú thích "một lần tải") là logs/slide_shots_v25/br6.png, chụp 14/11 sau bản sửa thẻ số
(br6_br8_fix_20261114.txt mục 4, dòng 28-29), footer 51.67 ms, 5 partitions, 525 rows: đó là "khoảng năm mươi hai mili
giây" của lời thoại; ảnh của báo cáo, gate2b_br6.png, ghi 28.77 ms (REPORT.md §5.2 dòng 792).

**Lời thoại:**
Vận hành hỏi: sản phẩm nào sắp hết hàng, ở kho nào? Số ngày còn hàng bằng tồn kho giả lập chia cho lượng bán trung
bình bảy ngày. Ngày ba mươi tháng mười một có năm trăm sáu mươi sáu cặp sản phẩm và kho còn hàng dưới ba ngày. Mỗi kho
là một partition, xếp sẵn theo số ngày còn hàng, nên danh sách chỉ cần đọc những dòng gấp nhất. Còn thẻ số thì đếm
trên toàn bảng, bằng một lượt gọi API riêng. Khi cache đã nóng, mỗi lượt gọi thường mất dưới năm mươi mili giây. Ảnh
chụp một lần tải: chân màn hình ghi khoảng năm mươi hai mili giây, vẫn rất xa ngưỡng hai giây.

**Số âm tiết:** 129

---

## Trang 15 · BR8 · Tài khoản đặt đơn bất thường · Tín

Nguồn gợi ý: docs/BR_SCOPE.md BR8; ảnh docs/evidence/gate2b_br8.png (T14); thao tác demo theo kịch bản T16.

**Tiêu đề:** BR8: đếm đơn của từng tài khoản trong mỗi cửa sổ 5 phút ngay trên luồng, gắn mức low, medium, high

**Ý chính (tối đa 4):**
- Vận hành hỏi: tài khoản nào đặt đơn bất thường?
- Structured Streaming đếm lượt mua mỗi tài khoản, cửa sổ 5 phút không chồng nhau: 1 đơn `low`, 2–3 `medium`, ≥4 `high`
- Cassandra `order_velocity_alerts`, partition key `(event_date)`, cửa sổ mới nhất nằm đầu; upsert, không cần xoá
- Làm mới mỗi 10 giây; mở cảnh báo ra tổng cửa sổ 5 phút, không phải từng đơn; footer 1 partition, p50 19.8 ms (API)

Số liệu: docs/evidence/gate2b_screens.txt (dòng BR8), gate2b_br8.png; REPORT.md §2.8, §4.2, §5.2; docs/BR_SCOPE.md BR8;
docs/API_CONTRACT.md §10. Tiêu đề và Ý chính 1: câu hỏi ở dòng BR8 của docs/BR_SCOPE.md (dòng 16) và bảng mục 2 của
REPORT.md (dòng 72); đếm theo cửa sổ 5 phút trên luồng ở processing/streaming_gold.py dòng 495-507. Ý chính 2: chỉ đếm
lượt mua (`.where(is_purchase)`, dòng 499); cửa sổ 5 phút không chồng nhau (tumbling) `F.window("event_time", "5
minutes")` ở dòng 500-502; ngưỡng `MED_THRESHOLD = 2` và `HIGH_THRESHOLD = 4` ở dòng 442-443, gán mức ở dòng 470-475,
khớp bảng "Severity vocabulary" của docs/API_CONTRACT.md §10 (dòng 605-611). Ý chính 3: khoá `((event_date),
window_start, user_id)` với `window_start DESC` ở serving/cassandra_schema.cql dòng 49-57; upsert, không xoá:
docstring của `start_br8` (streaming_gold.py dòng 432-434) và REPORT.md §4.2 dòng 341. Ý chính 4: làm mới 10 giây là
`REFRESH_MS = 10_000` ở web/src/pages/BR8Page.tsx dòng 17 (dùng ở dòng 86); mở cảnh báo ra tổng của cửa sổ, vì bảng
không lưu từng đơn: docs/BR_SCOPE.md dòng 16, REPORT.md §2.8 dòng 120 và SYSTEM_DESIGN.md dòng 919; "1 partition" và
"p50 19.8 ms" là cột partitions và meta_p50 của dòng BR8 trong gate2b_screens.txt (dòng 47). Lời thoại: "dữ liệu không
có mã đơn, nên một đơn là một lượt mua một sản phẩm" là silver không có cột mã đơn hay số lượng
(docs/evidence/review_20261113/r5_br8_thresholds.txt mục 4, dòng 29); "cửa sổ năm phút cố định" là cửa sổ tumbling ở
streaming_gold.py dòng 500-502; ngưỡng một, hai tới ba, bốn trở lên là streaming_gold.py dòng 442-443; "mức low gồm
mọi lượt mua đơn lẻ" là low = đúng một đơn trong cửa sổ, 5,475 trên 5,815 cảnh báo của lượt phát lại 17/11 (94.2%)
(r5_br8_thresholds.txt dòng 11-14); "nên màn hình mặc định ẩn đi" là bản sửa ngày 14/11: BR8Page mặc định lọc "Medium
+ High", ẩn 5,475 cảnh báo low trong bảng, còn thẻ số vẫn đếm đủ (docs/evidence/br6_br8_fix_20261114.txt dòng 6 và 25);
"lọc mức high thì chỉ còn ba tài khoản" là high = 3 (r5_br8_thresholds.txt dòng 13, br6_br8_fix_20261114.txt dòng 25);
"người mua cùng một mẫu điện thoại bốn lần trong năm phút" là tài khoản 539257885 mua sản phẩm 1005116
(electronics.smartphone, apple) bốn lần từ 16:15:22 tới 16:19:39, trong cửa sổ 16:15 (r5_br8_thresholds.txt dòng
16-19); "khi cache đã nóng, cả lượt gọi API mất khoảng năm mươi mili giây" là curl p50 47.4 ms của dòng BR8 trong
gate2b_curl_raw.txt (Summary, dòng 23), sau 3 lần làm nóng, tức cả vòng HTTP trả 5,815 dòng của ngày 17/11. Ảnh trên
slide (chú thích "Ảnh chụp 14/11/2026, một lần tải") là logs/slide_shots_v25/br8.png, chụp với bộ lọc mặc định "Medium
+ High" (br6_br8_fix_20261114.txt mục 4, dòng 28-29), footer 21.94 ms, 1 partition, 5,815 rows; ảnh của báo cáo,
gate2b_br8.png, ghi 45.81 ms (REPORT.md §5.2 dòng 794).

**Lời thoại:**
Vận hành còn hỏi: tài khoản nào đặt đơn bất thường? Dữ liệu không có mã đơn, nên ở đây một đơn là một lượt mua một sản
phẩm. Spark đếm đơn của từng tài khoản trong cửa sổ năm phút cố định: một đơn là low, hai tới ba là medium, bốn trở
lên là high. Mức low gồm mọi lượt mua đơn lẻ, nên màn hình mặc định ẩn đi. Lọc mức high thì chỉ còn ba tài khoản,
trong đó có người mua cùng một mẫu điện thoại bốn lần trong năm phút. Khi cache đã nóng, cả lượt gọi API mất khoảng
năm mươi mili giây. Tiếp theo, bạn Đắt nói về doanh thu từng phút và phễu chuyển đổi.

**Số âm tiết:** 129

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
ảnh gate2b_br1.png. Lời thoại: "trong giờ cuối của lần phát lại, GMV đạt khoảng ba trăm lẻ chín nghìn, giảm sáu phẩy
sáu phần trăm so với giờ trước đó" là thẻ GMV 309K, giờ trước đó 330.7K, ngành hàng `all`, phút đầu bảng 21:29
(t09_t10_live_checks.txt dòng 18-19): (330.7 − 309) / 330.7 = 6.6%; "chưa tới mười mili giây" là curl max 6.5 ms của
BR1 trong gate2b_curl_raw.txt: thời gian gọi API, không phải thời gian vẽ màn hình (nếu T25 đặt số này lên slide thì
ghi là API).

**Lời thoại:**
Ban điều hành hỏi: GMV, tức tổng giá trị đơn hàng, từng phút ra sao, ngành hàng nào đang dẫn? Spark tính GMV ngay trên
luồng. Trong giờ cuối của lần phát lại, GMV đạt khoảng ba trăm lẻ chín nghìn, giảm sáu phẩy sáu phần trăm so với giờ
trước đó. Trong Cassandra, ngày và ngành hàng là partition key, phút mới nhất nằm đầu, nên mỗi lần làm mới màn hình
chỉ đọc một partition, chưa tới mười mili giây.

**Số âm tiết:** 95

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
bước); footer trên ảnh gate2b_br2.png. Lời thoại: "hơn tám mươi sáu phần trăm số phiên rời đi trước khi thêm vào giỏ"
là 1 − 131,498 / 966,143 = 86.4%, phiên thêm giỏ so với phiên xem, cả tháng, ngành hàng `all` (t09_t10_live_checks.txt
dòng 24-25); "ba mươi partition" và "khoảng hai mươi mili giây" là dòng BR2 của gate2b_curl_raw.txt (30 partition,
curl p50 19.8 ms).

**Lời thoại:**
Marketing hỏi: khách rời đi ở bước nào, xem, thêm giỏ hay mua? Phễu được tính trước từ fact session funnel, theo ngày
và ngành hàng. Cả tháng, hơn tám mươi sáu phần trăm số phiên rời đi trước khi thêm vào giỏ, vì vậy trang sản phẩm là
chỗ marketing cần xem lại trước tiên. Phễu cả tháng đọc ba mươi partition ngày bằng DuckDB; khi cache đã nóng, mất
khoảng hai mươi mili giây. Tiếp theo, bạn Nguyên nói về giỏ hàng bị bỏ quên và sản phẩm mua kèm.

**Số âm tiết:** 102

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
394; "phiên kết thúc sau ba mươi phút không có sự kiện" là chú thích ở dòng 390-393; "chiều tối ngày mười bảy có hai
nghìn sáu trăm giỏ như vậy" là 2,600 dòng của lượt phát lại 17/11, 15:00–21:30 (docs/evidence/gate2a_br5_run.txt dòng
51, khớp silver ở dòng 52-56); "tổng giá trị khoảng một phẩy bốn triệu" là tổng `cart_value` 1,411,565.93 (dòng 57);
"khoảng bốn mươi phút sau thao tác cuối, vì Spark chờ watermark mười phút để chỉ ghi những phiên chắc chắn đã đóng" là
gate2a_br5_run.txt dòng 40-41 (phiên chỉ đóng khi watermark, chậm 10 phút, vượt qua sự kiện cuối + 30 phút, tức
khoảng 40 phút thời gian sự kiện) và câu "BR5 báo giỏ sau khoảng 40 phút thay vì 30 phút" ở mục 6.3 của báo cáo nộp
(Google Doc); "đánh đổi nhóm em chủ động chọn" cùng cách nói với trang 24 và 25 ("độ trễ ... là đánh đổi có chủ
đích"); "cùng phiên thì ghi đè lên dòng cũ" là docstring dòng 342-344 và REPORT.md §4.2 dòng 344
("cùng một phiên luôn ghi đè cùng một dòng"); "không cần xoá, và giỏ tìm thấy ở các micro-batch trước vẫn còn nguyên"
là docstring dòng 344-347, REPORT.md §4.2 dòng 344 và cột "Xong khi" của BR5 ở BR_SCOPE.md dòng 13 ("tăng dần trong
ngày và không tự rỗng"). Ngoài ba mươi, bốn mươi và mười phút, hai nghìn sáu trăm giỏ và một phẩy bốn triệu, lời
thoại không có số liệu nào khác.

**Lời thoại:**
Marketing còn hỏi: khách nào bỏ quên giỏ hàng? Spark dùng session window, tức phiên kết thúc sau ba mươi phút không có
sự kiện. Phiên có thêm giỏ mà không mua là giỏ bỏ quên. Chiều tối ngày mười bảy có hai nghìn sáu trăm giỏ như vậy,
tổng giá trị khoảng một phẩy bốn triệu. Giỏ hiện ra khoảng bốn mươi phút sau thao tác cuối, vì Spark chờ watermark
mười phút để chỉ ghi những phiên chắc chắn đã đóng. Đó là đánh đổi nhóm em chủ động chọn. Giỏ được ghi vào Cassandra
kiểu upsert, tức cùng phiên thì ghi đè lên dòng cũ. Nhờ vậy không cần xoá, và giỏ tìm thấy ở các micro-batch trước vẫn
còn nguyên.

**Số âm tiết:** 135

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
phải thư mục ngày. 9.6 ms là QueryMeta.ms, đo quanh truy vấn DuckDB ở br7.py dòng 34-38. Lời thoại: "nhánh theo lô đếm
trước" là REPORT.md §2.7 dòng 116 (bảng cặp phải tính trước trên toàn tập dữ liệu); "lift, tức cặp đó được mua cùng
nhiều gấp mấy lần mức ngẫu nhiên" là định nghĩa ở REPORT.md §2.7 dòng 114 (số lần mua cùng so với số lần kỳ vọng nếu
mua độc lập); "xếp theo lift, kèm số phiên mua cùng" là br7.py dòng 60 và các cột Sessions together, Lift trên ảnh
gate2b_br7.png; "lift cao mà chỉ dựa trên vài phiên thì chưa chắc là quy luật" là REPORT.md §5.2 dòng 820 (1005230 có
lift 4.07 nhưng chỉ mua cùng trong 3 phiên, còn 1004249 mua cùng 26 phiên với lift 1.72, khớp ảnh). Lời thoại không có
số liệu nào.

**Lời thoại:**
Bên hàng hoá hỏi: khách mua một sản phẩm thì thường mua kèm gì? Nhánh theo lô đếm trước từng cặp sản phẩm được mua
trong cùng một phiên, rồi tính lift, tức cặp đó được mua cùng nhiều gấp mấy lần mức ngẫu nhiên. Màn hình xếp theo
lift, kèm số phiên mua cùng, vì lift cao mà chỉ dựa trên vài phiên thì chưa chắc là quy luật. Tiếp theo, bạn Khang nói
về sản phẩm đang được quan tâm và phân khúc khách hàng.

**Số âm tiết:** 87

---

## Trang 20 · BR3 · Sản phẩm đang được quan tâm · Khang

Nguồn gợi ý: docs/BR_SCOPE.md BR3; ảnh docs/evidence/gate2b_br3.png (T14); thao tác demo theo kịch bản T16.

**Tiêu đề:** BR3: top 20 sản phẩm được xem nhiều nhất, tính lại mỗi phút ngay trên luồng sự kiện

**Ý chính (tối đa 4):**
- Hàng hoá hỏi: sản phẩm nào được xem nhiều nhất trong 15 phút gần nhất?
- Spark Structured Streaming: cửa sổ 15 phút trượt mỗi phút, đếm lượt xem và thêm giỏ theo sản phẩm, lấy top 20
- Cassandra `trending_products`, khoá `(window_start, rank)`: một cửa sổ là một partition, đã xếp sẵn theo hạng
- Footer ghi 381 partition, 40 dòng: đọc khoá mọi cửa sổ để tìm cửa sổ mới nhất, rồi đọc nó và cửa sổ một phút trước

Số liệu: docs/evidence/gate2b_screens.txt (dòng BR3 và ghi chú BR3 ở "other calls"); REPORT.md §4.2 và §6.2. Ý 4: "381 partition, 40 dòng" là footer của ảnh gate2b_br3.png, giải thích ở ghi chú BR3 của gate2b_screens.txt: màn hình gọi hai lần nối tiếp (web/src/pages/BR3Page.tsx, fetchTrending). Lần gọi cửa sổ mới nhất báo 380 partition vì đếm cả danh sách khoá đọc bằng `SELECT DISTINCT window_start`, cộng 1 partition được đọc (serving/api/routers/br3.py). Lần gọi cửa sổ một phút trước đọc 1 partition. Lời thoại: "được xem nhiều nhất" và "bằng nhau thì xét lượt thêm giỏ" là thứ tự top 20 theo lượt xem rồi lượt thêm giỏ ở processing/streaming_gold.py, khớp dòng "Top 20 products by views" trên ảnh; BR3 không tính mức tăng, nên tên trang theo tên trong báo cáo nộp, "Sản phẩm đang được quan tâm"; "đọc khoá của mọi cửa sổ" là REPORT.md §4.2 ("API đọc danh sách khoá bằng SELECT DISTINCT window_start"); "một sản phẩm của Apple dẫn đầu với tám mươi lượt xem" là ô "Top product" và hạng 1 trên ảnh của slide, logs/slide_shots/br3.png: cửa sổ mới nhất 21:04–21:19 ngày 17/11, sản phẩm 1005115, apple, 80 lượt xem; "thường mất dưới mười mili giây khi cache đã nóng" là curl p50 7.9 ms, p95 9.5 ms của dòng BR3 ở gate2b_screens.txt dòng 42 (20 lần đo sau 3 lần làm nóng); "nên chia partition theo ngày" là hướng sửa, chưa làm. Ý 2, 3: processing/streaming_gold.py (cửa sổ 15 phút trượt 1 phút, top 20 theo lượt xem rồi lượt thêm giỏ) và serving/cassandra_schema.cql (`PRIMARY KEY (window_start, rank)`).

**Lời thoại:**
Hàng hoá còn hỏi: sản phẩm nào được xem nhiều nhất trong mười lăm phút gần nhất? Spark đếm lượt xem trong cửa sổ mười
lăm phút, trượt mỗi phút, rồi lấy top hai mươi; bằng nhau thì xét lượt thêm giỏ. Mỗi cửa sổ là một partition trong
Cassandra, đã xếp sẵn theo hạng. Trong cửa sổ đã đóng gần nhất, một sản phẩm của Apple dẫn đầu với tám mươi lượt xem.
Để tìm ra cửa sổ này, API phải đọc khoá của mọi cửa sổ. Trên lượt phát lại, việc này vẫn thường mất dưới mười mili
giây khi cache đã nóng; nếu chạy cả tháng thì nên chia partition theo ngày.

**Số âm tiết:** 126

---

## Trang 21 · BR4 · Phân khúc khách hàng theo RFM · Khang

Nguồn gợi ý: docs/BR_SCOPE.md BR4; ảnh docs/evidence/gate2b_br4.png (T14); thao tác demo theo kịch bản T16.

**Tiêu đề:** BR4: heatmap RFM 5×5 cho marketing biết nhóm khách nào nên đầu tư

**Ý chính (tối đa 4):**
- Marketing hỏi: phân khúc khách hàng nào nên được đầu tư quảng cáo?
- RFM: mỗi khách đã mua được chấm 1–5 theo độ gần (recency), tần suất (frequency) và giá trị (monetary)
- Lấy từ `dim_user` bản hiện hành (SCD loại 2, chấm lại mỗi tuần), ghi Parquet `rfm_segments`, đọc bằng DuckDB
- Heatmap theo recency × frequency; chọn một ô để xem danh sách khách trong ô

Số liệu: footer trên ảnh gate2b_br4.png (T14). Lời thoại: "sáu mươi mốt phẩy năm phần trăm" là 19,071 / 31,005 khách
đã mua chỉ mua một lần ở lần chấm 30/11 (docs/evidence/review_20261113/r1_rfm_ties.txt dòng 5); "điểm F chia khách
thành năm nhóm đông bằng nhau" là `ntile(5)`: f_score 1, 2 và 3 mỗi nhóm đủ 6,201 khách mua một lần, vì `ntile(5)` phá
hoà theo `user_id` (dòng 7); "bốn trăm sáu mươi tám người chỉ mua một lần vẫn lọt vào phân khúc champion" là 468 khách
mua một lần có f_score 4 và nằm trong champion (dòng 7 và 10); "khoảng bảy phần trăm phân khúc này" là 468 / 6,477 =
7.2% (dòng 10); "chấm F theo ngưỡng cố định sẽ sửa được chỗ này" là đề xuất của báo cáo nộp (Google Doc), nơi giới hạn
này được ghi ở mục 2.4, 6.3 và 7.2.

**Lời thoại:**
Marketing hỏi thêm: phân khúc khách hàng nào nên được đầu tư quảng cáo? Mỗi khách đã mua được chấm điểm theo lần mua
gần nhất, tần suất và số tiền chi. Màn hình vẽ hai tiêu chí đầu thành bảng năm nhân năm, đọc thẳng từ Parquet bằng
DuckDB. Khi tự đánh giá, nhóm em thấy trong số khách đã mua hàng, có sáu mươi mốt phẩy năm phần trăm chỉ mua một lần.
Vì điểm F chia khách thành năm nhóm đông bằng nhau, có bốn trăm sáu mươi tám người chỉ mua một lần vẫn lọt vào phân
khúc champion, chiếm khoảng bảy phần trăm phân khúc này. Chấm F theo ngưỡng cố định sẽ sửa được chỗ này.

**Số âm tiết:** 126

---

## Trang 22 · Đánh giá: tính đúng đắn · Khang

Nguồn gợi ý: docs/evidence/correctness_8br.txt (T19).

**Tiêu đề:** Cả 8 BR khớp 100% với đáp án viết độc lập, trên ngưỡng 99%

**Ý chính (tối đa 4):**
- Đáp án viết bằng SQL DuckDB trên silver (BR6: tồn kho), không dùng code Spark; so từng dòng với đúng bảng mà màn hình đọc
- 8/8 BR khớp 100% (BR luồng: lượt phát lại 17/11/2019, 15:00–21:30); thử cố ý làm sai: đặt watermark sớm 10 phút thì BR3 tụt còn 97.36%, BR5 còn 96.77%
- SCD2 sạch ở cả `dim_product` và `dim_user`: 0 khoảng chồng, 0 khoảng hở, đúng 1 dòng hiện hành mỗi khoá
- BR4: điểm và phân khúc khớp 100%; 3 số thô hiện kèm khớp 90.96%, vì với 23,353 khách, màn hình đang hiện số của một lần chấm điểm cũ hơn; hướng sửa: đọc từ `stg_rfm_snapshot`

Số liệu: docs/evidence/correctness_8br.txt (bảng 9 dòng T19 ngày 10/11/2026: 8 BR và SCD2; phép thử watermark sai; giới
hạn BR4). Bảng chín dòng ở correctness_8br.txt dòng 125-169 (hàng 1-8 là 8 BR, hàng 9 là SCD2); 90.96% là 234,977 /
258,330 dòng số thô RFM khớp, ở mục "Not one of the nine" (dòng 171-172). Ý 2: lần chạy đúng dùng `--watermark
"2019-11-17 21:19:59"` (dòng 45); "đặt watermark sớm 10 phút" là cùng lệnh với `--watermark "2019-11-17 21:09:59"`
(mục "The check can fail", dòng 73-74), BR3 97.36% và BR5 96.77%, cả hai "BELOW 99%" (dòng 75-76). Ý 4: mục "BR4's raw
values" (dòng 64-71): `rfm_segments` chiếu dòng `dim_user` hiện hành, và một phiên bản giữ số của lần chấm đã mở nó,
nên điểm và phân khúc khớp lần chấm 30/11 còn số thô có thể cũ hơn; 23,353 khách là số khách lệch ít nhất một trong ba
số so với `stg_rfm_snapshot` ngày 30/11 (= 258,330 − 234,977, dòng 68-70); "hướng sửa: đọc từ `stg_rfm_snapshot`" là
đọc thẳng bảng mà đáp án so, chưa làm (dòng 70-71 ghi giữ nguyên theo thiết kế). Lời thoại: "đặt watermark sớm mười
phút là BR ba và BR năm tụt dưới ngưỡng" là dòng 74-76; "chín mươi phẩy chín mươi sáu phần trăm" là 90.96%; "với một
phần khách" là 23,353 khách ở dòng 70.

**Lời thoại:**
Về tính đúng đắn, nhóm em viết lại đáp án cho tám câu hỏi bằng SQL thuần, không dùng lại code Spark, rồi so từng dòng
với đúng bảng mà màn hình đọc. Cả tám BR khớp một trăm phần trăm, trên ngưỡng chín mươi chín phần trăm. Nhóm em cũng
thử cố ý làm sai: chỉ cần đặt watermark sớm mười phút là BR ba và BR năm tụt dưới ngưỡng, tức là phép so thật sự bắt
được lỗi. Với BR bốn, điểm và phân khúc khớp hoàn toàn; còn ba số thô hiện kèm khớp chín mươi phẩy chín mươi sáu phần
trăm, vì với một phần khách, màn hình đang lấy giá trị của một lần chấm điểm cũ hơn. Hai dimension SCD Type hai cũng
sạch: không khoảng nào chồng hay hở, mỗi khoá có đúng một dòng hiện hành. Tiếp theo, bạn Tín trình bày hiệu năng, tính
hữu dụng và kết luận.

**Số âm tiết:** 173

---

## Trang 23 · Đánh giá: hiệu năng · Tín

Nguồn gợi ý: docs/evidence/perf_table.md, gate2b_screens.txt (T17), batch_timings.txt (T02), streaming_perf.txt (T14).

**Tiêu đề:** Cả 8 màn hình trả lời dưới 2 giây; p95 của màn hình chậm nhất thấp hơn ngưỡng khoảng 30 lần

**Ý chính (tối đa 4):**
- Mỗi màn hình: warm-up 3 lần rồi đo 20 lần; `meta` = API tự đo thời gian truy vấn, `curl` = trọn lượt HTTP; không tính thời gian React vẽ trang
- 8/8 dưới 2 s, một client gọi lần lượt: `meta` p95 cao nhất 40.0 ms (BR4); `curl` p95 cao nhất 63.9 ms (BR8)
- Luồng theo kịp nguồn phát lại 480.7 sự kiện/s, gấp 4.2 lần tốc độ thật của cả sàn trong cùng khung giờ; micro-batch mỗi 5 s, p50 587–852 ms
- Nhánh theo lô chạy từ CSV tới gold mất 426.5 s, chỉ chạy lại khi nguồn đổi; mọi số trên trang này đo trên một máy, với mẫu 7% khách

Số liệu: docs/evidence/gate2b_screens.txt, perf_table.md, streaming_perf.txt, batch_timings.txt, review_20261113/r1_raw_profile.txt
mục 4. Chi tiết: REPORT.md §6.2. Tiêu đề: "thấp
hơn ngưỡng khoảng 30 lần" là câu "thấp hơn ngưỡng 2 giây khoảng 30 lần" ở REPORT.md dòng 873 (§6.2), tức 2,000 / 63.9
ms, curl p95 của dòng BR8 ở gate2b_screens.txt dòng 47; Google Doc §6.2.1 viết y như vậy. "Cả 8" là cột under_2s = yes
ở gate2b_screens.txt dòng 40-47. Ý 1: 3 lần làm nóng + 20 lần đo và định nghĩa meta (QueryMeta.ms) / curl (time_total)
là dòng "method" (dòng 4-5) của gate2b_screens.txt; "không tính thời gian React vẽ trang" là câu "Thời gian vẽ của React
không được tính" ở REPORT.md dòng 860. Ý 2: "một client gọi lần lượt" là "20 timed calls one after another" ở dòng
method (dòng 4) và câu "khi một client gọi lần lượt" ở mục 7.3 của báo cáo nộp (mục 6.2.1 ghi thêm: chưa đo tải đồng
thời và thời gian tải trọn trang trong trình duyệt); meta p95 40.0 ms là dòng BR4 (dòng 43; lời gọi r=1, giá trị xấu
nhất trong năm lời gọi theo điểm R, khối "# BR4" cùng tệp); curl p95 63.9 ms là dòng BR8 (dòng 47). Ý 3: 480.7 là "offered rate 480.7
rows/s" của replayer ở streaming_perf.txt dòng 25 (Run 1); 587–852 ms là cột "trig p50" của bốn job ở dòng 28-31 (br5
587, br8 590, br1 616, br3 852); "gấp 4.2 lần tốc độ thật của cả sàn trong cùng khung giờ" là 480.7 / 114.1 = 4.21,
với 114.1 sự kiện/s là cả tệp gốc trong cùng khung 17/11 08:00–14:30 UTC (review_20261113/r1_raw_profile.txt mục 4,
dòng 49; xem trang 06); streaming_perf.txt dòng 19 vẫn ghi chưa thử quá tải ("no overload test was run"), dù slide
không còn nói điều này; chu kỳ 5 s là "trigger every 5 s" ở dòng 5. Ý 4: 426.5 s là dòng total (dòng 30) ở mục 1 của batch_timings.txt (3/11/2026, aa65472; lần chạy
này đọc cả tệp CSV 8.4G, xem dòng input của header); "chỉ chạy lại khi nguồn đổi" là REPORT.md dòng 880; "một máy" và
"mẫu 7% khách" là hai gạch đầu dòng đầu của REPORT.md §6.4 (dòng 909, 910). Lời thoại: "hai mươi lần sau ba lần làm
nóng" là dòng method của gate2b_screens.txt; "tính trọn lượt HTTP" là cột curl (time_total) ở dòng method; "gần sáu
mươi tư mili giây ở p chín mươi lăm" là curl p95 63.9 ms của BR8 (dòng 47); "mười chín trên hai mươi lần đo không chậm
hơn thế" là p95 theo nearest rank (gate2b_screens.txt dòng 5) trên 20 lần đo, tức giá trị thứ 19.

**Lời thoại:**
Về hiệu năng, mỗi màn hình được đo hai mươi lần sau ba lần warm-up, tức chạy thử trước cho cache nóng lên. Cả tám màn
hình đều dưới hai giây. Tính trọn lượt HTTP, chậm nhất là BR tám: gần sáu mươi tư mili giây ở p chín mươi lăm, tức
mười chín trên hai mươi lần đo không chậm hơn thế.

**Số âm tiết:** 70

---

## Trang 24 · Đánh giá: tính hữu dụng · Tín

Nguồn gợi ý: REPORT.md §6.3 và docs/EVALUATION_SURVEY.md. Khảo sát T18 chưa chạy, nên không có survey_responses.csv.

**Tiêu đề:** Cả 8 câu hỏi đều có màn hình trả lời cụ thể; xét kỹ hơn, nhóm tìm ra 4 điểm cần tinh chỉnh, mỗi điểm có hướng xử lý

**Ý chính (tối đa 4):**
- 8/8 câu hỏi của 4 nhóm người dùng đều có câu trả lời cụ thể trên dữ liệu thử nghiệm (báo cáo Bảng 18); BR1, BR2, BR3, BR7 trả lời trọn vẹn
- Đã sửa ngày 14/11: thẻ số BR6 từng chỉ đếm 525 dòng đang hiện, nay đếm cả 63,655 dòng; BR8 mặc định ẩn 5,475 cảnh báo low
- BR4: 468 khách mua một lần lọt vào phân khúc champion (7.2% phân khúc này), hướng sửa: chấm F theo ngưỡng cố định; BR5: giỏ hiện sau ~40 phút vì chờ watermark 10 phút, để chỉ ghi những phiên đã đóng
- Bước kiểm chứng tiếp theo: khảo sát 5 người, 4 tác vụ, ngưỡng đạt đã định sẵn (`EVALUATION_SURVEY.md`)

Số liệu: báo cáo mục 6.3 (Bảng 18), 6.2.3, 7.2; docs/evidence/br6_br8_fix_20261114.txt, gate2a_br5_run.txt,
review_20261113/r1_rfm_ties.txt; docs/EVALUATION_SURVEY.md. Chi tiết: mục 6.3 (Bảng 18), 6.2.3 và 7.2 của báo cáo nộp
(Google Doc của Khang); REPORT.md §6.3, §6.4. Tiêu đề và ý 1: "8/8 câu hỏi ... có câu trả lời cụ thể trên dữ liệu thử
nghiệm" là Bảng 18 ở mục 6.3 của báo cáo nộp, như dòng Nguồn của slide ghi; "4 điểm cần tinh chỉnh" là BR4, BR5, BR6
và BR8, bốn màn hình mà bản 24 của trang này (và mục 6.3, 7.3 của báo cáo nộp lúc đó) gọi là "mới trả lời một phần";
"BR1, BR2, BR3, BR7 trả lời trọn vẹn" là bốn màn hình còn lại. REPORT.md §6.3 (dòng 888-899) chưa có kết luận này. Ý 2:
"đã sửa ngày 14/11" là docs/evidence/br6_br8_fix_20261114.txt (dòng 1-6); 525 là số dòng danh sách BR6 trả, 5 kho ×
(100 dòng gấp nhất + 5 dòng không bán), theo `_LIMIT_PER_WAREHOUSE` và `_NO_SALES_PER_WAREHOUSE` ở
serving/api/routers/br6.py dòng 74 và 76, cột rows của dòng BR6 ở gate2b_curl_raw.txt dòng 21 và
br6_br8_fix_20261114.txt dòng 18; trước 14/11 bốn thẻ số chỉ đếm trên 525 dòng đó (báo cáo nộp mục 5.2); nay thẻ số
đọc `GET /api/br6/summary`, `total` = 63,655, khớp cqlsh (br6_br8_fix_20261114.txt dòng 10 và 14); 63,655 là cả bảng
`stockout_risk`, hàng BR6 của bảng chín dòng ở correctness_8br.txt (dòng 155) và review_20261113/r4_screen_counts.txt
dòng 38; "BR8 mặc định ẩn 5,475 cảnh báo low" là bộ lọc mặc định "Medium + High" (br6_br8_fix_20261114.txt dòng 6 và
25), tức 94.2% của 5,815 cảnh báo ngày 17/11 (r5_br8_thresholds.txt dòng 11-14). Ý 3: 468 là số khách mua một lần có
f_score 4 và nằm trong champion, 7.2% là 468 / 6,477 (docs/evidence/review_20261113/r1_rfm_ties.txt dòng 7 và 10);
"chấm F theo ngưỡng cố định" là đề xuất của báo cáo nộp (xem trang 21); "~40 phút vì chờ watermark 10 phút, để chỉ ghi
những phiên đã đóng" là gate2a_br5_run.txt dòng 40-41 (phiên chỉ đóng, và chỉ được ghi, khi watermark, chậm 10 phút,
vượt qua sự kiện cuối + 30 phút). Ý 4: 5 người, 4 tác vụ là docs/EVALUATION_SURVEY.md mục 2 (dòng 23-25); "ngưỡng đạt
đã định sẵn" là cột "Ngưỡng thành công (Target SLO)" ở mục 1 (dòng 12-14); khảo sát chưa chạy: không có tệp
docs/evidence/survey_responses.csv, và REPORT.md dòng 903 ghi chưa có điểm hài lòng hay tỉ lệ hoàn thành tác vụ nào.
Lời thoại: "bốn nhóm người dùng" là REPORT.md §1.2; "bốn điểm cần tinh chỉnh" là ý 2 và 3; "thẻ số của BR sáu đã được
sửa" và "BR tám nay mặc định ẩn mức low" là br6_br8_fix_20261114.txt dòng 5-6; "độ trễ của BR năm là đánh đổi có chủ
đích" là BR5 ở ý 3; "BR bốn đã có cách sửa" là chấm F theo ngưỡng cố định; "năm người dùng" là EVALUATION_SURVEY.md mục
2 ("5 bạn sinh viên/kỹ sư"); "các tác vụ và ngưỡng đạt đã định sẵn" là mục 2 và mục 1.

**Lời thoại:**
Về tính hữu dụng, câu hỏi nào của bốn nhóm người dùng cũng có một màn hình cho câu trả lời cụ thể. Nhóm em còn xét kỹ
hơn xem câu trả lời đã đủ về mặt nghiệp vụ chưa, và tìm ra bốn điểm cần tinh chỉnh. Thẻ số của BR sáu đã được sửa, BR
tám nay mặc định ẩn mức low, độ trễ của BR năm là đánh đổi có chủ đích, còn BR bốn đã có cách sửa. Bước tiếp theo là
khảo sát năm người dùng, với các tác vụ và ngưỡng đạt đã định sẵn.

**Số âm tiết:** 105

---

## Trang 25 · Kết luận, giới hạn và hướng phát triển · Tín

Nguồn gợi ý: REPORT.md §6.4 (T24).

**Tiêu đề:** Cả 8 BR đều chạy trọn từ nhật ký thô tới màn hình, khớp 100% với đáp án độc lập và trả lời dưới 2 giây

**Ý chính (tối đa 4):**
- Đúng đắn: 8/8 BR khớp 100% với đáp án độc lập, trừ 3 số thô hiện kèm của BR4 (khớp 90.96%); hiệu năng: chậm nhất 63.9 ms ở p95; hữu dụng: 8/8 câu hỏi có câu trả lời cụ thể
- Nhóm tự tìm ra 4 điểm cần tinh chỉnh: thẻ số BR6 đã được sửa, BR8 mặc định ẩn mức low (14/11); độ trễ do chờ watermark của BR5 là đánh đổi có chủ đích; BR4: hướng sửa là chấm F theo ngưỡng cố định
- Giới hạn: một máy, Cassandra một node, mẫu 7% khách, luồng phát lại; tồn kho và catalogue giả lập
- Hướng phát triển: Kafka thay thư mục tệp (phần đọc nguồn đã tách riêng ở `source.py`); cụm nhiều node, đủ 67.5 triệu sự kiện; khảo sát 5 người dùng

Số liệu: docs/evidence/correctness_8br.txt, gate2b_screens.txt, br6_br8_fix_20261114.txt; báo cáo mục 6.3, 7.2, 7.3.
Chi tiết: REPORT.md §6.4. Tiêu đề và ý 1: "chạy trọn từ nhật ký thô tới màn hình" là nhánh theo lô từ CSV tới gold
(batch_timings.txt mục 1, xem trang 23) và nhánh luồng từ tệp phát lại tới Cassandra (trang 08 và 11); 8/8 BR khớp
100% là bảng chín hàng của docs/evidence/correctness_8br.txt, mục "10 November 2026: the nine-row table (T19)" (dòng
125, các hàng ở dòng 150-158; REPORT.md §6.1); "trừ 3 số thô hiện kèm của BR4 (khớp 90.96%)" là dòng 171-172 cùng tệp
(234,977 / 258,330, dưới 99%; xem trang 22); "dưới 2 giây" là cột under_2s và 63.9 ms là curl p95 của dòng BR8,
gate2b_screens.txt dòng 47; "hữu dụng: 8/8 câu hỏi có câu trả lời cụ thể" là Bảng 18 ở mục 6.3 của báo cáo nộp (xem
trang 24). Ý 2: bốn điểm như trang 24 ý 2 và 3; thẻ số BR6 và bộ lọc mặc định của BR8 sửa ngày 14/11 ở
br6_br8_fix_20261114.txt dòng 1-6; mục 7.2 của báo cáo nộp theo dòng Nguồn. Ý 3: các gạch đầu dòng "Không có cụm máy
thật" (dòng 909, Spark local[*] và Cassandra một node), "Tập làm việc là mẫu 7% khách" (dòng 910), "Luồng thời gian
thực là luồng phát lại" (dòng 911), "Tồn kho và thuộc tính sản phẩm là dữ liệu giả lập" (dòng 916) của REPORT.md §6.4.
Ý 4: hướng phát triển 1 và 2 ở REPORT.md dòng 922 và 923; 67.5 triệu là 67,501,979 sự kiện (REPORT.md dòng 46, bảng
nguồn số liệu của mục 1); "khảo sát 5 người dùng" là docs/EVALUATION_SURVEY.md mục 2 (xem trang 24). Lời thoại: "chạy
trọn từ nhật ký thô tới màn hình" như tiêu đề; "khớp với một đáp án viết độc lập" là checks/correctness_8br.py
(REPORT.md §6.1); "màn hình nào cũng trả lời dưới hai giây" là cột under_2s ở gate2b_screens.txt dòng 40-47; "một máy"
là REPORT.md dòng 909; "bảy phần trăm khách" là dòng 910; "luồng phát lại" là dòng 911; Kafka là dòng 922 (REPORT.md
dòng 677: "Kafka là lựa chọn của một hệ thống thật"); "chạy đủ dữ liệu trên nhiều máy" là dòng 923 (cụm Spark và
Cassandra nhiều node). Trong báo cáo nộp (Google Doc), giới hạn, hướng phát triển và kết luận nằm ở mục 7 (kết luận
là mục 7.3), không phải §6.4.

**Lời thoại:**
Tóm lại, cả tám BR đều chạy trọn từ nhật ký thô tới màn hình, khớp với một đáp án viết độc lập, và màn hình nào cũng
trả lời dưới hai giây. Các số này đo trên một máy, với mẫu bảy phần trăm khách và luồng phát lại. Bước tiếp theo là
thay thư mục tệp bằng Kafka, một hệ thống truyền sự kiện, rồi chạy đủ dữ liệu trên nhiều máy. Phần trình bày của nhóm
em tới đây là hết, em cảm ơn cô và các bạn đã lắng nghe.

**Số âm tiết:** 96

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
- [6] R. Kimball, M. Ross, The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling, 3rd ed., Wiley, 2013
- [7] Apache Software Foundation, Apache Parquet: File format, parquet.apache.org/docs/file-format/
- [8] PostgreSQL Global Development Group, PostgreSQL 16 Documentation, Sec. 5.11, Ch. 11, postgresql.org/docs/16/
- [9] M. Raasveldt, H. Mühleisen, DuckDB: An embeddable analytical database, ACM SIGMOD, 2019
- [10] A. Lakshman, P. Malik, Cassandra: A decentralized structured storage system, ACM SIGOPS OSR, 2010
- [11] M. Kleppmann, Designing Data-Intensive Applications, O'Reilly Media, 2017
- [12] M. Zaharia et al., Apache Spark: A unified engine for big data processing, Communications of the ACM, 2016
- [13] M. Armbrust et al., Structured Streaming: A declarative API for real-time applications..., ACM SIGMOD, 2018
- [14] Apache Software Foundation, Structured Streaming Programming Guide: Handling late data and watermarking, spark.apache.org/docs/latest/
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
