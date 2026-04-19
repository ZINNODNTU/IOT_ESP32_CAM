import tornado.httpserver
import tornado.websocket
import tornado.concurrent
import tornado.ioloop
import tornado.web
import tornado.gen

import socket
import numpy as np
import imutils
import cv2
import os
import json
import re
import time
import threading
import csv
import unicodedata
from datetime import datetime
from typing import Dict, List, Tuple, Optional


connectedDevices = set()
KNOWN_FACES_DIR = "known_faces"
FACE_SIMILARITY_THRESHOLD = 0.86
REGISTRATION_CSV = "face_registrations.csv"
ATTENDANCE_CSV = "attendance_log.csv"

REGISTRATION_HEADERS = ["timestamp", "person_id", "person_name", "device_id", "image_file", "bbox"]
ATTENDANCE_HEADERS = ["timestamp", "date", "person_id", "person_name", "device_id", "score", "status", "mode"]

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "abc@123"


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def sanitize_name(name: str) -> str:
    clean = re.sub(r"\s+", " ", name.strip(), flags=re.UNICODE)
    return clean.strip()[:128]


def to_ascii_label(text: str) -> str:
    """OpenCV putText không hỗ trợ tiếng Việt, nên chuyển sang ASCII để tránh lỗi hiển thị trên frame."""
    safe = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").strip()
    return safe or "Unknown"


def sanitize_person_id(person_id: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_-]+", "_", person_id.strip())
    clean = clean.strip("_")
    return clean[:64]


def ensure_csv_file(path: str, headers: List[str]):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()


