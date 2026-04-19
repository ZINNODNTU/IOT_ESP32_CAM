# BÁO CÁO MÔN HỌC

## Đề tài
**Hệ thống điểm danh khuôn mặt sử dụng ESP32-CAM và Python WebSocket (Tornado + OpenCV)**

---

## 1) Thông tin học phần
- **Học phần:** Công nghệ IoT và Ứng dụng  
- **Ngành:** Công nghệ Thông tin  
- **Sinh viên thực hiện:** ................................................  
- **MSSV:** ................................................  
- **Lớp:** ................................................  
- **Giảng viên hướng dẫn:** ................................................  
- **Thời gian thực hiện:** ................................................

---

## 2) Tóm tắt đề tài
Đề tài xây dựng hệ thống điểm danh tự động theo thời gian thực bằng nhận diện khuôn mặt. Thiết bị **ESP32-CAM** chụp khung hình JPEG và gửi liên tục qua **WebSocket** về máy chủ Python. Backend sử dụng **Tornado** để xử lý kết nối đồng thời, **OpenCV** để phát hiện và nhận diện khuôn mặt, sau đó ghi nhận kết quả điểm danh theo hai chế độ **CHECK_IN/CHECK_OUT** vào file CSV.

Hệ thống cung cấp:
- **Giao diện điểm danh** cho lớp học/phòng lab.
- **Giao diện quản trị** để đăng ký khuôn mặt mới, xem/xóa dữ liệu đăng ký và lịch sử điểm danh.
- **Cơ chế tránh điểm danh trùng** theo từng ngày, theo `person_id` và `mode`.

---

## 3) Mục tiêu và phạm vi

### 3.1 Mục tiêu
1. Xây dựng mô hình điểm danh khuôn mặt chi phí thấp, dễ triển khai bằng ESP32-CAM.
2. Đồng bộ luồng video và nhận diện theo thời gian thực qua mạng LAN/Internet.
3. Quản lý đăng ký khuôn mặt và lịch sử điểm danh qua giao diện web.
4. Đảm bảo dữ liệu điểm danh được lưu vết, dễ kiểm tra và xuất báo cáo.

### 3.2 Phạm vi
- Phát hiện khuôn mặt với Haar Cascade trong OpenCV.
- Nhận diện theo vector đặc trưng đơn giản (chuẩn hóa histogram + cosine similarity).
- Lưu trữ mức file hệ thống: thư mục ảnh + CSV.
- Chưa dùng CSDL quan hệ, chưa dùng mô hình deep learning chuyên sâu.

---

## 4) Cơ sở lý thuyết

### 4.1 Kiến trúc IoT áp dụng
Hệ thống gồm 3 lớp:
- **Lớp thiết bị biên (edge):** ESP32-CAM AI Thinker chụp ảnh và gửi frame.
- **Lớp truyền thông:** WiFi + WebSocket (`/ws`).
- **Lớp ứng dụng:** Python Tornado xử lý ảnh, API, giao diện web.

### 4.2 Quy trình nhận diện khuôn mặt
1. Nhận frame JPEG từ ESP32-CAM.
2. Xoay frame theo cấu hình camera (`0/90/180/270`).
3. Chuyển ảnh xám và phát hiện khuôn mặt bằng Haar Cascade.
4. Cắt ROI khuôn mặt lớn nhất (khi đăng ký) hoặc từng ROI (khi nhận diện).
5. Chuẩn hóa khuôn mặt: resize `128x128`, cân bằng histogram, flatten, L2 normalize.
6. So khớp với mẫu đã lưu bằng cosine similarity.
7. Nếu điểm < ngưỡng, gán `Unknown`.

### 4.3 Quy tắc điểm danh
Điểm danh chỉ được ghi khi đồng thời thỏa:
- Màn hình điểm danh đang mở (heartbeat hợp lệ).
- Người được nhận diện khác `Unknown`.
- Chế độ hợp lệ: `CHECK_IN` hoặc `CHECK_OUT`.
- Chưa tồn tại bản ghi trùng trong ngày với cùng `person_id` và `mode`.

---

## 5) Phân tích hệ thống hiện tại

### 5.1 Thành phần phần mềm/chương trình
- **Firmware ESP32-CAM:** `arduino/esp32cam_ws_stream/esp32cam_ws_stream.ino`
- **Backend server:** `python_backend/websockets_stream.py`
- **UI điểm danh:** `python_backend/templates/attendance.html`
- **UI quản trị đăng ký:** `python_backend/templates/admin_login.html`, `python_backend/templates/admin_register.html`

### 5.2 Dữ liệu lưu trữ
- `python_backend/known_faces/`: ảnh khuôn mặt đã đăng ký.
- `python_backend/face_registrations.csv`: nhật ký đăng ký khuôn mặt.
- `python_backend/attendance_log.csv`: nhật ký điểm danh.

### 5.3 Thư viện sử dụng
Theo file requirements:
- `tornado`
- `numpy`
- `imutils`
- `opencv-python`
- `websockets`

