# Hướng Dẫn Triển Khai AttendAI IoT Trên AWS EC2

## 📋 Mục Lục
1. [Yêu Cầu Hệ Thống](#yêu-cầu-hệ-thống)
2. [Chuẩn Bị AWS EC2](#chuẩn-bị-aws-ec2)
3. [Cài Đặt Server](#cài-đặt-server)
4. [Cấu Hình ESP32-CAM](#cấu-hình-esp32-cam)
5. [Kiểm Tra Và Troubleshooting](#kiểm-tra-và-troubleshooting)

---

## 🖥️ Yêu Cầu Hệ Thống

### AWS EC2 Instance
- **Loại Instance**: `t2.small` hoặc cao hơn (tối thiểu 2GB RAM)
- **OS**: Ubuntu 20.04 LTS hoặc 22.04 LTS
- **Storage**: Tối thiểu 20GB
- **Region**: Chọn region gần nhất (ví dụ: ap-southeast-1 cho Singapore)

### ESP32-CAM
- **Board**: AI-Thinker ESP32-CAM
- **Nguồn**: 5V/2A (ổn định)
- **WiFi**: 2.4GHz (không hỗ trợ 5GHz)

---

## ☁️ Chuẩn Bị AWS EC2

### Bước 1: Tạo EC2 Instance

1. **Đăng nhập AWS Console** → EC2 Dashboard
2. **Launch Instance**:
   - Name: `AttendAI-Server`
   - AMI: Ubuntu Server 22.04 LTS
   - Instance type: `t2.small` (hoặc `t2.medium` cho nhiều camera)
   - Key pair: Tạo mới hoặc chọn existing key

3. **Network Settings**:
   - Auto-assign public IP: **Enable**
   - Security Group: Tạo mới với tên `AttendAI-SG`

### Bước 2: Cấu Hình Security Group

Thêm các **Inbound Rules** sau:

| Type | Protocol | Port Range | Source | Description |
|------|----------|------------|--------|-------------|
| SSH | TCP | 22 | My IP | SSH access |
| Custom TCP | TCP | 3000 | 0.0.0.0/0 | WebSocket server |
| HTTP | TCP | 80 | 0.0.0.0/0 | HTTP (optional) |
| HTTPS | TCP | 443 | 0.0.0.0/0 | HTTPS (optional) |

⚠️ **Lưu ý bảo mật**: 
- Giới hạn SSH (port 22) chỉ cho IP của bạn
- Sau khi test xong, nên giới hạn port 3000 cho IP cụ thể

### Bước 3: Kết Nối SSH

```bash
# Trên Windows (PowerShell hoặc CMD)
ssh -i "your-key.pem" ubuntu@YOUR_EC2_PUBLIC_IP

# Trên Linux/Mac
chmod 400 your-key.pem
ssh -i "your-key.pem" ubuntu@YOUR_EC2_PUBLIC_IP
```

---

## 🚀 Cài Đặt Server

### Bước 1: Cập Nhật Hệ Thống

```bash
sudo apt update && sudo apt upgrade -y
```

### Bước 2: Cài Đặt Python và Dependencies

```bash
# Cài đặt Python 3.10+
sudo apt install -y python3 python3-pip python3-venv

# Cài đặt các thư viện hệ thống cần thiết
sudo apt install -y libopencv-dev python3-opencv
sudo apt install -y build-essential cmake pkg-config
sudo apt install -y libjpeg-dev libpng-dev libtiff-dev
sudo apt install -y libavcodec-dev libavformat-dev libswscale-dev
```

### Bước 3: Clone Project

```bash
# Tạo thư mục project
mkdir -p ~/attendai
cd ~/attendai

# Upload code lên server (sử dụng scp hoặc git)
# Cách 1: Sử dụng SCP từ máy local
# scp -i "your-key.pem" -r ./python_backend ubuntu@YOUR_EC2_PUBLIC_IP:~/attendai/

# Cách 2: Sử dụng Git (nếu có repository)
# git clone YOUR_REPO_URL .
```

### Bước 4: Cài Đặt Python Dependencies

```bash
cd ~/attendai/python_backend

# Tạo virtual environment
python3 -m venv venv
source venv/bin/activate

# Cài đặt requirements
pip install --upgrade pip
pip install -r requirements.txt
```

### Bước 5: Cấu Hình Environment Variables

```bash
# Tạo file .env
nano .env
```

Thêm nội dung sau:

```bash
# AWS Configuration
PUBLIC_HOST=YOUR_EC2_PUBLIC_IP
PORT=3000

# Admin Configuration (ĐỔI MẬT KHẨU!)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password_here

# Performance
MAX_WORKERS=4
SKIP_FRAME_RATIO=3
```

Lưu file: `Ctrl+O`, `Enter`, `Ctrl+X`

### Bước 6: Chạy Server (Test)

```bash
# Kích hoạt virtual environment
source venv/bin/activate

# Chạy server
python websockets_stream.py
```

Bạn sẽ thấy output:

```
🚀 Server bind: 0.0.0.0:3000
🌐 Public base URL: http://YOUR_EC2_PUBLIC_IP:3000
📋 Attendance page: http://YOUR_EC2_PUBLIC_IP:3000/attendance
🛠️ Admin page: http://YOUR_EC2_PUBLIC_IP:3000/admin/login
```

Nhấn `Ctrl+C` để dừng server.

### Bước 7: Cấu Hình Auto-Start với Systemd

Tạo service file:

```bash
sudo nano /etc/systemd/system/attendai.service
```

Thêm nội dung:

```ini
[Unit]
Description=AttendAI IoT Face Recognition Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/attendai/python_backend
Environment="PATH=/home/ubuntu/attendai/python_backend/venv/bin"
ExecStart=/home/ubuntu/attendai/python_backend/venv/bin/python websockets_stream.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Kích hoạt service:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (tự động chạy khi khởi động)
sudo systemctl enable attendai

# Start service
sudo systemctl start attendai

# Kiểm tra status
sudo systemctl status attendai
```

Các lệnh quản lý service:

```bash
# Xem logs
sudo journalctl -u attendai -f

# Restart service
sudo systemctl restart attendai

# Stop service
sudo systemctl stop attendai
```

---

## 📷 Cấu Hình ESP32-CAM

### Bước 1: Cài Đặt Arduino IDE

1. Download Arduino IDE từ: https://www.arduino.cc/en/software
2. Cài đặt ESP32 Board:
   - File → Preferences
   - Additional Board Manager URLs: `https://dl.espressif.com/dl/package_esp32_index.json`
   - Tools → Board → Boards Manager → Tìm "ESP32" → Install

### Bước 2: Cài Đặt Thư Viện

Tools → Manage Libraries → Tìm và cài đặt:
- `ArduinoWebsockets` by Gil Maimon

### Bước 3: Cấu Hình Code

Mở file [`esp32cam_ws_stream.ino`](arduino/esp32cam_ws_stream/esp32cam_ws_stream.ino) và chỉnh sửa:

```cpp
// ================= CẤU HÌNH WIFI =================
const char* ssid = "YOUR_WIFI_SSID";        // Tên WiFi của bạn
const char* password = "YOUR_WIFI_PASSWORD"; // Mật khẩu WiFi

// ================= CẤU HÌNH SERVER =================
const char* ws_url = "ws://YOUR_EC2_PUBLIC_IP:3000/ws";

// ================= CẤU HÌNH CAMERA =================
#define DEVICE_ID "esp32cam_01"  // ID duy nhất cho mỗi camera
```

**Ví dụ**:
```cpp
const char* ssid = "MyHomeWiFi";
const char* password = "MyPassword123";
const char* ws_url = "ws://13.239.29.180:3000/ws";
#define DEVICE_ID "esp32cam_office_01"
```

### Bước 4: Upload Code Lên ESP32-CAM

1. **Kết nối ESP32-CAM với FTDI**:
   - FTDI TX → ESP32 RX
   - FTDI RX → ESP32 TX
   - FTDI GND → ESP32 GND
   - FTDI 5V → ESP32 5V
   - **Nối GPIO0 với GND** (để vào chế độ flash)

2. **Cấu hình Arduino IDE**:
   - Tools → Board → ESP32 Arduino → AI Thinker ESP32-CAM
   - Tools → Port → Chọn COM port của FTDI
   - Tools → Upload Speed → 115200

3. **Upload**:
   - Nhấn nút Upload
   - Sau khi upload xong, **ngắt GPIO0 khỏi GND**
   - Nhấn nút Reset trên ESP32-CAM

4. **Kiểm tra Serial Monitor**:
   - Tools → Serial Monitor
   - Baud rate: 115200
   - Bạn sẽ thấy ESP32 kết nối WiFi và WebSocket

---

## 🔍 Kiểm Tra Và Troubleshooting

### Kiểm Tra Server

```bash
# Kiểm tra server đang chạy
sudo systemctl status attendai

# Xem logs real-time
sudo journalctl -u attendai -f

# Kiểm tra port đang listen
sudo netstat -tulpn | grep 3000

# Test từ local
curl http://localhost:3000/api/faces
```

### Kiểm Tra Từ Browser

1. Mở browser và truy cập:
   - Attendance page: `http://YOUR_EC2_PUBLIC_IP:3000/attendance`
   - Admin page: `http://YOUR_EC2_PUBLIC_IP:3000/admin/login`

2. Đăng nhập admin:
   - Username: `admin`
   - Password: (mật khẩu bạn đã đặt trong config)

### Troubleshooting ESP32-CAM

#### Lỗi: "WiFi connection timeout"
```
✅ Giải pháp:
- Kiểm tra SSID và password
- Đảm bảo WiFi là 2.4GHz (không phải 5GHz)
- Kiểm tra cường độ sóng WiFi
```

#### Lỗi: "WebSocket connection failed"
```
✅ Giải pháp:
- Kiểm tra EC2 Public IP có đúng không
- Kiểm tra Security Group đã mở port 3000
- Kiểm tra server đang chạy: sudo systemctl status attendai
- Ping EC2 từ mạng local: ping YOUR_EC2_PUBLIC_IP
```

#### Lỗi: "Camera init failed"
```
✅ Giải pháp:
- Kiểm tra nguồn 5V/2A ổn định
- Kiểm tra kết nối camera module
- Thử reset ESP32-CAM
```

#### Lỗi: "Frame too large" hoặc "FB-OVF"
```
✅ Giải pháp:
- Đã được tối ưu trong code (QVGA, quality 18)
- Giảm TARGET_FPS nếu vẫn lỗi
- Kiểm tra băng thông mạng
```

### Monitoring Server

```bash
# Kiểm tra CPU và RAM
htop

# Kiểm tra network traffic
sudo iftop

# Kiểm tra disk space
df -h

# Xem logs chi tiết
tail -f ~/attendai/python_backend/app.log
```

### Tối Ưu Hiệu Năng

1. **Nếu có nhiều camera (>3)**:
   - Nâng cấp lên `t2.medium` hoặc `t2.large`
   - Tăng `MAX_WORKERS` trong config

2. **Nếu mạng chậm**:
   - Giảm `TARGET_FPS` trong ESP32 code
   - Tăng `SKIP_FRAME_RATIO` trong server config

3. **Nếu CPU cao**:
   - Tăng `SKIP_FRAME_RATIO`
   - Giảm `MAX_FACES_PER_FRAME`
   - Giảm `MAX_FACE_COMPARISONS`

---

## 🔒 Bảo Mật Production

### 1. Đổi Mật Khẩu Admin
Chỉnh sửa [`config.py`](python_backend/config.py:53):
```python
ADMIN_CONFIG: Dict[str, str] = {
    "username": "admin",
    "password": "YOUR_STRONG_PASSWORD_HERE",  # ĐỔI MẬT KHẨU!
}
```

### 2. Cấu Hình Firewall
```bash
# Cài đặt UFW
sudo apt install ufw

# Cho phép SSH và port 3000
sudo ufw allow 22/tcp
sudo ufw allow 3000/tcp

# Enable firewall
sudo ufw enable
```

### 3. Giới Hạn IP (Optional)
Chỉnh sửa Security Group để chỉ cho phép IP cụ thể truy cập port 3000.

### 4. Setup HTTPS (Recommended)
```bash
# Cài đặt Nginx
sudo apt install nginx

# Cài đặt Certbot cho SSL
sudo apt install certbot python3-certbot-nginx

# Cấu hình domain và SSL
sudo certbot --nginx -d yourdomain.com
```

---

## 📊 Checklist Deployment

- [ ] EC2 instance đã tạo và chạy
- [ ] Security Group đã cấu hình đúng
- [ ] Server code đã upload
- [ ] Dependencies đã cài đặt
- [ ] Environment variables đã cấu hình
- [ ] Systemd service đã setup và running
- [ ] ESP32-CAM đã cấu hình WiFi và server URL
- [ ] ESP32-CAM kết nối thành công
- [ ] Web interface truy cập được
- [ ] Face registration hoạt động
- [ ] Face recognition hoạt động
- [ ] Attendance logging hoạt động
- [ ] Mật khẩu admin đã đổi
- [ ] Firewall đã cấu hình
- [ ] Monitoring đã setup

---

## 📞 Hỗ Trợ

Nếu gặp vấn đề, kiểm tra:
1. Server logs: `sudo journalctl -u attendai -f`
2. ESP32 Serial Monitor
3. Browser Console (F12)
4. Network connectivity: `ping`, `telnet`

**Các file quan trọng**:
- Server: [`websockets_stream.py`](python_backend/websockets_stream.py)
- Config: [`config.py`](python_backend/config.py)
- ESP32: [`esp32cam_ws_stream.ino`](arduino/esp32cam_ws_stream/esp32cam_ws_stream.ino)
- Requirements: [`requirements.txt`](python_backend/requirements.txt)

---

## 🎯 Kết Luận

Sau khi hoàn thành các bước trên, hệ thống AttendAI IoT của bạn sẽ:
- ✅ Chạy ổn định trên AWS EC2
- ✅ Tự động khởi động khi server reboot
- ✅ Xử lý nhiều camera đồng thời
- ✅ Nhận diện khuôn mặt real-time
- ✅ Ghi log điểm danh tự động

**Lưu ý**: Nhớ backup file CSV định kỳ để tránh mất dữ liệu!
