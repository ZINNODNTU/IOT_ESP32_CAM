# HƯỚNG DẪN TRIỂN KHAI THƯƠNG MẠI ATTENDAI IOT

## Tổng quan
Hệ thống AttendAI IoT đã được tối ưu hóa và chuẩn hóa cho môi trường production với:
- **Mạng ổn định**: ESP32 với retry logic, watchdog, exponential backoff
- **Hiệu suất cao**: Python backend với cấu hình tối ưu
- **Dễ triển khai**: Cấu hình tập trung, documentation đầy đủ

## Cấu trúc file sau khi tối ưu hóa

```
AttendAI_IOT/
├── arduino/
│   └── esp32cam_ws_stream/
│       └── esp32cam_ws_stream.ino          # ESP32 code (đã tối ưu mạng)
├── python_backend/
│   ├── websockets_stream.py                 # Server chính
│   ├── config.py                           # Cấu hình production
│   ├── requirements.txt                     # Python dependencies
│   ├── attendance_log.csv                   # Log điểm danh
│   ├── face_registrations.csv               # Đăng ký khuôn mặt
│   ├── known_faces/                         # Thư mục khuôn mặt đã biết
│   └── templates/                           # HTML templates
│       ├── admin_login.html
│       ├── admin_register.html
│       ├── attendance.html
│       └── index.html
└── README.md                                # Documentation chính
```

## Bước 1: Cài đặt Python Backend

### 1.1. Chuẩn bị server
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3-pip python3-venv

# CentOS/RHEL
sudo yum install python3-pip
```

### 1.2. Tạo virtual environment và cài đặt dependencies
```bash
cd python_backend
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 1.3. Cấu hình production
Chỉnh sửa `config.py` nếu cần:
```python
# Đổi mật khẩu admin (QUAN TRỌNG!)
ADMIN_CONFIG = {
    "username": "admin",
    "password": "YOUR_STRONG_PASSWORD_HERE",  # THAY ĐỔI NGAY!
}
```

## Bước 2: Cấu hình ESP32 Camera

### 2.1. Chuẩn bị Arduino IDE
- Cài đặt Arduino IDE
- Thêm board ESP32: File → Preferences → Additional Boards Manager URLs
  ```
  https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
  ```
- Cài đặt board: Tools → Board → Boards Manager → "ESP32 by Espressif Systems"

### 2.2. Cấu hình code ESP32
Mở `arduino/esp32cam_ws_stream/esp32cam_ws_stream.ino` và chỉnh sửa:

```cpp
// 1. Cấu hình WiFi (dòng 11-12)
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// 2. Cấu hình server (dòng 19-22)
// CHO LOCAL TESTING:
// const char* ws_url = "ws://YOUR_SERVER_IP:3000/ws";

// CHO PRODUCTION SERVER:
const char* ws_url = "ws://YOUR_PRODUCTION_SERVER_IP:3000/ws";
```

### 2.3. Upload code lên ESP32
1. Kết nối ESP32-CAM với máy tính
2. Chọn board: Tools → Board → "AI Thinker ESP32-CAM"
3. Chọn port COM
4. Nhấn Upload

## Bước 3: Khởi động hệ thống

### 3.1. Khởi động Python Backend
```bash
cd python_backend
source venv/bin/activate  # Linux/Mac
# hoặc venv\Scripts\activate  # Windows

# Khởi động server
python websockets_stream.py
```

### 3.2. Kiểm tra server
Mở trình duyệt truy cập:
- `http://SERVER_IP:3000` - Trang chủ
- `http://SERVER_IP:3000/attendance` - Trang điểm danh
- `http://SERVER_IP:3000/admin/login` - Trang admin

### 3.3. Kiểm tra kết nối ESP32
- Mở Serial Monitor (115200 baud)
- ESP32 sẽ hiển thị:
  ```
  WiFi connected
  IP: 192.168.x.x
  WebSocket connected
  Frame X sent (Y bytes, Z ms)
  ```

## Bước 4: Cấu hình Production (Nâng cao)

