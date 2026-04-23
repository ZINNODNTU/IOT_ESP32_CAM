# 🚀 Quick Start Guide - AttendAI IoT

## Khởi Động Nhanh

### 1️⃣ Cấu Hình ESP32-CAM

Mở file [`esp32cam_ws_stream.ino`](arduino/esp32cam_ws_stream/esp32cam_ws_stream.ino) và chỉnh sửa:

```cpp
// WiFi của bạn
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// AWS Server Public IP
const char* ws_url = "ws://YOUR_AWS_PUBLIC_IP:3000/ws";

// ID camera (unique cho mỗi camera)
#define DEVICE_ID "esp32cam_01"
```

### 2️⃣ Chạy Server Trên AWS

```bash
# SSH vào EC2
ssh -i "your-key.pem" ubuntu@YOUR_EC2_PUBLIC_IP

# Di chuyển vào thư mục project
cd ~/attendai/python_backend

# Chạy script khởi động
chmod +x start_server.sh
./start_server.sh
```

### 3️⃣ Truy Cập Web Interface

- **Điểm danh**: `http://YOUR_EC2_PUBLIC_IP:3000/attendance`
- **Admin**: `http://YOUR_EC2_PUBLIC_IP:3000/admin/login`
  - Username: `admin`
  - Password: `abc@123` (đổi trong [`config.py`](python_backend/config.py))

---

## 📚 Tài Liệu Chi Tiết

- **Hướng dẫn deployment AWS đầy đủ**: [`AWS_DEPLOYMENT_GUIDE.md`](AWS_DEPLOYMENT_GUIDE.md)
- **Cấu hình production**: [`PRODUCTION_DEPLOYMENT.md`](PRODUCTION_DEPLOYMENT.md)
- **Báo cáo môn học**: [`BAO_CAO_MON_HOC.md`](BAO_CAO_MON_HOC.md)

---

## 🔧 Cấu Trúc Project

```
AttendAI_IOT/
├── arduino/
│   └── esp32cam_ws_stream/
│       └── esp32cam_ws_stream.ino    # Code ESP32-CAM
├── python_backend/
│   ├── websockets_stream.py          # Server chính
│   ├── config.py                     # Cấu hình
│   ├── requirements.txt              # Dependencies
│   ├── start_server.sh               # Script khởi động (Linux)
│   ├── start_server.bat              # Script khởi động (Windows)
│   ├── templates/                    # HTML templates
│   ├── known_faces/                  # Ảnh khuôn mặt đã đăng ký
│   ├── attendance_log.csv            # Log điểm danh
│   └── face_registrations.csv        # Danh sách đăng ký
├── AWS_DEPLOYMENT_GUIDE.md           # Hướng dẫn AWS
└── README.md                         # File này
```

---

## ⚙️ Cấu Hình Quan Trọng

### Server ([`config.py`](python_backend/config.py))

```python
# Hiệu năng
MAX_WORKERS = 4                    # Số worker threads
SKIP_FRAME_RATIO = 3               # Bỏ qua frame để tăng tốc
FACE_SIMILARITY_THRESHOLD = 0.86   # Ngưỡng nhận diện

# Bảo mật
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "abc@123"         # ⚠️ ĐỔI MẬT KHẨU!
```

### ESP32-CAM ([`esp32cam_ws_stream.ino`](arduino/esp32cam_ws_stream/esp32cam_ws_stream.ino))

```cpp
#define MAX_FRAME_SIZE 15000       // Kích thước frame tối đa
#define TARGET_FPS 5               // FPS mục tiêu
#define RECONNECT_DELAY_MS 5000    // Thời gian reconnect
```

---

## 🐛 Troubleshooting

### ESP32 không kết nối được WiFi
- Kiểm tra SSID và password
- Đảm bảo WiFi là 2.4GHz (không phải 5GHz)
- Kiểm tra nguồn 5V/2A ổn định

### ESP32 không kết nối được WebSocket
- Kiểm tra AWS Public IP đúng chưa
- Kiểm tra Security Group đã mở port 3000
- Kiểm tra server đang chạy: `sudo systemctl status attendai`

### Server bị crash
- Xem logs: `sudo journalctl -u attendai -f`
- Kiểm tra RAM: `free -h`
- Restart: `sudo systemctl restart attendai`

---

## 📊 Tính Năng

✅ Nhận diện khuôn mặt real-time  
✅ Hỗ trợ nhiều camera đồng thời  
✅ Điểm danh tự động (Check-in/Check-out)  
✅ Quản lý đăng ký khuôn mặt qua web  
✅ Export dữ liệu CSV  
✅ Tối ưu cho AWS EC2  
✅ Auto-reconnect khi mất kết nối  
✅ Watchdog tự động restart  

---

## 🔒 Bảo Mật

**Trước khi deploy production:**

1. ✅ Đổi mật khẩu admin trong [`config.py`](python_backend/config.py:53)
2. ✅ Giới hạn IP trong AWS Security Group
3. ✅ Setup HTTPS/WSS với SSL certificate
4. ✅ Enable firewall: `sudo ufw enable`
5. ✅ Regular backup CSV files

---

## 📈 Monitoring

```bash
# Xem logs real-time
sudo journalctl -u attendai -f

# Kiểm tra CPU/RAM
htop

# Kiểm tra network
sudo iftop

# Kiểm tra disk
df -h
```

---

## 🎯 Performance Tips

**Nếu có nhiều camera (>3):**
- Nâng cấp EC2 lên `t2.medium` hoặc `t2.large`
- Tăng `MAX_WORKERS` trong config

**Nếu mạng chậm:**
- Giảm `TARGET_FPS` trong ESP32 code
- Tăng `SKIP_FRAME_RATIO` trong server config

**Nếu CPU cao:**
- Tăng `SKIP_FRAME_RATIO`
- Giảm `MAX_FACES_PER_FRAME`

---

## 📞 Support

Nếu gặp vấn đề, kiểm tra:
1. Server logs: `sudo journalctl -u attendai -f`
2. ESP32 Serial Monitor (115200 baud)
3. Browser Console (F12)
4. AWS Security Group rules

---

## 📝 License

Dự án AttendAI IoT - Hệ thống điểm danh khuôn mặt IoT

---

**Chúc bạn triển khai thành công! 🎉**
