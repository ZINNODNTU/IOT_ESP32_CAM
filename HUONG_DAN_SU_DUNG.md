# 🎯 Hướng Dẫn Sử Dụng Hệ Thống Điểm Danh AttendAI IoT

## 📋 Tổng Quan

Hệ thống điểm danh khuôn mặt tự động sử dụng ESP32-CAM và AI, hỗ trợ:
- ✅ Nhận diện khuôn mặt real-time
- ✅ Điểm danh tự động (Check-in/Check-out)
- ✅ Quản lý qua web interface
- ✅ Chạy trên local hoặc AWS

---

## 🚀 Khởi Động Nhanh

### 1. Chạy Server

**Trên Windows (Local)**:
```cmd
cd python_backend
python websockets_stream.py
```

**Trên Linux/AWS**:
```bash
cd python_backend
chmod +x start_server.sh
./start_server.sh
```

Bạn sẽ thấy:
```
🧠 Loaded known face samples: 0
🔐 Admin login: admin / abc@123
🚀 Server bind: 0.0.0.0:3000
🌐 Public base URL: http://YOUR_IP:3000
📋 Attendance page: http://YOUR_IP:3000/attendance
```

### 2. Cấu Hình ESP32-CAM

Mở [`esp32cam_ws_stream.ino`](arduino/esp32cam_ws_stream/esp32cam_ws_stream.ino) và sửa:

```cpp
// WiFi
const char* ssid = "YOUR_WIFI_NAME";
const char* password = "YOUR_WIFI_PASSWORD";

// Server (dùng IP từ bước 1)
const char* ws_url = "ws://YOUR_SERVER_IP:3000/ws";

// Device ID (unique cho mỗi camera)
#define DEVICE_ID "esp32cam_01"
```

### 3. Upload Code Lên ESP32

1. Kết nối FTDI với ESP32-CAM
2. **Nối GPIO0 với GND** (quan trọng!)
3. Tools → Board → AI Thinker ESP32-CAM
4. Tools → Port → Chọn COM port
5. Upload
6. **Ngắt GPIO0 khỏi GND**
7. Nhấn Reset

### 4. Kiểm Tra Kết Nối

Mở Serial Monitor (115200 baud), bạn sẽ thấy:
```
✅ WiFi connected
📍 IP: 192.168.x.x
✅ WebSocket connected
📱 Device ID: esp32cam_01
🚀 System ready!
```

Server sẽ log:
```
🔌 New connection from 192.168.x.x
✅ Device connected: esp32cam_01 from 192.168.x.x
📦 Frame #20 from esp32cam_01: 5768 bytes
```

---

## 👤 Đăng Ký Khuôn Mặt

### Bước 1: Đăng Nhập Admin

1. Truy cập: `http://YOUR_IP:3000/admin/login`
2. Username: `admin`
3. Password: `abc@123`

### Bước 2: Đăng Ký Người Dùng

1. Vào trang Admin: `http://YOUR_IP:3000/admin/register`
2. Chọn camera từ dropdown
3. Nhập thông tin:
   - **Person ID**: Mã số (ví dụ: `SV001`, `NV001`)
   - **Person Name**: Tên đầy đủ (ví dụ: `Nguyễn Văn A`)
4. Đứng trước camera, đảm bảo khuôn mặt rõ ràng
5. Click **"Đăng ký khuôn mặt"**

Thành công sẽ thấy:
```
✅ Đã đăng ký khuôn mặt cho Nguyễn Văn A
```

### Bước 3: Kiểm Tra Danh Sách

Trong trang Admin, xem danh sách người đã đăng ký:
- Person ID
- Person Name  
- Timestamp
- Image file

---

## 📸 Điểm Danh

### Bước 1: Mở Trang Điểm Danh

Truy cập: `http://YOUR_IP:3000/attendance`

### Bước 2: Chọn Chế Độ

- **Check In**: Điểm danh vào
- **Check Out**: Điểm danh ra

### Bước 3: Đứng Trước Camera

Hệ thống sẽ tự động:
1. Phát hiện khuôn mặt
2. Nhận diện người dùng
3. Hiển thị tên và độ chính xác
4. Ghi log điểm danh (nếu chưa điểm danh hôm nay)

Khi nhận diện thành công:
```
Nguyễn Văn A (0.92) [CHECK_IN]
```

