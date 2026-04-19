# BAO CAO MON HOC

## De tai
He thong diem danh khuon mat su dung ESP32-CAM va Python WebSocket

## 1. Thong tin sinh vien
- Ho va ten: ........................................................
- MSSV: ............................................................
- Lop: .............................................................
- Nganh: Cong nghe thong tin
- Hoc phan: Cong nghe IoT va ung dung
- Giang vien huong dan: ............................................
- Thoi gian thuc hien: .............................................

## 2. Tom tat de tai
De tai xay dung he thong diem danh tu dong dua tren nhan dien khuon mat. Thiet bi ESP32-CAM thu nhan khung hinh va gui ve may chu Python thong qua giao thuc WebSocket. May chu su dung OpenCV de phat hien va so khop khuon mat, sau do ghi ket qua diem danh vao tep CSV theo che do CHECK_IN/CHECK_OUT. He thong co giao dien web cho quan tri dang ky khuon mat va giao dien diem danh thoi gian thuc.

## 3. Muc tieu va pham vi
### 3.1 Muc tieu
- Xay dung mo hinh diem danh thong minh chi phi thap, de trien khai trong phong hoc/phong lab.
- Ho tro quan ly du lieu khuon mat va lich su diem danh qua giao dien web.
- Dam bao he thong co the hoat dong realtime tren mang LAN.

### 3.2 Pham vi
- Su dung bo phat hien khuon mat Haar Cascade trong OpenCV.
- So khop khuon mat theo vector dac trung don gian (chuan hoa histogram + cosine similarity).
- Du lieu luu tru o muc file (thu muc anh + CSV), chua tich hop CSDL lon.
- He thong chay noi bo, chua trien khai cloud.

## 4. Co so ly thuyet
### 4.1 Tong quan IoT trong bai toan diem danh
Mo hinh IoT trong de tai gom 3 lop:
- Lop cam bien/biên (edge): ESP32-CAM thu anh khuon mat.
- Lop truyen thong: WiFi + WebSocket truyen frame JPEG ve server.
- Lop xu ly ung dung: Python Tornado + OpenCV + giao dien web.

### 4.2 Nguyen ly nhan dien trong he thong
- Phat hien khuon mat: Haar Cascade tren anh xam.
- Trich xuat dac trung: resize 128x128, can bang histogram, flatten vector va chuan hoa L2.
- Do tuong dong: cosine similarity.
- Nguong chap nhan: `FACE_SIMILARITY_THRESHOLD = 0.86`.

Neu diem tuong dong nho hon nguong, he thong gan nhan `Unknown`.

### 4.3 Co che diem danh
He thong chi ghi nhan diem danh khi:
- Giao dien attendance dang mo (co heartbeat).
- Nguoi duoc nhan dien khong phai `Unknown`.
- Che do hop le: CHECK_IN hoac CHECK_OUT.
- Chua diem danh trung lap trong ngay voi cung person_id va mode.

## 5. Phan tich va thiet ke he thong
### 5.1 Kien truc tong the
1. ESP32-CAM ket noi WiFi, mo ket noi WebSocket den server (`/ws`).
2. ESP32-CAM gui `DEVICE_ID` truoc, sau do gui frame JPEG lien tuc.
3. Backend Tornado nhan frame, xoay anh theo cau hinh, phat hien/nhan dien khuon mat.
4. Ket qua nhan dien hien thi tren stream va tra ve JSON API cho frontend.
5. Frontend hien thi camera, trang thai, lich su diem danh va trang quan tri.

### 5.2 Thanh phan chinh
- Firmware ESP32-CAM: `arduino/esp32cam_ws_stream/esp32cam_ws_stream.ino`
- Backend xu ly: `python_backend/websockets_stream.py`
- Giao dien diem danh: `python_backend/templates/attendance.html`
- Giao dien quan tri: `python_backend/templates/admin_login.html`, `python_backend/templates/admin_register.html`
- Du lieu luu tru:
  - `python_backend/known_faces/` (anh da dang ky)
  - `python_backend/face_registrations.csv`
  - `python_backend/attendance_log.csv`

