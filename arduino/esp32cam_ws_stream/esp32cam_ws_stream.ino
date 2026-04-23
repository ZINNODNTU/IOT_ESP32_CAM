#include "esp_camera.h"
#include <WiFi.h>
#include <ArduinoWebsockets.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

using namespace websockets;

// ================= CẤU HÌNH WIFI =================
const char* ssid = "1";        // ⚠️ THAY BẰNG SSID WIFI
const char* password = "14022021i"; // ⚠️ THAY BẰNG MẬT KHẨU

// ================= CẤU HÌNH SERVER =================
// LOCAL: const char* ws_url = "ws://192.168.x.x:3000/ws";
// AWS: const char* ws_url = "ws://YOUR_AWS_IP:3000/ws";
const char* ws_url = "ws://192.168.5.183:3000/ws";

// ================= CẤU HÌNH CAMERA =================
#define DEVICE_ID "esp32cam_01"  // ID duy nhất cho mỗi camera

// ================= TỐI ƯU HIỆU NĂNG =================
#define MAX_FRAME_SIZE 10000     // 10KB - giảm để ổn định mạng
#define BASE_FPS 5               // FPS cơ bản
#define MAX_RETRY 5              // Số lần retry tối đa
#define RECONNECT_DELAY 5000     // 5 giây

// ================= CAMERA PIN (AI-Thinker) =================
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// ================= BIẾN TOÀN CỤC =================
WebsocketsClient client;

unsigned long lastFrameTime = 0;
unsigned long lastReconnect = 0;
int retryCount = 0;
int currentFPS = BASE_FPS;
unsigned long frameCount = 0;

// ================= KHỞI TẠO CAMERA =================
bool initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;

  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;

  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;

  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;

  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;

  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  // Cấu hình tối ưu cho mạng ổn định
  if (psramFound()) {
    config.frame_size = FRAMESIZE_QVGA;   // 320x240 - cân bằng chất lượng/tốc độ
    config.jpeg_quality = 22;             // Chất lượng vừa phải
    config.fb_count = 2;                  // 2 frame buffers - quan trọng!
  } else {
    config.frame_size = FRAMESIZE_QQVGA;  // 160x120 - fallback
    config.jpeg_quality = 25;
    config.fb_count = 1;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("❌ Camera init failed: 0x%x\n", err);
    return false;
  }

  Serial.println("✅ Camera initialized");
  return true;
}

// ================= KẾT NỐI WIFI =================
void connectWiFi() {
  WiFi.begin(ssid, password);
  WiFi.setAutoReconnect(true);
  WiFi.persistent(true);

  Serial.print("🔌 Connecting WiFi");
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 40) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi connected");
    Serial.print("📍 IP: ");
    Serial.println(WiFi.localIP());
    Serial.print("📶 RSSI: ");
    Serial.println(WiFi.RSSI());
  } else {
    Serial.println("\n❌ WiFi failed");
    ESP.restart();
  }
}

// ================= KẾT NỐI WEBSOCKET =================
bool connectWS() {
  Serial.println("🔗 Connecting WebSocket...");

  if (client.connect(ws_url)) {
    // Gửi device ID ngay sau khi kết nối
    client.send(DEVICE_ID);
    retryCount = 0;
    Serial.println("✅ WebSocket connected");
    Serial.printf("📱 Device ID: %s\n", DEVICE_ID);
    return true;
  }

  Serial.println("❌ WebSocket failed");
  return false;
}

// ================= SETUP =================
void setup() {
  // Tắt brownout detector
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);
  
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n========================================");
  Serial.println("  ESP32-CAM AttendAI IoT");
  Serial.println("========================================");
  Serial.printf("Device ID: %s\n", DEVICE_ID);
  Serial.printf("PSRAM: %s\n", psramFound() ? "Yes" : "No");
  Serial.printf("Free Heap: %d bytes\n", ESP.getFreeHeap());
  Serial.println("========================================\n");

  // Khởi tạo camera
  if (!initCamera()) {
    Serial.println("❌ Camera init failed. Restarting...");
    delay(3000);
    ESP.restart();
  }

  // Kết nối WiFi
  connectWiFi();

  // Kết nối WebSocket
  if (!connectWS()) {
    Serial.println("⚠️ Initial WS connection failed, will retry...");
  }

  Serial.println("\n🚀 System ready!\n");
}

// ================= MAIN LOOP =================
void loop() {
  unsigned long now = millis();

  // ===== RECONNECT WEBSOCKET =====
  if (!client.available()) {
    if (now - lastReconnect > RECONNECT_DELAY) {
      lastReconnect = now;
      retryCount++;

      Serial.printf("🔄 Reconnecting... (attempt %d/%d)\n", retryCount, MAX_RETRY);

      if (retryCount > MAX_RETRY) {
        Serial.println("❌ Max retries reached. Restarting ESP32...");
        delay(2000);
        ESP.restart();
      }

      // Kiểm tra WiFi trước
      if (WiFi.status() != WL_CONNECTED) {
        Serial.println("⚠️ WiFi disconnected, reconnecting...");
        connectWiFi();
      }

      connectWS();
    }
    
    client.poll();
    delay(10);
    return;
  }

  // ===== FPS CONTROL =====
  unsigned long frameInterval = 1000 / currentFPS;
  if (now - lastFrameTime < frameInterval) {
    client.poll();
    delay(1);
    return;
  }

  // ===== CAPTURE FRAME =====
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("⚠️ Camera capture failed");
    delay(50);
    return;
  }

  // ===== VALIDATE FRAME SIZE =====
  if (fb->len > MAX_FRAME_SIZE) {
    Serial.printf("⚠️ Frame too large: %d bytes (max: %d)\n", fb->len, MAX_FRAME_SIZE);
    esp_camera_fb_return(fb);
    return;
  }

  // ===== VALIDATE JPEG =====
  if (fb->len < 2 || fb->buf[fb->len-2] != 0xFF || fb->buf[fb->len-1] != 0xD9) {
    Serial.println("⚠️ Invalid JPEG data");
    esp_camera_fb_return(fb);
    return;
  }

  // ===== SEND FRAME =====
  unsigned long sendStart = millis();
  bool sent = client.sendBinary((const char*)fb->buf, fb->len);
  unsigned long sendTime = millis() - sendStart;

  // Giải phóng frame buffer ngay
  int frameSize = fb->len;
  esp_camera_fb_return(fb);

  if (!sent) {
    Serial.println("❌ Failed to send frame");
    return;
  }

  frameCount++;

  // ===== ADAPTIVE FPS =====
  // Giảm FPS nếu gửi chậm, tăng FPS nếu gửi nhanh
  if (sendTime > 200 && currentFPS > 2) {
    currentFPS--;
    Serial.printf("⬇️ FPS decreased to %d (send time: %lums)\n", currentFPS, sendTime);
  } else if (sendTime < 100 && currentFPS < BASE_FPS) {
    currentFPS++;
    Serial.printf("⬆️ FPS increased to %d (send time: %lums)\n", currentFPS, sendTime);
  }

  // ===== LOGGING (mỗi 20 frames) =====
  if (frameCount % 20 == 0) {
    Serial.printf("📊 Frame #%lu | FPS: %d | Size: %d bytes | Send: %lums | Heap: %d\n",
                  frameCount, currentFPS, frameSize, sendTime, ESP.getFreeHeap());
  }

  lastFrameTime = now;

  // Poll để xử lý messages từ server
  client.poll();
  
  // Delay nhỏ để tránh watchdog timeout
  delay(5);
}