### Bước 4: Xem Lịch Sử

Trong trang Attendance, xem:
- **Lượt điểm danh hôm nay**: Số người đã điểm danh
- **Lịch sử điểm danh**: Bảng chi tiết với timestamp, tên, mode

---

## 🔧 Cấu Hình Nâng Cao

### Thay Đổi Mật Khẩu Admin

Sửa [`config.py`](python_backend/config.py:52-54):
```python
ADMIN_CONFIG: Dict[str, str] = {
    "username": "admin",
    "password": "YOUR_NEW_PASSWORD",  # ĐỔI MẬT KHẨU!
}
```

### Điều Chỉnh Độ Nhạy Nhận Diện

Sửa [`config.py`](python_backend/config.py:25):
```python
"similarity_threshold": 0.86,  # Tăng = khó nhận diện hơn, giảm = dễ hơn
```

### Xoay Camera

Trong trang Attendance hoặc Admin, click:
- **Xoay trái 90°**
- **Xoay phải 90°**
- **Góc mặc định**

### Tối Ưu Hiệu Năng

Sửa [`config.py`](python_backend/config.py:33-40):
```python
PERFORMANCE_CONFIG: Dict[str, Any] = {
    "max_workers": 4,              # Tăng nếu có nhiều camera
    "skip_frame_ratio": 3,         # Giảm = xử lý nhiều frame hơn
    "enable_frame_skipping": True, # Bật để tiết kiệm CPU
}
```

---

## 🐛 Troubleshooting

### ESP32 Không Kết Nối WiFi

**Triệu chứng**: Serial Monitor hiện "Connecting WiFi....." mãi

**Giải pháp**:
- Kiểm tra SSID và password đúng chưa
- Đảm bảo WiFi là 2.4GHz (không phải 5GHz)
- Kiểm tra nguồn 5V/2A ổn định
- Thử reset ESP32

### ESP32 Không Kết Nối WebSocket

**Triệu chứng**: "❌ WebSocket failed"

**Giải pháp**:
- Kiểm tra server đang chạy: `netstat -an | findstr 3000`
- Kiểm tra IP server đúng chưa
- Ping server: `ping YOUR_SERVER_IP`
- Kiểm tra firewall/Security Group

### Không Hiển Thị Video

**Triệu chứng**: Web hiện "Không phát hiện mặt trong frame"

**Giải pháp**:
1. Kiểm tra ESP32 đã kết nối: Xem "Thiết bị online: 1"
2. Kiểm tra server logs có `📦 Frame #...` không
3. Restart server Python
4. Reset ESP32
5. Xem [`DEBUG_VIDEO_STREAM.md`](DEBUG_VIDEO_STREAM.md)

### Nhận Diện Sai Người

**Triệu chứng**: Nhận diện nhầm hoặc hiện "Unknown"

**Giải pháp**:
- Đăng ký thêm ảnh khuôn mặt (nhiều góc độ)
- Giảm `similarity_threshold` trong config
- Đảm bảo ánh sáng tốt khi đăng ký và điểm danh
- Khuôn mặt nhìn thẳng vào camera

### Server Bị Crash

**Triệu chứng**: Server dừng đột ngột

**Giải pháp**:
- Xem logs: `python websockets_stream.py 2>&1 | tee server.log`
- Kiểm tra RAM: `free -h` (Linux) hoặc Task Manager (Windows)
- Giảm `max_workers` trong config
- Tăng `skip_frame_ratio`

---

## 📊 Quản Lý Dữ Liệu

### Export Dữ Liệu Điểm Danh

File CSV: [`attendance_log.csv`](python_backend/attendance_log.csv)

Cột:
- `timestamp`: Thời gian điểm danh
- `date`: Ngày
- `person_id`: Mã số
- `person_name`: Tên
- `device_id`: Camera nào
- `score`: Độ chính xác
- `status`: OK
- `mode`: CHECK_IN hoặc CHECK_OUT

### Backup Dữ Liệu

**Quan trọng**: Backup định kỳ các file:
```
python_backend/attendance_log.csv
python_backend/face_registrations.csv
python_backend/known_faces/
```

**Trên Windows**:
```cmd
xcopy python_backend\*.csv backup\ /Y
xcopy python_backend\known_faces backup\known_faces\ /E /Y
```