def append_csv_row(path: str, headers: List[str], row: Dict[str, str]):
    ensure_csv_file(path, headers)
    with open(path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writerow(row)


def read_csv_rows(path: str, limit: int = 200) -> List[Dict[str, str]]:
    if not os.path.exists(path):
        return []
    with open(path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if limit > 0:
        rows = rows[-limit:]
    rows.reverse()
    return rows


def rewrite_csv(path: str, headers: List[str], rows: List[Dict[str, str]]):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def clear_csv(path: str, headers: List[str]):
    rewrite_csv(path, headers, [])


def extract_largest_face(image_bgr: np.ndarray, detector: cv2.CascadeClassifier) -> Tuple[Optional[np.ndarray], Optional[List[int]]]:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
    if len(faces) == 0:
        return None, None
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    face = image_bgr[y:y + h, x:x + w]
    return face, [int(x), int(y), int(w), int(h)]


def normalize_face(face_bgr: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, (128, 128))
    gray = cv2.equalizeHist(gray)
    vec = gray.astype(np.float32).flatten()
    norm = np.linalg.norm(vec)
    return vec if norm < 1e-6 else vec / norm


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    return float(np.dot(vec1, vec2))


def load_known_faces(detector: cv2.CascadeClassifier) -> List[Tuple[str, str, np.ndarray]]:
    known_embeddings: List[Tuple[str, str, np.ndarray]] = []
    if not os.path.isdir(KNOWN_FACES_DIR):
        os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
        return known_embeddings

    registration_rows = read_csv_rows(REGISTRATION_CSV, 0)
    image_meta: Dict[str, Tuple[str, str]] = {}
    for row in registration_rows:
        image_file = (row.get("image_file") or "").strip()
        person_id = (row.get("person_id") or "").strip()
        person_name = (row.get("person_name") or "").strip()
        if image_file and person_id and person_name and image_file not in image_meta:
            image_meta[image_file] = (person_id, person_name)

    for filename in os.listdir(KNOWN_FACES_DIR):
        base_name, ext = os.path.splitext(filename)
        if ext.lower() not in (".jpg", ".jpeg", ".png", ".bmp", ".webp"):
            continue

        person_id, person_name = image_meta.get(filename, ("", ""))
        if not person_id:
            person_id = base_name.split("__", 1)[0].strip() if "__" in base_name else base_name.strip()
        if not person_name:
            person_name = person_id
        if not person_id:
            continue

        image_path = os.path.join(KNOWN_FACES_DIR, filename)
        image = cv2.imread(image_path)
        if image is None:
            continue

        face, _ = extract_largest_face(image, detector)
        if face is None:
            continue

        known_embeddings.append((person_id, person_name, normalize_face(face)))

    return known_embeddings


def reload_known_faces(app: tornado.web.Application):
    app.known_faces = load_known_faces(app.face_detector)
    summary: Dict[str, int] = {}
    for person_id, person_name, _ in app.known_faces:
        key = f"{person_id} - {person_name}"
        summary[key] = summary.get(key, 0) + 1
    app.known_face_summary = summary


def is_attendance_screen_active(app: tornado.web.Application) -> bool:
    return (time.time() - app.attendance_last_seen_ts) <= 10


def should_mark_attendance(app: tornado.web.Application, person_name: str, mode: str) -> bool:
    if person_name in ("", "Unknown"):
        return False
    if mode not in ("CHECK_IN", "CHECK_OUT"):
        return False
    return True


def mark_attendance(app: tornado.web.Application, person_id: str, person_name: str, device_id: str, score: float, mode: str) -> bool:
    if not should_mark_attendance(app, person_name, mode):
        return False

    with app.attendance_lock:
        key = f"{today_str()}::{person_id}::{mode}"
        if key in app.attendance_marked_today:
            return False

        append_csv_row(
            ATTENDANCE_CSV,
            ATTENDANCE_HEADERS,
            {
                "timestamp": now_iso(),
                "date": today_str(),
                "person_id": person_id,
                "person_name": person_name,
                "device_id": device_id or "unknown",
                "score": f"{score:.3f}",
                "status": "OK",
                "mode": mode,
            },
        )
        app.attendance_marked_today.add(key)
        return True


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user = self.get_secure_cookie("admin_user")
        return user.decode("utf-8") if user else None


def rotate_by_degree(frame: np.ndarray, degree: int) -> np.ndarray:
    d = int(degree) % 360
    if d == 0:
        return frame
    if d == 90:
        return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    if d == 180:
        return cv2.rotate(frame, cv2.ROTATE_180)
    if d == 270:
        return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return imutils.rotate_bound(frame, d)


class WSHandler(tornado.websocket.WebSocketHandler):
    def initialize(self):
        self.outputFrame = None
        self.frame = None
        self.id = None
        self.latestDetections = []
        self.executor = tornado.concurrent.futures.ThreadPoolExecutor(max_workers=4)

    def open(self):
        connectedDevices.add(self)
        print("🔌 New connection")

    def on_message(self, message):
        if self.id is None:
            self.id = message
            print("✅ Device connected:", self.id)
            return

        self.frame = cv2.imdecode(np.frombuffer(message, dtype=np.uint8), cv2.IMREAD_COLOR)
        tornado.ioloop.IOLoop.current().run_in_executor(self.executor, self.process_frames)

    def process_frames(self):
        if self.frame is None:
            return

        frame = rotate_by_degree(self.frame.copy(), self.application.camera_rotation_deg)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.application.face_detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(40, 40),
        )

        with self.application.known_faces_lock:
            known_faces = list(self.application.known_faces)

        attendance_mode = self.application.attendance_mode
        screen_active = is_attendance_screen_active(self.application)

        detections = []
        for (x, y, w, h) in faces:
            face_roi = frame[y:y + h, x:x + w]
            emb = normalize_face(face_roi)

            best_name = "Unknown"
            best_score = -1.0
            best_person_id = ""
            best_person_name = "Unknown"
            for person_id, person_name, known_emb in known_faces:
                score = cosine_similarity(emb, known_emb)
                if score > best_score:
                    best_score = score
                    best_person_id = person_id
                    best_person_name = person_name

            if best_score < FACE_SIMILARITY_THRESHOLD:
                best_person_id = ""
                best_person_name = "Unknown"

            attendance_marked = False
            if screen_active and best_person_name != "Unknown":
                attendance_marked = mark_attendance(
                    self.application,
                    best_person_id,
                    best_person_name,
                    self.id or "",
                    best_score,
                    attendance_mode,
                )

            color = (0, 200, 0) if best_person_name != "Unknown" else (0, 165, 255)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            mark_label = f" [{attendance_mode}]" if attendance_marked else ""
            # Ghi chú: tên tiếng Việt đầy đủ sẽ hiển thị ở frontend JSON;
            # OpenCV trên frame chỉ vẽ nhãn ASCII để không bị lỗi font.
            frame_label_name = to_ascii_label(best_person_name)
            label = f"{frame_label_name} ({best_score:.2f}){mark_label}"
            cv2.putText(
                frame,
                label,
                (x, y - 8 if y > 20 else y + h + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                2,
            )

            detections.append(
                {
                    "person_id": best_person_id,
                    "person_name": best_person_name,
                    "name": best_person_name,
                    "score": round(best_score, 3),
                    "bbox": [int(x), int(y), int(w), int(h)],
                    "attendance_marked": attendance_marked,
                    "mode": attendance_mode,
                    "screen_active": screen_active,
                }
            )

        self.latestDetections = detections

        ok, encoded = cv2.imencode(".jpg", frame)
        if ok:
            self.outputFrame = encoded.tobytes()

    def on_close(self):
        connectedDevices.discard(self)
        print("❌ Connection closed:", self.id)

    def check_origin(self, origin):
        return True


class StreamHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self, slug):
        self.set_header("Cache-Control", "no-store")
        self.set_header("Content-Type", "multipart/x-mixed-replace;boundary=frame")

        client = None
        for c in connectedDevices:
            if c.id == slug:
                client = c
                break

        if client is None:
            self.write("❌ Device not found")
            return

        while True:
            if client.outputFrame is None:
                yield tornado.gen.sleep(0.1)
                continue

            self.write(b"--frame\r\n")
            self.write(b"Content-Type: image/jpeg\r\n\r\n")
            self.write(client.outputFrame)
            self.write(b"\r\n")
            yield self.flush()
            yield tornado.gen.sleep(0.03)


class FaceStatusHandler(tornado.web.RequestHandler):
    def get(self):
        data = {}
        for d in connectedDevices:
            if d.id:
                data[d.id] = d.latestDetections
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps(data, ensure_ascii=False))


class AttendanceConfigHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(
            json.dumps(
                {
                    "mode": self.application.attendance_mode,
                    "screen_active": is_attendance_screen_active(self.application),
                    "camera_rotation_deg": self.application.camera_rotation_deg,
                },
                ensure_ascii=False,
            )
        )

    def post(self):
        try:
            payload = json.loads(self.request.body.decode("utf-8"))
        except Exception:
            payload = {}

        mode = (payload.get("mode") or self.application.attendance_mode).upper().strip()
        if mode not in ("CHECK_IN", "CHECK_OUT"):
            self.set_status(400)
            self.write({"ok": False, "message": "mode phải là CHECK_IN hoặc CHECK_OUT"})
            return

        rotation = payload.get("camera_rotation_deg", self.application.camera_rotation_deg)
        try:
            rotation = int(rotation) % 360
        except Exception:
            self.set_status(400)
            self.write({"ok": False, "message": "camera_rotation_deg không hợp lệ"})
            return

        if rotation not in (0, 90, 180, 270):
            self.set_status(400)
            self.write({"ok": False, "message": "camera_rotation_deg chỉ hỗ trợ 0, 90, 180, 270"})
            return

        self.application.attendance_mode = mode
        self.application.camera_rotation_deg = rotation
        self.application.attendance_last_seen_ts = time.time()
        self.write({"ok": True, "mode": mode, "camera_rotation_deg": rotation})


class AttendanceHeartbeatHandler(tornado.web.RequestHandler):
    def post(self):
        self.application.attendance_last_seen_ts = time.time()
        self.write({"ok": True, "ts": self.application.attendance_last_seen_ts})


class AttendanceLogHandler(tornado.web.RequestHandler):
    def get(self):
        try:
            limit = int(self.get_argument("limit", "200"))
        except ValueError:
            limit = 200

        rows = read_csv_rows(ATTENDANCE_CSV, limit)
        today = today_str()
        today_rows = [r for r in rows if r.get("date") == today]
        today_unique = len({f"{r.get('person_id')}::{r.get('mode')}" for r in today_rows if r.get("person_id")})

        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"rows": rows, "today": today, "today_count": today_unique}, ensure_ascii=False))


class KnownFacesHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        with self.application.known_faces_lock:
            summary = dict(self.application.known_face_summary)
        rows = read_csv_rows(REGISTRATION_CSV, 200)
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"people": summary, "rows": rows}, ensure_ascii=False))


class RegisterFaceHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        try:
            payload = json.loads(self.request.body.decode("utf-8"))
        except Exception:
            self.set_status(400)
            self.write({"ok": False, "message": "Payload không hợp lệ"})
            return

        raw_person_id = (payload.get("person_id") or "").strip()
        raw_name = (payload.get("person_name") or payload.get("name") or "").strip()
        device_id = (payload.get("device_id") or "").strip()

        if not raw_person_id or not raw_name or not device_id:
            self.set_status(400)
            self.write({"ok": False, "message": "Thiếu person_id, person_name hoặc device_id"})
            return

        safe_person_id = sanitize_person_id(raw_person_id)
        safe_name = sanitize_name(raw_name)
        if not safe_person_id or not safe_name:
            self.set_status(400)
            self.write({"ok": False, "message": "person_id hoặc person_name không hợp lệ"})
            return

        client = None
        for c in connectedDevices:
            if c.id == device_id:
                client = c
                break

        if client is None:
            self.set_status(404)
            self.write({"ok": False, "message": "Không tìm thấy thiết bị"})
            return

        if client.frame is None:
            self.set_status(400)
            self.write({"ok": False, "message": "Thiết bị chưa gửi frame"})
            return

        frame = rotate_by_degree(client.frame.copy(), self.application.camera_rotation_deg)
        face, bbox = extract_largest_face(frame, self.application.face_detector)
        if face is None:
            self.set_status(400)
            self.write({"ok": False, "message": "Không phát hiện khuôn mặt trong frame hiện tại"})
            return

        os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
        timestamp = int(time.time() * 1000)
        filename = f"{safe_person_id}__{timestamp}.jpg"
        save_path = os.path.join(KNOWN_FACES_DIR, filename)
        if not cv2.imwrite(save_path, face):
            self.set_status(500)
            self.write({"ok": False, "message": "Không thể lưu ảnh khuôn mặt"})
            return

        append_csv_row(
            REGISTRATION_CSV,
            REGISTRATION_HEADERS,
            {
                "timestamp": now_iso(),
                "person_id": safe_person_id,
                "person_name": safe_name,
                "device_id": device_id,
                "image_file": filename,
                "bbox": ",".join(map(str, bbox or [])),
            },
        )

        with self.application.known_faces_lock:
            reload_known_faces(self.application)

        self.write({"ok": True, "message": f"Đã đăng ký khuôn mặt cho {safe_name}", "saved_file": filename})


class DeleteRegistrationHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        try:
            payload = json.loads(self.request.body.decode("utf-8"))
        except Exception:
            payload = {}

        image_file = (payload.get("image_file") or "").strip()
        if not image_file:
            self.set_status(400)
            self.write({"ok": False, "message": "Thiếu image_file"})
            return

        rows = read_csv_rows(REGISTRATION_CSV, 0)
        rows = list(reversed(rows))
        filtered = [r for r in rows if (r.get("image_file") or "") != image_file]
        rewrite_csv(REGISTRATION_CSV, REGISTRATION_HEADERS, filtered)

        file_path = os.path.join(KNOWN_FACES_DIR, image_file)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

        with self.application.known_faces_lock:
            reload_known_faces(self.application)

        self.write({"ok": True, "message": "Đã xóa bản ghi đăng ký"})


class DeleteAllRegistrationsHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        clear_csv(REGISTRATION_CSV, REGISTRATION_HEADERS)
        if os.path.isdir(KNOWN_FACES_DIR):
            for filename in os.listdir(KNOWN_FACES_DIR):
                path = os.path.join(KNOWN_FACES_DIR, filename)
                if os.path.isfile(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass

        with self.application.known_faces_lock:
            reload_known_faces(self.application)

        self.write({"ok": True, "message": "Đã xóa toàn bộ dữ liệu đăng ký"})


class DeleteAttendanceHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        clear_csv(ATTENDANCE_CSV, ATTENDANCE_HEADERS)
        with self.application.attendance_lock:
            self.application.attendance_marked_today = set()
        self.write({"ok": True, "message": "Đã xóa toàn bộ dữ liệu điểm danh"})


class AdminLoginHandler(BaseHandler):
    def get(self):
        self.render("admin_login.html", error="")

    def post(self):
        username = self.get_body_argument("username", "").strip()
        password = self.get_body_argument("password", "").strip()

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            self.set_secure_cookie("admin_user", ADMIN_USERNAME, httponly=True)
            self.redirect("/admin/register")
            return

        self.render("admin_login.html", error="Sai tài khoản hoặc mật khẩu")


class AdminLogoutHandler(BaseHandler):
    def post(self):
        self.clear_cookie("admin_user")
        self.redirect("/admin/login")


class AttendancePageHandler(BaseHandler):
    def get(self):
        ip = get_local_ip()
        device_ids = [d.id for d in connectedDevices if d.id]
        self.render(
            "attendance.html",
            title="Điểm danh khuôn mặt",
            ip=ip,
            deviceIds=device_ids,
            streamBaseUrl=f"http://{ip}:3000/video_feed/",
        )


class AdminRegisterPageHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        ip = get_local_ip()
        device_ids = [d.id for d in connectedDevices if d.id]
        self.render(
            "admin_register.html",
            title="Quản trị đăng ký khuôn mặt",
            ip=ip,
            deviceIds=device_ids,
            streamBaseUrl=f"http://{ip}:3000/video_feed/",
            admin_user=self.current_user,
        )


class RootHandler(tornado.web.RequestHandler):
    def get(self):
        self.redirect("/attendance")


application = tornado.web.Application(
    [
        (r"/video_feed/([^/]+)", StreamHandler),
        (r"/ws", WSHandler),

        (r"/api/faces", FaceStatusHandler),
        (r"/api/attendance/config", AttendanceConfigHandler),
        (r"/api/attendance/heartbeat", AttendanceHeartbeatHandler),
        (r"/api/attendance", AttendanceLogHandler),

        (r"/api/admin/known_faces", KnownFacesHandler),
        (r"/api/admin/register_face", RegisterFaceHandler),
        (r"/api/admin/delete_registration", DeleteRegistrationHandler),
        (r"/api/admin/delete_all_registrations", DeleteAllRegistrationsHandler),
        (r"/api/admin/delete_all_attendance", DeleteAttendanceHandler),

        (r"/admin/login", AdminLoginHandler),
        (r"/admin/logout", AdminLogoutHandler),
        (r"/admin/register", AdminRegisterPageHandler),

        (r"/attendance", AttendancePageHandler),
        (r"/", RootHandler),
    ],
    template_path="templates",
    login_url="/admin/login",
    cookie_secret="esp32-face-attendance-secret-2026",
)


if __name__ == "__main__":
    PORT = 3000
    ip = get_local_ip()

    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    application.face_detector = cv2.CascadeClassifier(cascade_path)
    application.known_faces_lock = threading.Lock()

    application.attendance_lock = threading.Lock()
    application.attendance_mode = "CHECK_IN"
    application.attendance_last_seen_ts = 0.0
    application.attendance_marked_today = set()
    # Mặc định không xoay; người dùng có thể xoay 0/90/180/270 từ giao diện web.
    application.camera_rotation_deg = 0

    os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
    ensure_csv_file(REGISTRATION_CSV, REGISTRATION_HEADERS)
    ensure_csv_file(ATTENDANCE_CSV, ATTENDANCE_HEADERS)

    with application.known_faces_lock:
        reload_known_faces(application)

    print(f"🧠 Loaded known face samples: {len(application.known_faces)}")
    print("🔐 Admin login: admin / abc@123")

    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(PORT)

    print(f"🚀 Server: http://{ip}:{PORT}")
    print(f"📋 Attendance page: http://{ip}:{PORT}/attendance")
    print(f"🛠️ Admin page: http://{ip}:{PORT}/admin/login")

    tornado.ioloop.IOLoop.current().start()