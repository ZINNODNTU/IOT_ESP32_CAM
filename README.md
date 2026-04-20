# AttendAI IoT - Hệ thống điểm danh khuôn mặt với ESP32-CAM

Hệ thống IoT sử dụng ESP32-CAM để stream video qua WebSocket đến backend Python, thực hiện nhận diện khuôn mặt và quản lý điểm danh tự động.

## 🚀 Triển khai trên AWS (Tối ưu hiệu năng, không lag)

### 1. Cấu hình AWS EC2 Instance
- **Instance Type**: t3.medium hoặc t3.large (tối thiểu 2GB RAM)
- **AMI**: Ubuntu 22.04 LTS
- **Security Group**: Mở port 3000 (HTTP) và 22 (SSH)
- **Storage**: 20GB GP2

### 2. Cài đặt Backend trên AWS

```bash
# Cập nhật hệ thống
sudo apt update -y
sudo apt upgrade -y

# Cài đặt dependencies
sudo apt install -y python3-pip python3-venv libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev

# Clone repository
git clone https://github.com/ZINNODNTU/IOT_ESP32_CAM.git
cd IOT_ESP32_CAM/python_backend

# Tạo virtual environment
python3 -m venv venv
source venv/bin/activate

# Cài đặt Python packages
pip install --upgrade pip
pip install tornado numpy imutils opencv-python websockets requests

# Thiết lập biến môi trường AWS
export PUBLIC_HOST=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
export PORT=3000

# Chạy server với cấu hình tối ưu cho AWS
python websockets_stream.py
```

### 3. Cấu hình ESP32-CAM cho AWS

Sửa file `arduino/esp32cam_ws_stream/esp32cam_ws_stream.ino`:

```cpp
// Cấu hình WiFi
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Sửa IP server AWS (lấy từ EC2 Public IP)
const char* ws_url = "ws://YOUR_EC2_PUBLIC_IP:3000/ws";

// ID camera (đặt tên duy nhất)
const char* DEVICE_ID = "esp32cam_01";
```

### 4. Tối ưu hiệu năng đã được tích hợp

#### Backend Python (`websockets_stream.py`):
- **MAX_WORKERS=2**: Giới hạn số worker xử lý
- **SKIP_FRAME_RATIO=2**: Xử lý 1 frame, bỏ qua 1 frame (giảm 50% tải)
- **Face Cache**: Cache kết quả nhận diện trong 10 giây
- **Rate Limiting**: Giới hạn 20fps tối đa
- **Timeout**: Timeout xử lý 500ms

#### ESP32-CAM (`esp32cam_ws_stream.ino`):
- **TARGET_FPS=10**: Giảm FPS từ 30 xuống 10
- **Dynamic Delay**: Điều chỉnh delay động dựa trên thời gian gửi
- **Frame Size Limit**: Giới hạn kích thước frame 30KB
- **Reconnect Logic**: Tự động reconnect khi mất kết nối

### 5. Chạy tự động với Systemd (Production)

Tạo file service `/etc/systemd/system/attendai.service`:

```ini
[Unit]
Description=AttendAI IoT Backend Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/IOT_ESP32_CAM/python_backend
Environment="PUBLIC_HOST=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
Environment="PORT=3000"
ExecStart=/home/ubuntu/IOT_ESP32_CAM/python_backend/venv/bin/python websockets_stream.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Kích hoạt service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable attendai
sudo systemctl start attendai
sudo systemctl status attendai
```

### 6. Truy cập hệ thống

- **Trang điểm danh**: `http://YOUR_EC2_PUBLIC_IP:3000/attendance`
- **Trang quản trị**: `http://YOUR_EC2_PUBLIC_IP:3000/admin/login`
  - Username: `admin`
  - Password: `abc@123`

### 7. Giám sát hiệu năng AWS

#### CloudWatch Metrics:
- CPU Utilization (giữ dưới 70%)
- Network In/Out
- Memory Usage

#### Logs:
```bash
# Xem logs backend
sudo journalctl -u attendai -f

# Xem real-time logs
tail -f /home/ubuntu/IOT_ESP32_CAM/python_backend/server.log
```

### 8. Tối ưu hóa bổ sung cho AWS

#### Load Balancer (nhiều camera):
```bash
# Sử dụng Application Load Balancer với WebSocket support
# Health check path: /api/attendance/heartbeat
# Port: 3000
```

#### Auto Scaling:
- Scale out khi CPU > 80% trong 5 phút
- Scale in khi CPU < 30% trong 15 phút

#### CDN (CloudFront):
- Cache static assets (HTML, CSS, JS)
- Giảm tải cho EC2 instance

### 9. Khắc phục sự cố thường gặp

#### Lag/Độ trễ cao:
1. Giảm FPS trong ESP32 code (TARGET_FPS=5)
2. Tăng SKIP_FRAME_RATIO trong backend (SKIP_FRAME_RATIO=3)
3. Kiểm tra bandwidth mạng giữa ESP32 và AWS

#### Mất kết nối WebSocket:
1. Kiểm tra Security Group (mở port 3000)
2. Kiểm tra route table và internet gateway
3. Tăng timeout trong ESP32 code

#### Hiệu năng CPU cao:
1. Giảm MAX_WORKERS xuống 1
2. Tăng SKIP_FRAME_RATIO lên 3
3. Nâng cấp EC2 instance type

### 10. Benchmark hiệu năng

| Cấu hình | FPS | CPU Usage | Memory | Latency |
|----------|-----|-----------|--------|---------|
| t3.micro | 5-8 | 60-80% | 1GB | 200-500ms |
| t3.medium | 10-15 | 40-60% | 2GB | 100-300ms |
| t3.large | 15-20 | 30-50% | 4GB | 50-200ms |

### 11. Liên hệ và hỗ trợ

- **GitHub**: https://github.com/ZINNODNTU/IOT_ESP32_CAM
- **Tài liệu**: Xem thư mục `docs/`
- **Issue**: Mở issue trên GitHub repository

---

**Lưu ý**: Hệ thống đã được tối ưu hóa cho môi trường AWS với các cải tiến giảm lag đáng kể. Đảm bảo cấu hình đúng ESP32 và backend để đạt hiệu năng tốt nhất.