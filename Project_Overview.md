# Card Album Simulator - Project Overview

## 1. Mục đích dự án
**Card Album Simulator** là một ứng dụng giả lập (simulator) được xây dựng nhằm mục đích thử nghiệm, trực quan hóa và kiểm chứng các cơ chế gacha/mở thẻ bài cho tính năng **Card Album**. Ứng dụng giúp cho đội ngũ phát triển và thiết kế game (Game Designers) có thể mô phỏng tỉ lệ rơi thẻ, kiểm tra các logic liên quan đến bộ sưu tập và đánh giá tính cân bằng của hệ thống thông qua giao diện trực quan.

## 2. Tech Stack (Công nghệ sử dụng)
- **Ngôn ngữ:** Python 3.12+
- **Giao diện người dùng (UI):** [Streamlit](https://streamlit.io/) - Framework tạo web app nhanh chóng cho các dự án data/mô phỏng.
- **Xử lý dữ liệu:** Pandas.

## 3. Cấu trúc thư mục và các thành phần chính
Dự án được cấu trúc theo dạng module với thư mục chính là `card_album/`:

- **`main.py`**: Điểm neo (entry point) của dự án. File này được gọi để khởi chạy ứng dụng Streamlit.
- **`Card_Album_Specification.md`**: Tài liệu đặc tả kỹ thuật chi tiết. Chứa toàn bộ các dữ liệu, quy tắc, bảng tỉ lệ (probability tables), thiết lập tính năng, chỉ số và cấu hình liên quan đến tính năng Card Album (như sự kiện Card Rush, Buy 1 or All, các bộ thẻ/Card Sets).
- **`requirement.txt`**: File chứa danh sách các thư viện cần thiết (streamlit, pandas).

### Phân tích thư mục `card_album/`
- **`config.py`**: Nơi lưu trữ toàn bộ các cấu hình tĩnh của hệ thống. Bao gồm danh sách các gói thẻ (Bronze, Emerald, Silver, Amethyst, Ruby, Gold, Rainbow), độ hiếm (1-5 sao và thẻ Vàng), trọng số rớt thẻ (weights), kích thước gói thẻ trong các sự kiện (như Card Rush), và các thông số hiển thị giao diện.
- **`gacha.py`**: Chứa logic cốt lõi (core logic) của việc mô phỏng mở gói thẻ. Xử lý các nghiệp vụ như: tính toán kích thước gói thực tế (effective pack size), áp dụng cơ chế bảo hiểm (pity bonus), và xác định ngẫu nhiên độ hiếm của thẻ bài dựa trên trọng số đã cấu hình. Hỗ trợ mở đơn lẻ hoặc mở hàng loạt (bulk).
- **`state.py`**: Chịu trách nhiệm quản lý trạng thái hiện tại của người dùng (user session state). Theo dõi tiến độ thu thập thẻ (Album completion), số sao (stars) nhận được từ các thẻ trùng lặp (duplicates) và xử lý việc reset dữ liệu tiến trình.
- **`ui.py`**: Quản lý phần giao diện trực quan bằng Streamlit. Render dashboard hiển thị tình trạng bộ sưu tập, thanh điều hướng (sidebar) để chọn loại pack, các nút bấm để mở gói thẻ và bảng thống kê kết quả sau khi mở thẻ.

## 4. Cách vận hành
1. Hệ thống khởi tạo trạng thái (Album state) thông qua `state.py`.
2. Người dùng thao tác trên giao diện Streamlit (`ui.py`) để chọn gói thẻ muốn mở (dựa trên các loại gói định nghĩa ở `config.py`).
3. Giao diện gọi hàm mở gói thẻ từ `gacha.py`, truyền vào cấu hình tương ứng.
4. Logic gacha xử lý ngẫu nhiên để trả về danh sách các thẻ bài, đồng thời cập nhật lại tiến trình vào `state.py` (tính thẻ mới, thẻ trùng lặp).
5. Giao diện tự động cập nhật lại các chỉ số (Dashboard) để người dùng xem kết quả.
