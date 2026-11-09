# Kế hoạch & Phiếu khảo sát Đánh giá Trải nghiệm Người dùng (Effectiveness Evaluation)

> **Môn:** CO5173 Data Engineering — Đồ án ShopInsight (Nhóm 15)  
> **Người phụ trách:** Trịnh Trần Trung Tín (`chuntinne05`)  
> **Tuần thực hiện:** W43 chuẩn bị form — W44 tiến hành khảo sát  
> **Mục tiêu Rubric:** Tiêu chí **Effectiveness** (đo lường độ trễ thực tế < 2s và mức độ hài lòng của 5 người dùng đại diện 4 nhóm nghiệp vụ).

---

## 1. Mục tiêu và Thang đo (Evaluation Metrics)

Rubric Đồ án yêu cầu định nghĩa rõ metric, phương pháp đo và ngưỡng thành công (SLO):

| Metric | Phương pháp đo | Ngưỡng thành công (Target SLO) |
|---|---|---|
| **1. Tốc độ phản hồi (Latency)** | Người dùng thao tác, ghi nhận số ms hiển thị tại footer `QueryMeta` | **< 2,000 ms** trên mọi màn hình |
| **2. Độ mượt & phản hồi cảm nhận (Perceived Performance)** | Thang điểm Likert 1–5 (1: Rất chậm, 5: Tức thì) | Điểm trung bình **$\ge$ 4.0 / 5** |
| **3. Độ trực quan của thông tin (Usability & Clarity)** | Thang điểm Likert 1–5 (1: Rối mắt/Khó hiểu, 5: Rất rõ ràng) | Điểm trung bình **$\ge$ 4.2 / 5** |
| **4. Tỉ lệ hoàn thành tác vụ (Task Completion Rate)** | Người dùng thực hiện 4 tác vụ nghiệp vụ độc lập | **100% hoàn thành** không lỗi |

---

## 2. Kịch bản Khảo sát (4 Tác vụ đại diện 4 nhóm người dùng)

Người tham gia khảo sát (5 bạn sinh viên/kỹ sư) sẽ thực hiện lần lượt 4 kịch bản sau trên hệ thống ShopInsight:

### Tác vụ 1: Ban điều hành (Executive — BR1)
- **Mục tiêu:** Kiểm tra doanh thu GMV biến động theo thời gian thực.
- **Thao tác:** Mở tab **BR1**, lọc theo ngày demo (`2019-11-17`), quan sát biểu đồ GMV 60 phút tự làm mới mỗi 10 giây.
- **Câu hỏi xác thực:** Ngành hàng nào đang có doanh số cao nhất trong khung giờ hiện tại?

### Tác vụ 2: Marketing (Growth & Campaigns — BR2, BR4, BR5)
- **Mục tiêu:** Xác định phân khúc khách hàng chi tiêu cao và phiên giỏ hàng bị bỏ quên.
- **Thao tác:**
  1. Mở tab **BR4 (RFM)**: Chọn ô `Champions` (5-5) trên heatmap 5x5, xem danh sách khách hàng.
  2. Mở tab **BR5 (Abandoned Carts)**: Lọc các giỏ hàng có giá trị $> \$100$, bấm nút mô phỏng "Tạo chiến dịch email".
- **Câu hỏi xác thực:** Có bao nhiêu giỏ hàng bị bỏ quên có giá trị trên \$100?

### Tác vụ 3: Nhập hàng (Merchandising & Inventory — BR3, BR7)
- **Mục tiêu:** Tìm top sản phẩm tăng trưởng nóng và gợi ý mua kèm (Cross-sell).
- **Thao tác:**
  1. Mở tab **BR3**: Xem top 20 sản phẩm trending trong 15 phút.
  2. Mở tab **BR7**: Nhập mã sản phẩm `1005115`, xem danh sách 10 sản phẩm hay được mua kèm nhất.
- **Câu hỏi xác thực:** Sản phẩm nào có điểm tương đồng (lift) cao nhất với mã `1005115`?

### Tác vụ 4: Vận hành kho (Supply Chain & Fraud — BR6, BR8)
- **Mục tiêu:** Cảnh báo nguy cơ thiếu hàng và phát hiện tài khoản đặt đơn bất thường.
- **Thao tác:**
  1. Mở tab **BR6 (Stockout Risk)**: Lọc Kho 1, lọc ngưỡng $< 3$ ngày. Quan sát các dòng bị bôi đỏ cảnh báo khẩn cấp.
  2. Mở tab **BR8 (Order Velocity Alerts)**: Bấm vào một dòng cảnh báo để mở rộng, xem tổng của cửa sổ 5 phút đó: số đơn trong cửa sổ, tổng giá trị, giá trị trung bình mỗi đơn và mức độ cảnh báo.
- **Câu hỏi xác thực:**
  1. Có bao nhiêu SKU tại Kho 1 đang ở mức nguy hiểm dưới 3 ngày?
  2. Với cảnh báo bạn vừa mở rộng ở BR8: cửa sổ 5 phút đó có bao nhiêu đơn, và cảnh báo ở mức độ nào?

---

## 3. Mẫu Phiếu Khảo sát (Survey Questionnaire)

Người tham gia điền đánh giá theo các câu hỏi sau:

1. **Thời gian tải trang có nhanh và tức thì không?**  
   `[ ] 1 - Rất chậm (> 4s)` `[ ] 2 - Chậm (2-4s)` `[ ] 3 - Chấp nhận được (1-2s)` `[ ] 4 - Nhanh (< 1s)` `[ ] 5 - Rất nhanh (tức thì)`

2. **Footer `QueryMeta` có giúp bạn biết rõ câu truy vấn tốn bao nhiêu thời gian và đọc bao nhiêu dữ liệu không?**  
   `[ ] 1 - Hoàn toàn không` `[ ] 2 - Không rõ` `[ ] 3 - Bình thường` `[ ] 4 - Hữu ích` `[ ] 5 - Rất minh bạch và tin cậy`

3. **Màu sắc cảnh báo (Đỏ: khẩn cấp, Vàng: chú ý, Xanh: an toàn) trên BR6 và BR8 có nhất quán, dễ nhìn không?**  
   `[ ] 1 - Rất rối` `[ ] 2 - Hơi khó nhìn` `[ ] 3 - Bình thường` `[ ] 4 - Trực quan` `[ ] 5 - Rất chuyên nghiệp`

4. **Khi không có dữ liệu (Empty State), hệ thống có thông báo giải thích rõ ràng không?**  
   `[ ] 1 - Không (màn hình trắng)` `[ ] 2 - Kém` `[ ] 3 - Đủ hiểu` `[ ] 4 - Rõ ràng` `[ ] 5 - Rất tốt`

5. **Đánh giá chung về độ hữu ích của 8 màn hình trong việc ra quyết định kinh doanh:**  
   `[ ] 1 - Không hữu ích` `[ ] 2 - Ít hữu ích` `[ ] 3 - Tạm được` `[ ] 4 - Hữu ích` `[ ] 5 - Rất hữu ích`

---

> **Lưu ý:** Bảng kết quả thu thập khảo sát (Section 4) sẽ được điền sau khi thực hiện khảo sát thực tế trong W44.  
> Template: [Người tham gia | Vai trò | Latency (1-5) | QueryMeta (1-5) | Màu sắc & UI (1-5) | Chung (1-5) | Tác vụ hoàn thành | Góp ý]
