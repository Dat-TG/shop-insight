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

## Phân công (theo T20)

| Người | Trang |
|---|---|
| Khang | 01, 02, 03, 04, 16 (BR3), 17 (BR4), 22 |
| Nguyên | 05, 06, 07, 11, 18 (BR5), 19 (BR7), 25, 26 |
| Đắt | 08, 09, 10, 12, 14 (BR1), 15 (BR2) |
| Tín | 13, 20 (BR6), 21 (BR8), 23, 24 |

Trang 14-21 mở đầu đoạn demo của từng BR. Lời thoại ở đó ngắn: câu hỏi nghiệp vụ và vì sao màn hình trả lời
được câu hỏi đó. Thao tác demo nằm trong kịch bản T16. Mục 5 xếp BR theo người làm (BR1, BR2 · BR3, BR4 ·
BR5, BR7 · BR6, BR8) để mỗi người demo liền một đoạn.

---

## Trang 01 · Trang bìa · Khang

Nguồn gợi ý: điền họ tên đầy đủ và MSSV của bốn bạn (trên slide đang để trống).

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

---

## Trang 02 · Nội dung và người trình bày · Khang

Nguồn gợi ý: slide đã có bảng 6 mục, người trình bày và số trang (theo phân công ở trên).

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

---

## Trang 03 · Bối cảnh · Khang

Nguồn gợi ý: REPORT.md §1.1 Bối cảnh, §1.3 Vì sao không truy vấn thẳng nhật ký thô.

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

---

## Trang 04 · Bốn nhóm người dùng · Khang

Nguồn gợi ý: REPORT.md §1.2 Các bên liên quan.

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

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

## Trang 11 · Cassandra: thiết kế khoá từ câu hỏi của màn hình · Nguyên

Nguồn gợi ý: REPORT.md §4.2, serving/cassandra_schema.cql.

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

---

## Trang 12 · Spark: một engine cho nhánh theo lô và nhánh thời gian thực · Đắt

Nguồn gợi ý: REPORT.md §4.3; docs/evidence/batch_timings.txt (T02).

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

## Trang 14 · BR1 · Doanh thu theo từng phút · Đắt

Nguồn gợi ý: docs/BR_SCOPE.md BR1; ảnh docs/evidence/gate2b_br1.png (T14); thao tác demo theo kịch bản T16.

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

---

## Trang 15 · BR2 · Phễu chuyển đổi · Đắt

Nguồn gợi ý: docs/BR_SCOPE.md BR2; ảnh docs/evidence/gate2b_br2.png (T14); thao tác demo theo kịch bản T16.

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

---

## Trang 16 · BR3 · Sản phẩm đang tăng mạnh · Khang

Nguồn gợi ý: docs/BR_SCOPE.md BR3; ảnh docs/evidence/gate2b_br3.png (T14); thao tác demo theo kịch bản T16.

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

---

## Trang 17 · BR4 · Phân khúc khách hàng theo RFM · Khang

Nguồn gợi ý: docs/BR_SCOPE.md BR4; ảnh docs/evidence/gate2b_br4.png (T14); thao tác demo theo kịch bản T16.

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

## Trang 20 · BR6 · Nguy cơ hết hàng · Tín

Nguồn gợi ý: docs/BR_SCOPE.md BR6; ảnh docs/evidence/gate2b_br6.png (T14); thao tác demo theo kịch bản T16.

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

---

## Trang 21 · BR8 · Tài khoản đặt đơn bất thường · Tín

Nguồn gợi ý: docs/BR_SCOPE.md BR8; ảnh docs/evidence/gate2b_br8.png (T14); thao tác demo theo kịch bản T16.

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

---

## Trang 22 · Đánh giá: tính đúng đắn · Khang

Nguồn gợi ý: docs/evidence/correctness_8br.txt (T19).

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

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

## Trang 25 · Kết luận, giới hạn và hướng phát triển · Nguyên

Nguồn gợi ý: REPORT.md §6.4 (T24).

**Tiêu đề:**

**Ý chính (tối đa 4):**
-

**Lời thoại:**

**Số âm tiết:**

---

## Trang 26 · Tài liệu tham khảo · Nguyên

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
