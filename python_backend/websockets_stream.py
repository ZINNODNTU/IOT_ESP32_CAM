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
import requests
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


# ✅ LẤY PUBLIC IP
def get_public_ip():
    try:
        return requests.get("https://api.ipify.org").text
    except:
        return "localhost"


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def sanitize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip())[:128]


def to_ascii_label(text: str) -> str:
    safe = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").strip()
    return safe or "Unknown"


def sanitize_person_id(person_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", person_id.strip())[:64]


def ensure_csv_file(path: str, headers: List[str]):
    if not os.path.exists(path):
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            csv.DictWriter(f, fieldnames=headers).writeheader()


def append_csv_row(path: str, headers: List[str], row: Dict[str, str]):
    ensure_csv_file(path, headers)
    with open(path, "a", newline="", encoding="utf-8-sig") as f:
        csv.DictWriter(f, fieldnames=headers).writerow(row)


def read_csv_rows(path: str, limit: int = 200):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return rows[-limit:][::-1]


def extract_largest_face(image, detector):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = detector.detectMultiScale(gray, 1.1, 5)
    if len(faces) == 0:
        return None, None
    x, y, w, h = max(faces, key=lambda f: f[2]*f[3])
    return image[y:y+h, x:x+w], [x, y, w, h]


def normalize_face(face):
    gray = cv2.resize(cv2.cvtColor(face, cv2.COLOR_BGR2GRAY), (128, 128))
    vec = gray.astype("float32").flatten()
    return vec / (np.linalg.norm(vec) + 1e-6)


def cosine_similarity(a, b):
    return float(np.dot(a, b))


def load_known_faces(detector):
    data = []
    os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
    for f in os.listdir(KNOWN_FACES_DIR):
        img = cv2.imread(os.path.join(KNOWN_FACES_DIR, f))
        if img is None:
            continue
        face, _ = extract_largest_face(img, detector)
        if face is None:
            continue
        pid = f.split("__")[0]
        data.append((pid, pid, normalize_face(face)))
    return data


class WSHandler(tornado.websocket.WebSocketHandler):
    def initialize(self):
        self.frame = None
        self.outputFrame = None
        self.id = None
        self.executor = tornado.concurrent.futures.ThreadPoolExecutor(2)

    def open(self):
        connectedDevices.add(self)

    def on_message(self, message):
        if self.id is None:
            self.id = message
            return
        self.frame = cv2.imdecode(np.frombuffer(message, np.uint8), cv2.IMREAD_COLOR)
        tornado.ioloop.IOLoop.current().run_in_executor(self.executor, self.process)

    def process(self):
        if self.frame is None:
            return
        frame = self.frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.application.face_detector.detectMultiScale(gray, 1.1, 5)

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x,y),(x+w,y+h),(0,255,0),2)

        _, enc = cv2.imencode(".jpg", frame)
        self.outputFrame = enc.tobytes()

    def on_close(self):
        connectedDevices.discard(self)

    def check_origin(self, origin):
        return True


class StreamHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self, slug):
        self.set_header("Content-Type","multipart/x-mixed-replace; boundary=frame")

        while True:
            for c in connectedDevices:
                if c.id == slug and c.outputFrame:
                    self.write(b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + c.outputFrame + b"\r\n")
                    yield self.flush()
            yield tornado.gen.sleep(0.03)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Server running OK 🚀")


app = tornado.web.Application([
    (r"/ws", WSHandler),
    (r"/video_feed/(.*)", StreamHandler),
    (r"/", MainHandler),
])


if __name__ == "__main__":
    PORT = 3000
    PUBLIC_IP = get_public_ip()

    app.face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    server = tornado.httpserver.HTTPServer(app)

    # 🔥 FIX QUAN TRỌNG
    server.listen(PORT, address="0.0.0.0")

    print(f"🚀 Server: http://{PUBLIC_IP}:{PORT}")

    tornado.ioloop.IOLoop.current().start()