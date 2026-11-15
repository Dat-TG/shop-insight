# Tóm tắt việc sử dụng AI — Nhóm 15

File này tóm tắt [`docs/AI_USAGE.md`](AI_USAGE.md), nhật ký đầy đủ của 50 phiên làm việc có dùng AI
(14/9 – 15/11/2026). Nhật ký gốc bằng tiếng Anh và chỉ được ghi thêm, không sửa phiên cũ, nên đó là bản có
giá trị khi cần đối chiếu. Mỗi ý dưới đây ghi kèm số phiên (S…) để tra lại.

**Công cụ:** Claude Code của Anthropic, model Claude Opus 5 (S1–S7), sau đó là Claude Opus 5.5 (S8–S50).

**Phạm vi của nhật ký:** nhật ký ghi những gì xảy ra trong các phiên Claude Code. Nhóm còn trao đổi, phân công và
chốt nhiều quyết định qua kênh chat của nhóm và trên Google Sheets theo dõi task. Những trao đổi đó không nằm trong
nhật ký, nên nhật ký chỉ cho thấy một phần công việc của các thành viên.

## 1. Quy định môn học và cách nhóm khai báo

Đề cương CO5173 (mục 5.4) cho phép dùng AI để hỗ trợ, cấm nộp sản phẩm do AI tạo toàn bộ hoặc phần lớn, và yêu
cầu ghi rõ công cụ cùng cách dùng. Nhóm khai báo theo ba cách:

- Nhật ký `docs/AI_USAGE.md` có từ buổi đầu tiên (S1, 14/9), công khai trong repo và được README dẫn tới. Mỗi
  phiên ghi bốn phần: AI tạo ra gì, kiểm tra bằng cách nào, AI sai ở đâu và được sửa ra sao, quyết định nào
  do thành viên đưa ra.
- Báo cáo nhắc tới việc dùng Claude Code và dẫn tới nhật ký ở Phụ lục A.1. Câu đó viết ngắn. Mức độ tham gia của
  AI trong từng phần nằm ở nhật ký và ở mục 2 dưới đây.

## 2. Phân vai giữa thành viên và AI

| Thành viên | AI |
|---|---|
| Chốt domain, 8 câu hỏi nghiệp vụ, kiến trúc bronze → silver → star schema → gold và stack công nghệ | Khảo sát repo, đề xuất phương án và kế hoạch |
| Trả lời các câu hỏi thiết kế, duyệt kế hoạch trước khi AI viết | Soạn nháp code, tài liệu, các mục báo cáo và nội dung slide |
| Review PR, chạy lại trên máy mình, quyết định nhận hay bác bản nháp | Chạy lệnh đo và đối chiếu số liệu |
| Bắt lỗi AI và yêu cầu làm lại (mục 5) | Sửa theo yêu cầu, ghi lại lỗi đã mắc |
| Thuyết trình, quay video, trả lời câu hỏi | — |

Nhóm ghi thẳng mức độ AI tham gia:

- **Phần lớn bản nháp code, tài liệu, các mục báo cáo và nội dung slide do AI viết theo hướng dẫn của nhóm**, trong
  phiên của thành viên phụ trách: theo thiết kế, hợp đồng API, danh sách task và kế hoạch mà thành viên đã chốt.
  Bản nháp chỉ thành bài nộp sau khi thành viên duyệt kế hoạch, review, chạy lại và chấp nhận.
- **Từ S40, AI gõ các lệnh đo chính thức** (benchmark, thời gian từng màn hình, kiểm tra tính đúng). Đắt chọn cách
  làm này và duyệt toàn bộ output thô trước khi merge (S41). Quy ước ban đầu là thành viên tự chạy phép đo, và
  nhật ký ghi rõ chỗ đổi quy ước này.

## 3. Phần việc của từng thành viên