### 5.3 API tieu bieu
- `GET /api/faces`: Trang thai nhan dien theo tung camera.
- `GET/POST /api/attendance/config`: Lay/cap nhat mode diem danh va goc camera.
- `POST /api/attendance/heartbeat`: Xac nhan man hinh diem danh dang mo.
- `GET /api/attendance`: Lay lich su diem danh.
- `POST /api/admin/register_face`: Dang ky khuon mat moi.
- `GET /api/admin/known_faces`: Danh sach nguoi mau va lich su dang ky.

## 6. Cai dat va trien khai
### 6.1 Moi truong
- Phan cung: ESP32-CAM AI Thinker.
- Ngon ngu:
  - Arduino C++ (firmware)
  - Python (backend)
  - HTML/CSS/JavaScript (frontend)
- Thu vien Python: Tornado, OpenCV, NumPy, imutils.

### 6.2 Cac buoc thuc hien
1. Nap firmware cho ESP32-CAM, cau hinh `ssid`, `password`, `ws_url`, `DEVICE_ID`.
2. Khoi dong backend Python tai cong `3000`.
3. Mo trang diem danh: `/attendance`.
4. Dang nhap quan tri tai `/admin/login` de dang ky khuon mat.
5. Kiem tra lich su diem danh va du lieu CSV.

## 7. Ket qua dat duoc
- He thong ket noi realtime giua ESP32-CAM va server thong qua WebSocket.
- Ho tro dang ky khuon mat truc tiep tu frame hien tai cua camera.
- Nhan dien va diem danh tu dong theo 2 che do CHECK_IN/CHECK_OUT.
- Co co che tranh diem danh trung lap theo ngay.
- Co giao dien quan tri va giao dien diem danh tach biet.

## 8. Danh gia
### 8.1 Uu diem
- Chi phi thap, de mo rong voi nhieu camera.
- Trien khai noi bo don gian, phu hop bai toan mon hoc.
- Luong xu ly ro rang, de bao tri va de nang cap.

### 8.2 Han che
- Do chinh xac phu thuoc chat luong anh, anh sang, goc mat.
- Chua su dung mo hinh deep learning chuyen sau (FaceNet/ArcFace).
- Dang dung tai khoan quan tri hard-code, can nang cap bao mat.
- Luu tru bang file CSV khong toi uu khi du lieu lon.

### 8.3 Huong phat trien
- Chuyen sang embedding deep learning de tang do chinh xac.
- Tich hop CSDL (MySQL/PostgreSQL) va phan quyen nguoi dung.
- Dong bo du lieu len cloud, bo sung dashboard thong ke.
- Bo sung anti-spoofing (chong dung anh/clip de gia mao).

## 9. Ket luan
De tai da dat muc tieu xay dung he thong diem danh khuon mat dua tren ESP32-CAM va Python backend. He thong dap ung duoc yeu cau co ban cua mon hoc IoT ung dung: ket noi thiet bi, xu ly du lieu thoi gian thuc, cung cap giao dien dieu khien va luu vet du lieu. Day la nen tang tot de tiep tuc nang cap thanh giai phap diem danh thuc te quy mo lon hon.

## 10. Tai lieu tham khao
1. OpenCV Documentation - https://docs.opencv.org/
2. Tornado Web Framework - https://www.tornadoweb.org/
3. ESP32-CAM (Espressif) Technical Docs - https://docs.espressif.com/
4. ArduinoWebsockets Library - https://github.com/gilmaimon/ArduinoWebsockets

## 11. Phu luc
### 11.1 Cau truc thu muc de tai
- `arduino/esp32cam_ws_stream/esp32cam_ws_stream.ino`
- `python_backend/websockets_stream.py`
- `python_backend/templates/attendance.html`
- `python_backend/templates/admin_login.html`
- `python_backend/templates/admin_register.html`
- `python_backend/known_faces/`
- `python_backend/face_registrations.csv`
- `python_backend/attendance_log.csv`

### 11.2 Tai khoan quan tri mac dinh (de test)
- Username: `admin`
- Password: `abc@123`

Luu y: Trong nop bai chinh thuc, can doi mat khau mac dinh va bo thong tin nhay cam.