### 4.1. Sử dụng systemd (Linux)
Tạo file service `/etc/systemd/system/attendai.service`:
```ini
[Unit]
Description=AttendAI IoT Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/python_backend
ExecStart=/path/to/python_backend/venv/bin/python websockets_stream.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Khởi động service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable attendai
sudo systemctl start attendai
sudo systemctl status attendai
```

### 4.2. Cấu hình Nginx reverse proxy (optional)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### 4.3. Cấu hình SSL (HTTPS/WSS)
```bash
# Sử dụng Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Bước 5: Monitoring và Maintenance

### 5.1. Monitoring cơ bản
```bash
# Kiểm tra CPU, memory
htop
free -h

# Kiểm tra logs
tail -f python_backend/app.log
journalctl -u attendai -f

# Kiểm tra kết nối
netstat -tulpn | grep :3000
```

### 5.2. Backup dữ liệu
Tạo script backup `backup.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/backup/attendai"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR/$DATE
cp python_backend/attendance_log.csv $BACKUP_DIR/$DATE/
cp python_backend/face_registrations.csv $BACKUP_DIR/$DATE/
cp -r python_backend/known_faces $BACKUP_DIR/$DATE/

# Xóa backup cũ hơn 30 ngày
find $BACKUP_DIR -type d -mtime +30 -exec rm -rf {} \;
```

### 5.3. Xử lý sự cố thường gặp

#### **ESP32 không kết nối được**
1. Kiểm tra Serial Monitor ESP32
2. Kiểm tra server có đang chạy không: `ps aux | grep python`
3. Kiểm tra firewall: `sudo ufw status`
4. Test kết nối: `telnet SERVER_IP 3000`

#### **Server không nhận được ảnh**
1. Kiểm tra server log: `tail -f app.log`
2. Kiểm tra ESP32 log có "Frame sent" không
3. Test WebSocket với client: `websocat ws://SERVER_IP:3000/ws`

#### **Hiệu suất thấp**
1. Giảm FPS ESP32: `#define TARGET_FPS 3`
2. Tăng skip frame ratio: `SKIP_FRAME_RATIO = 4`
3. Giảm chất lượng ảnh: `config.jpeg_quality = 20`

## Bước 6: Scaling cho nhiều camera

### 6.1. Load balancing
Sử dụng Nginx load balancer:
```nginx
upstream attendai_backend {
    server 127.0.0.1:3000;
    server 127.0.0.1:3001;
    server 127.0.0.1:3002;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://attendai_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 6.2. Multiple server instances
```bash
# Khởi động nhiều instance
python websockets_stream.py --port 3000 &
python websockets_stream.py --port 3001 &
python websockets_stream.py --port 3002 &
```

## Tối ưu hóa đã được áp dụng

### ESP32 Camera:
- ✅ Retry logic với exponential backoff
- ✅ Watchdog timer tự động restart
- ✅ Giảm FPS từ 10 xuống 5
- ✅ Giảm frame size từ 30KB xuống 15KB
- ✅ Giảm chất lượng ảnh để tránh FB-OVF
- ✅ Connection timeout và error handling

### Python Backend:
- ✅ Cấu hình tập trung (`config.py`)
- ✅ Tăng worker từ 2 lên 4
- ✅ Skip frame ratio từ 2 lên 3
- ✅ Giới hạn so sánh khuôn mặt (20 comparisons)
- ✅ Frame skipping khi hệ thống quá tải
- ✅ Cache face embeddings

## Ước lượng hiệu suất production
- **Throughput**: 5-10 FPS/camera ổn định
- **Latency**: < 500ms end-to-end
- **Concurrent cameras**: 10-20 camera/server
- **CPU usage**: 30-50% cho 10 camera
- **Memory usage**: 200-400MB cho 10 camera

## Liên hệ và hỗ trợ
- **Issues**: Tạo issue trên repository
- **Emergency**: Khởi động lại service `sudo systemctl restart attendai`
- **Backup**: Chạy backup script hàng ngày

---
*Phiên bản: Production 2.0*
*Cập nhật: 2026-04-21*
*Tài liệu này nên được cập nhật khi có thay đổi hệ thống*