**Đắt** (BR1, BR2; nền tảng Spark, silver, warehouse, streaming)
- Đưa ra hầu hết quyết định thiết kế ở mục 4: luật làm sạch silver, đặc tả `fact_event`, `fact_session_funnel`,
  cách chạy streaming, ý nghĩa "so với kỳ trước" của BR1.
- Review và merge PR của cả nhóm: #9 (Tín), #17 và #19 (Khang), #23 (Tín), #26 (Nguyên), #36 (Khang), #39 (Nguyên),
  #50 (Khang) (S8, S17, S19, S22, S23, S32, S33, S45).
- Chọn quy trình đo đạc (S40), duyệt toàn bộ output thô của phép đo trước khi merge (S41).
- Chốt cấu trúc deck và thứ tự người nói, chốt slide và cách giao code cho giảng viên (S29, S30, S48, S49).

**Khang** (BR3, BR4; báo cáo)
- Tự lập kế hoạch phần việc của mình bằng GitHub spec-kit, tự review mọi thay đổi và tự chạy mọi lệnh git (S16).
- Quyết định thiết kế RFM: snapshot theo tuần, `dim_user` SCD2 theo thiết kế 5.4, điểm F bằng `ntile(5)`; bác bản
  chấm F theo ngưỡng của AI (S16).
- Chọn cách BR3 tìm cửa sổ mới nhất mà không đổi schema hay hợp đồng API (S19).
- Viết `gen_inventory.py` và đặt câu hỏi cho bản sửa của AI, bản đó được làm lại (S8, S16).
- Chạy kiểm tra tính đúng trên máy mình (S31). Chủ trì báo cáo nộp: Google Doc của Khang là bản viết lại có cấu
  trúc riêng, không phải bản chuyển từ `docs/REPORT.md`.

