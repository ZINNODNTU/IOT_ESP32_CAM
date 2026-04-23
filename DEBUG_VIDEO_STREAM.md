# 🔍 Debug Guide - Không Hiển Thị Video

## Vấn Đề Hiện Tại
- ESP32 đã kết nối WebSocket ✅
- Server nhận frames ✅  
- Nhưng `/video_feed/esp32cam_01` bị timeout ❌

## 🔧 Các Bước Debug

### Bước 1: Restart Server với Logging Mới

```bash
cd python_backend
python websockets_stream.py
```

Bạn sẽ thấy logs chi tiết hơn:
- `🎥 Stream request for device: esp32cam_01`
- `✅ Found device: esp32cam_01, outputFrame: True/False`
- `🎬 Starting stream for esp32cam_01`

### Bước 2: Kiểm Tra outputFrame

Khi server nhận frame, kiểm tra xem có log này không:
```
📦 Frame #20 from esp32cam_01: 5768 bytes, shape: (240, 320, 3)
```

**Nếu KHÔNG có log này** → ESP32 không gửi frame
**Nếu CÓ log này** → Tiếp tục bước 3

### Bước 3: Test Trực Tiếp Video Feed

Mở browser và truy cập:
```
http://103.249.21.75:3000/video_feed/esp32cam_01
```

Xem server logs:
- `🎥 Stream request for device: esp32cam_01` → Request đã đến
- `✅ Found device: esp32cam_01, outputFrame: True` → Device tìm thấy
- `🎬 Starting stream for esp32cam_01` → Bắt đầu stream
- `📺 Streamed 30 frames to esp32cam_01` → Đang stream

**Nếu thấy `outputFrame: False`** → Vấn đề ở `quick_encode_frame()`

### Bước 4: Kiểm Tra Firewall/Security Group

```bash
# Trên server, kiểm tra port 3000 đang listen
sudo netstat -tulpn | grep 3000

# Kết quả mong đợi:
tcp  0  0.0.0.0:3000  0.0.0.0:*  LISTEN  12345/python
```

**Kiểm tra AWS Security Group**:
- Inbound rule cho port 3000 phải mở cho `0.0.0.0/0` (hoặc IP của bạn)

### Bước 5: Test Từ Server Local

SSH vào server và test:
```bash
curl -v http://localhost:3000/video_feed/esp32cam_01
```

Nếu thành công từ localhost nhưng fail từ bên ngoài → Vấn đề firewall

### Bước 6: Kiểm Tra Browser Console

Mở DevTools (F12) → Console tab, xem lỗi chi tiết:
```
Failed to load resource: net::ERR_CONNECTION_TIMED_OUT
```

Thử:
```
Failed to load resource: net::ERR_CONNECTION_REFUSED  → Server không chạy
Failed to load resource: net::ERR_CONNECTION_TIMED_OUT → Firewall block
```

## 🐛 Các Vấn Đề Thường Gặp

### 1. outputFrame = None

**Nguyên nhân**: `quick_encode_frame()` không được gọi hoặc lỗi

**Giải pháp**: Thêm debug log vào `quick_encode_frame()`:

```python
def quick_encode_frame(self, frame):
    print(f"🔄 Encoding frame for {self.id}, shape: {frame.shape}")
    try:
        if self.application.camera_rotation_deg != 0:
            frame = rotate_by_degree(frame, self.application.camera_rotation_deg)
        
        ok, encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if ok:
            self.outputFrame = encoded.tobytes()
            print(f"✅ Frame encoded: {len(self.outputFrame)} bytes")
        else:
            print(f"❌ Frame encode failed")
    except Exception as e:
        print(f"⚠️ Quick encode error: {e}")
```

### 2. Connection Timeout

**Nguyên nhân**: Firewall hoặc Security Group

**Giải pháp**:
```bash
# Kiểm tra UFW (nếu có)
sudo ufw status

# Nếu active, cho phép port 3000
sudo ufw allow 3000/tcp
```

**AWS Security Group**: Đảm bảo có rule:
```
Type: Custom TCP
Port: 3000
Source: 0.0.0.0/0 (hoặc IP của bạn)
```

### 3. Server Bind Sai IP

**Kiểm tra**: Server có bind đúng `0.0.0.0` không?

Trong logs khởi động phải thấy:
```
🚀 Server bind: 0.0.0.0:3000
```

**KHÔNG phải**:
```
🚀 Server bind: 127.0.0.1:3000  ← SAI!
```

### 4. ESP32 Gửi Frame Nhưng Server Không Xử Lý

**Kiểm tra**: Có log `📦 Frame #...` không?

**Nếu KHÔNG** → Vấn đề ở `on_message()`:
- Message không phải binary
- Decode lỗi
- Exception bị bỏ qua

## 📋 Checklist Debug

```
[ ] Server đang chạy (python websockets_stream.py)
[ ] ESP32 đã kết nối (✅ Device connected: esp32cam_01)
[ ] Server nhận frames (📦 Frame #20 from esp32cam_01)
[ ] outputFrame được tạo (✅ Frame encoded: 5768 bytes)
[ ] Port 3000 đang listen (netstat -tulpn | grep 3000)
[ ] Firewall/Security Group mở port 3000
[ ] Browser có thể truy cập http://IP:3000/attendance
[ ] Video feed URL đúng: /video_feed/esp32cam_01
```

## 🔬 Test Commands

```bash
# 1. Kiểm tra server đang chạy
ps aux | grep python

# 2. Kiểm tra port
sudo netstat -tulpn | grep 3000

# 3. Test từ localhost
curl -I http://localhost:3000/attendance

# 4. Test video feed từ localhost
curl -v http://localhost:3000/video_feed/esp32cam_01

# 5. Kiểm tra firewall
sudo iptables -L -n | grep 3000

# 6. Test từ máy khác
telnet 103.249.21.75 3000
```

## 💡 Giải Pháp Nhanh

Nếu vẫn không được, thử restart toàn bộ:

```bash
# 1. Stop server
pkill -f websockets_stream.py

# 2. Restart server
cd ~/attendai/python_backend
python websockets_stream.py

# 3. Reset ESP32 (nhấn nút Reset)

# 4. Đợi 10 giây

# 5. Refresh browser
```

## 📞 Cần Hỗ Trợ?

Gửi cho tôi:
1. Server logs (50 dòng cuối)
2. Browser console errors
3. Output của: `netstat -tulpn | grep 3000`
4. AWS Security Group rules screenshot

---

**Lưu ý**: Sau mỗi thay đổi code, PHẢI restart server Python!