**Trên Linux**:
```bash
cp python_backend/*.csv backup/
cp -r python_backend/known_faces backup/
```

### Xóa Dữ Liệu

**Xóa 1 người**:
1. Vào Admin page
2. Tìm người cần xóa trong danh sách
3. Click nút Xóa

**Xóa toàn bộ đăng ký**:
1. Vào Admin page
2. Click "Xóa toàn bộ dữ liệu đăng ký"
3. Confirm

**Xóa lịch sử điểm danh**:
1. Vào Admin page
2. Click "Xóa toàn bộ dữ liệu điểm danh"
3. Confirm

---

## 🔒 Bảo Mật

### Checklist Bảo Mật

- [ ] Đổi mật khẩu admin mặc định
- [ ] Giới hạn IP truy cập (firewall/Security Group)
- [ ] Sử dụng HTTPS (nếu public)
- [ ] Backup dữ liệu định kỳ
- [ ] Không share admin credentials
- [ ] Update dependencies thường xuyên

### Setup HTTPS (Optional)

Nếu deploy public, nên dùng HTTPS:

1. Cài Nginx
2. Cài Certbot
3. Cấu hình reverse proxy
4. Xem [`AWS_DEPLOYMENT_GUIDE.md`](AWS_DEPLOYMENT_GUIDE.md)

---

## 📈 Monitoring

### Kiểm Tra Trạng Thái

**Server logs**:
```bash
# Real-time
tail -f server.log

# Tìm lỗi
grep "ERROR" server.log
grep "❌" server.log
```

**ESP32 logs**:
- Mở Serial Monitor
- Xem FPS, frame size, send time
- Kiểm tra reconnect

**System resources**:
```bash
# CPU, RAM
htop

# Network
iftop

# Disk
df -h
```

### Performance Metrics

**Tốt**:
- FPS: 3-5
- Frame size: 5-10KB
- Send time: <100ms
- CPU: <50%
- RAM: <1GB

**Cần tối ưu**:
- FPS: <2 → Tăng bandwidth
- Send time: >200ms → Giảm quality/size
- CPU: >80% → Tăng skip_frame_ratio
- RAM: >2GB → Giảm max_workers

---

## 📞 Hỗ Trợ

### Tài Liệu

- [`README.md`](README.md) - Tổng quan
- [`QUICKSTART.md`](QUICKSTART.md) - Khởi động nhanh
- [`AWS_DEPLOYMENT_GUIDE.md`](AWS_DEPLOYMENT_GUIDE.md) - Deploy AWS
- [`DEBUG_VIDEO_STREAM.md`](DEBUG_VIDEO_STREAM.md) - Debug video
- [`ESP32_UPLOAD_TROUBLESHOOTING.md`](ESP32_UPLOAD_TROUBLESHOOTING.md) - Upload ESP32

### Logs Cần Gửi Khi Báo Lỗi

1. Server logs (50 dòng cuối)
2. ESP32 Serial Monitor output
3. Browser Console errors (F12)
4. Screenshot lỗi
5. Mô tả chi tiết vấn đề

---

## 🎓 Tips & Tricks

### Tăng Độ Chính Xác

1. **Đăng ký nhiều ảnh**: Mỗi người nên có 2-3 ảnh từ góc độ khác nhau
2. **Ánh sáng tốt**: Đăng ký và điểm danh ở nơi sáng
3. **Khuôn mặt rõ**: Không đeo khẩu trang, kính đen
4. **Nhìn thẳng**: Khuôn mặt hướng về camera

### Tăng Tốc Độ

1. **Giảm resolution**: Sửa ESP32 code, dùng QQVGA
2. **Tăng skip ratio**: Sửa config, tăng lên 5
3. **Giảm quality**: Sửa ESP32, tăng jpeg_quality lên 25
4. **Upgrade hardware**: Dùng EC2 lớn hơn

### Multi-Camera Setup

1. **Mỗi ESP32 cần Device ID riêng**:
```cpp
#define DEVICE_ID "esp32cam_office"
#define DEVICE_ID "esp32cam_entrance"
#define DEVICE_ID "esp32cam_lab"
```

2. **Server tự động xử lý nhiều camera**
3. **Chọn camera trong dropdown khi đăng ký/điểm danh**

---

**Chúc bạn sử dụng thành công! 🎉**