**Nguyên** (BR5, BR7)
- BR5 làm trọn ba lớp và đẩy lên PR #26. Nhật ký ghi: "Nguyen's code is as Nguyen pushed it" (S22).
- Kiểm tra ground truth (T13) và cách sắp xếp BR7 theo lift trước, là thay đổi của Nguyên (PR #39, S33).
- Tự chỉnh các trang 05–07 của deck trên bản PDF, được đưa vào deck bản 20 (13/11).

**Tín** (BR6, BR8; khung ứng dụng)
- Đẩy khung ứng dụng, hợp đồng API cố định với 8 bộ fixture, DDL Postgres và ba dimension nhỏ (PR #9, S8).
- BR6, BR8 và bước 6 của warehouse (PR #23). Nhật ký ghi: phần truy vấn, endpoint và màn hình "is as Tin pushed
  it" (S23).
- Tự chỉnh lời thoại các trang của mình trong deck (commit `fb02c88`, 14/11).

## 4. Các quyết định thiết kế do thành viên đưa ra

**Kiến trúc và dữ liệu**
- Chọn lịch làm việc: giữ khung 2–4 giờ mỗi tuần và để các gate linh hoạt, giữa hai phương án AI đã tính đầy đủ
  (S1).
- Giữ 25.859 sự kiện của ngày 1/12 theo giờ Việt Nam, nên silver có 31 thư mục ngày. Thêm luật làm sạch thứ 7
  (bỏ dòng có `user_session` null) ngay ở silver (S6, Đắt).
- Ghim image Docker tới bản patch (`cassandra:4.1.12`, `postgres:16.15`) (S7, Đắt).
- Đưa BR2, BR4, BR6 về đúng hợp đồng API đã chốt, không mở rộng hợp đồng (S8, Đắt).
- Đặc tả `fact_event`: công thức `event_sk`, cách xử lý dòng trùng, danh sách kiểm tra (S10, Đắt).
- `fact_session_funnel` giữ lag có dấu, không ép về 0 (S18, Đắt).
- BR2 đếm theo phiên và thêm các cột `*_events`. Bảng theo ngành dựng từ endpoint có sẵn, không đổi hợp đồng (S21,
  Đắt).
- RFM chụp snapshot theo tuần, `dim_user` làm SCD2, điểm F dùng `ntile(5)` (S16, Khang).

**Streaming**
- Replayer dùng Spark và `toLocalIterator`. BR1 chạy update mode với trigger 5 giây. Timestamp trong Cassandra
  theo giờ Việt Nam (S12, Đắt).
- "So với kỳ trước" là 60 phút gần nhất so với 60 phút trước đó, nên API đọc tối đa 120 dòng (S13, Đắt).
- `--fresh` làm rỗng cả các bảng streaming, Ctrl-C dừng giữa hai micro-batch (S14, Đắt).
- BR3 tìm cửa sổ mới nhất bằng cách liệt kê partition key, không đổi schema (S19, Khang).

**Nộp bài**
- Hướng dẫn chạy (`docs/RUN_GUIDE_VI.md`) cho giảng viên lấy code qua link GitHub, tag `submission-2026-11-15`.
  Không gửi kèm dữ liệu dựng sẵn (S48, Đắt).

## 5. Những lần thành viên bắt lỗi hoặc bác bỏ AI

- **S2:** con số ngân sách giờ mà S1 kế thừa bị sai. Phiên này sửa lại và dựng lại tracker.
- **S11:** cách AI cập nhật tracker làm mất định dạng Google Sheets. Đắt khôi phục từ lịch sử phiên bản và đổi
  sang sửa trực tiếp qua connector.
- **S12:** Đắt yêu cầu test lại trên Cassandra thật trước khi commit.
- **S16:** AI tự chấm điểm F theo ngưỡng giá trị, lệch khỏi tracker mà không hỏi. Khang yêu cầu trở lại
  `ntile(5)`. Khang cũng hỏi lại bản sửa `gen_inventory.py` và bản đó được làm lại.
- **S19:** Đắt review PR #19 và phát hiện câu mô tả 612 sản phẩm sai ở bốn chỗ (code đúng, câu chữ sai).
- **S45:** Đắt review PR #50 và phát hiện thứ tự chạy ở mục 5.1 sai: trên máy mới, quy trình dừng ở bước nạp
  Postgres.
- **S48:** Đắt yêu cầu hướng dẫn chạy dùng link GitHub thay cho file zip mà AI đề xuất ban đầu.

Nhóm không đưa vào báo cáo con số nào chưa đo được. Ví dụ, báo cáo ghi rõ là chưa có kết quả khảo sát người dùng,
không ước lượng (S46).

## 6. Quy trình làm việc với AI

- Phần lớn các phiên từ S8 bắt đầu ở *plan mode*. AI khảo sát repo và đề xuất kế hoạch, thành viên trả lời các
  câu hỏi thiết kế và duyệt kế hoạch, sau đó AI mới viết.
- Code SQL/Spark do AI viết chỉ được commit sau khi đã chạy thật (quy ước từ S1).
- Mỗi con số đưa vào báo cáo kèm câu lệnh tạo ra nó. Các lệnh đo nằm trong `docs/evidence/` và
  `benchmark/results/`, ai cũng chạy lại được.
- Hook trong `.claude/hooks/` chặn AI xoá dữ liệu dưới `data/`, commit thẳng lên `main` hay force-push, và cảnh
  báo khi code rơi vào các lỗi Spark đã biết (S3).
- Mỗi phiên có một mục "AI sai ở đâu". Tổng cộng nhật ký ghi khoảng 200 lỗi AI đã mắc và được sửa.

## 7. Những điểm nhóm ghi nhận thẳng thắn

- Một số phiên không được ghi kịp thời và được bổ sung sau: S27 (hình và số liệu của bài thuyết trình indexing,
  23 và 26/10) và S49 (công việc ngày 14/11, ghi lại ngày 15/11 từ git và ghi chú phiên).
- Một số mục của nhật ký còn ghi "human review pending". Những mục đó chưa được thành viên phụ trách xác nhận
  trong nhật ký.