### 5.4 API và route chính
- `GET /api/faces`: trạng thái nhận diện theo từng camera.
- `GET/POST /api/attendance/config`: lấy/cập nhật chế độ điểm danh và góc camera.
- `POST /api/attendance/heartbeat`: xác nhận màn hình điểm danh đang hoạt động.
- `GET /api/attendance`: lấy dữ liệu lịch sử điểm danh.
- `GET /api/admin/known_faces`: lấy dữ liệu đăng ký khuôn mặt (cần đăng nhập).
- `POST /api/admin/register_face`: đăng ký khuôn mặt mới.
- `POST /api/admin/delete_registration`: xóa 1 bản ghi đăng ký.
- `POST /api/admin/delete_all_registrations`: xóa toàn bộ đăng ký.
- `POST /api/admin/delete_all_attendance`: xóa toàn bộ điểm danh.
- `/attendance`: trang điểm danh.
- `/admin/login`, `/admin/register`: khu vực quản trị.

### 5.5 Cơ chế bảo mật hiện có
- Đăng nhập quản trị dùng cookie (`set_secure_cookie`).
- Tài khoản admin đang hard-code trong mã nguồn (`admin / abc@123`) để demo.
- Chưa có phân quyền nhiều vai trò, chưa mã hóa mật khẩu băm trong CSDL.

---

## 6) Triển khai và vận hành

### 6.1 Cấu hình ESP32-CAM
Trong firmware:
- Khai báo WiFi: `ssid`, `password`.
- Khai báo `ws_url` trỏ về server WebSocket.
- Khai báo `DEVICE_ID` duy nhất cho từng camera.

### 6.2 Chạy backend Python
1. Cài thư viện: `pip install -r python_backend/requirements.txt`
2. Chạy server: `python python_backend/websockets_stream.py`
3. Mặc định server chạy cổng `3000`.

### 6.3 Sử dụng hệ thống
1. Mở `/attendance` để theo dõi stream và điểm danh realtime.
2. Mở `/admin/login` để đăng nhập quản trị.
3. Vào `/admin/register`, chọn thiết bị và lưu khuôn mặt cho `person_id`, `person_name`.
4. Theo dõi dữ liệu tại bảng lịch sử hoặc file CSV.

---

## 7) Kết quả đạt được
- ESP32-CAM truyền frame ổn định về backend qua WebSocket.
- Nhận diện khuôn mặt realtime theo từng camera đang kết nối.
- Hỗ trợ điểm danh hai chế độ CHECK_IN/CHECK_OUT.
- Có cơ chế heartbeat để chỉ ghi nhận khi màn hình điểm danh hoạt động.
- Có cơ chế chống trùng điểm danh trong cùng ngày.
- Có giao diện quản trị riêng để đăng ký/xóa dữ liệu khuôn mặt.

---

## 8) Đánh giá

### 8.1 Ưu điểm
- Chi phí thấp, dễ tái sử dụng phần cứng.
- Cấu trúc hệ thống rõ ràng, dễ demo môn học.
- Tách biệt chức năng: stream, API, quản trị, điểm danh.
- Dễ mở rộng nhiều camera bằng `DEVICE_ID`.

### 8.2 Hạn chế
- Độ chính xác phụ thuộc ánh sáng, góc mặt, chất lượng ảnh.
- Thuật toán nhận diện còn đơn giản, chưa dùng embedding deep learning.
- Xác thực admin và lưu trữ dữ liệu chưa đạt mức production.
- Lưu bằng CSV khó mở rộng khi lượng dữ liệu lớn.

### 8.3 Hướng phát triển
1. Nâng cấp nhận diện bằng FaceNet/ArcFace hoặc InsightFace.
2. Chuyển lưu trữ sang MySQL/PostgreSQL.
3. Mã hóa, băm mật khẩu, thêm RBAC (role-based access control).
4. Bổ sung anti-spoofing (chống giả mạo bằng ảnh/video).
5. Đồng bộ cloud và dashboard thống kê theo ngày/lớp/phòng.

---

## 9) Kết luận
Đề tài đã hoàn thành mục tiêu xây dựng hệ thống điểm danh khuôn mặt IoT hoạt động thực tế với ESP32-CAM và Python. Hệ thống thể hiện đầy đủ chu trình IoT: thu nhận dữ liệu từ thiết bị biên, truyền dữ liệu thời gian thực, xử lý nhận diện, cung cấp giao diện vận hành và lưu vết kết quả. Đây là nền tảng khả thi để phát triển thành sản phẩm điểm danh quy mô lớn hơn.

---

## 10) Tài liệu tham khảo
1. OpenCV Documentation: https://docs.opencv.org/
2. Tornado Web Framework: https://www.tornadoweb.org/
3. ESP32-CAM Technical Docs: https://docs.espressif.com/
4. ArduinoWebsockets Library: https://github.com/gilmaimon/ArduinoWebsockets

---

## 11) Phụ lục

### 11.1 Cấu trúc thư mục chính
- `arduino/esp32cam_ws_stream/esp32cam_ws_stream.ino`
- `python_backend/websockets_stream.py`
- `python_backend/templates/attendance.html`
- `python_backend/templates/admin_login.html`
- `python_backend/templates/admin_register.html`
- `python_backend/known_faces/`
- `python_backend/face_registrations.csv`
- `python_backend/attendance_log.csv`

### 11.2 Tài khoản quản trị mặc định (môi trường demo)
- Username: `admin`
- Password: `abc@123`

> Khuyến nghị khi nộp chính thức hoặc triển khai thật: đổi tài khoản mặc định, tăng cường bảo mật xác thực và loại bỏ thông tin nhạy cảm khỏi mã nguồn.
