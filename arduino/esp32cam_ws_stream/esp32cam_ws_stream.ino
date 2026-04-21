#include "esp_camera.h"
#include <WiFi.h>
#include <ArduinoWebsockets.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

using namespace websockets;

// ================= CẤU HÌNH WIFI =================
const char* ssid = "1";               // Thay bằng SSID WiFi thực tế
const char* password = "14022021i";    // Thay bằng mật khẩu WiFi

// ================= CẤU HÌNH SERVER =================
// CHO LOCAL TESTING (PC Windows):
// const char* ws_url = "ws://192.168.5.183:3000/ws";

// CHO AWS SERVER:
const char* ws_url = "ws://13.239.29.180:3000/ws";

// ================= CẤU HÌNH CAMERA =================
#define DEVICE_ID "esp32cam_01"

// Camera pin configuration (AI Thinker)
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

// ================= CẤU HÌNH TỐI ƯU CHO MẠNG ỔN ĐỊNH =================
#define MAX_FRAME_SIZE 15000           // Giảm kích thước frame (15KB)
#define TARGET_FPS 5                   // Giảm FPS để ổn định mạng (từ 8 xuống 5)
#define RECONNECT_DELAY_MS 5000       // Thời gian chờ reconnect
#define MAX_RETRY_COUNT 5              // Số lần retry tối đa
#define RETRY_BACKOFF_MS 1000          // Exponential backoff
#define WATCHDOG_TIMEOUT_MS 30000      // Watchdog timeout 30s

// ================= BIẾN TOÀN CỤC =================
WebsocketsClient client;
unsigned long lastConnectionAttempt = 0;
int retryCount = 0;
unsigned long lastWatchdogCheck = 0;
bool cameraInitialized = false;

// ================= UTILITY FUNCTIONS =================
int max(int a, int b) {
  return (a > b) ? a : b;
}

void printSystemInfo() {
  Serial.println("\n=== SYSTEM INFO ===");
  Serial.printf("Free Heap: %d bytes\n", ESP.getFreeHeap());
  Serial.printf("PSRAM: %s\n", psramFound() ? "Yes" : "No");
  Serial.printf("Chip Revision: %d\n", ESP.getChipRevision());
  Serial.printf("CPU Freq: %d MHz\n", ESP.getCpuFreqMHz());
  Serial.println("===================\n");
}

// ================= CAMERA INIT =================
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

  // GIẢM TẢI ĐỂ TRÁNH FB-OVF VÀ ỔN ĐỊNH MẠNG
  if (psramFound()) {
    config.frame_size = FRAMESIZE_QVGA;    // Giảm từ VGA xuống QVGA (320x240)
    config.jpeg_quality = 18;             // Giảm chất lượng (từ 12 lên 18)
    config.fb_count = 1;                   // Giảm từ 2 xuống 1 frame buffer
  } else {
    config.frame_size = FRAMESIZE_QQVGA;   // Rất nhỏ (160x120)
    config.jpeg_quality = 20;              // Chất lượng thấp
    config.fb_count = 1;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed: 0x%x\n", err);
    return false;
  }

  Serial.println("Camera initialized successfully");
  cameraInitialized = true;
  return true;
}

// ================= WIFI CONNECTION =================
bool connectWiFi() {
  Serial.print("Connecting to WiFi");
  
  WiFi.begin(ssid, password);
  unsigned long startTime = millis();
  const unsigned long timeout = 20000; // 20 seconds timeout
  
  while (WiFi.status() != WL_CONNECTED) {
    if (millis() - startTime > timeout) {
      Serial.println("\nWiFi connection timeout");
      return false;
    }
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWiFi connected");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
  Serial.print("RSSI: ");
  Serial.println(WiFi.RSSI());
  
  return true;
}

// ================= WEBSOCKET CONNECTION =================
bool connectWebSocket() {
  Serial.println("Connecting to WebSocket...");
  
  // Set timeout cho WebSocket
  client.setConnectionTimeout(10, 5000); // 10s connection timeout
  
  bool connected = client.connect(ws_url);
  
  if (connected) {
    Serial.println("WebSocket connected");
    
    // Gửi device ID
    client.send(DEVICE_ID);
    
    // Reset retry count khi kết nối thành công
    retryCount = 0;
    return true;
  } else {
    Serial.println("WebSocket connection failed");
    return false;
  }
}

// ================= WATCHDOG =================
void checkWatchdog() {
  unsigned long currentTime = millis();
  
  if (currentTime - lastWatchdogCheck > WATCHDOG_TIMEOUT_MS) {
    Serial.println("Watchdog timeout - Restarting ESP32");
    ESP.restart();
  }
  
  // Update watchdog nếu có activity
  if (client.available() || WiFi.status() == WL_CONNECTED) {
    lastWatchdogCheck = currentTime;
  }
}

// ================= SETUP =================
void setup() {
  // Disable brownout detector
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);
  
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n=== ESP32-CAM STABLE NETWORK OPTIMIZATION ===");
  printSystemInfo();
  
  // Khởi tạo camera
  if (!initCamera()) {
    Serial.println("Camera initialization failed. Restarting in 5s...");
    delay(5000);
    ESP.restart();
  }
  
  // Kết nối WiFi với retry
  int wifiRetries = 0;
  while (!connectWiFi() && wifiRetries < 3) {
    wifiRetries++;
    Serial.printf("WiFi retry %d/3\n", wifiRetries);
    delay(2000);
  }
  
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Failed to connect to WiFi. Restarting...");
    ESP.restart();
  }
  
  // Kết nối WebSocket
  if (!connectWebSocket()) {
    Serial.println("Initial WebSocket connection failed");
  }
  
  lastWatchdogCheck = millis();
  lastConnectionAttempt = millis();
}

// ================= MAIN LOOP - TỐI ƯU CHO MẠNG ỔN ĐỊNH =================
void loop() {
  unsigned long currentTime = millis();
  
  // Kiểm tra watchdog
  checkWatchdog();
  
  // Kiểm tra và reconnect WebSocket nếu cần
  if (!client.available()) {
    if (currentTime - lastConnectionAttempt > RECONNECT_DELAY_MS) {
      Serial.println("WebSocket disconnected. Attempting to reconnect...");
      
      if (connectWebSocket()) {
        Serial.println("WebSocket reconnected successfully");
        lastConnectionAttempt = currentTime;
      } else {
        retryCount++;
        Serial.printf("Reconnect failed (attempt %d/%d)\n", retryCount, MAX_RETRY_COUNT);
        
        // Exponential backoff
        unsigned long backoffTime = RETRY_BACKOFF_MS * (1 << min(retryCount, 5));
        backoffTime = min(backoffTime, 30000UL); // Max 30 seconds
        
        if (retryCount >= MAX_RETRY_COUNT) {
          Serial.println("Max retries reached. Restarting ESP32...");
          delay(2000);
          ESP.restart();
        }
        
        lastConnectionAttempt = currentTime + backoffTime;
        return;
      }
    }
    
    // Poll để giữ kết nối
    client.poll();
    delay(10);
    return;
  }
  
  // Kiểm tra FPS - chỉ gửi frame khi đủ thời gian
  static unsigned long lastFrameTime = 0;
  if (currentTime - lastFrameTime < (1000 / TARGET_FPS)) {
    client.poll();
    delay(5);
    return;
  }
  
  // Chụp ảnh với error handling
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    delay(50);
    return;
  }
  
  // Kiểm tra kích thước frame
  if (fb->len > MAX_FRAME_SIZE) {
    Serial.printf("Frame too large: %d bytes (max: %d). Skipping.\n", fb->len, MAX_FRAME_SIZE);
    esp_camera_fb_return(fb);
    delay(10);
    return;
  }
  
  // Gửi frame với timeout
  unsigned long sendStart = millis();
  bool sent = client.sendBinary((const char*)fb->buf, fb->len);
  unsigned long sendTime = millis() - sendStart;
  
  if (!sent) {
    Serial.println("Failed to send frame. Connection may be broken.");
    esp_camera_fb_return(fb);
    delay(100);
    return;
  }
  
  // Log mỗi 10 frame để giảm spam serial
  static unsigned long framesSent = 0;
  framesSent++;
  if (framesSent % 10 == 0) {
    Serial.printf("Frame %d sent (%d bytes, %lu ms)\n", framesSent, fb->len, sendTime);
  }
  
  // Giải phóng frame buffer
  esp_camera_fb_return(fb);
  
  // Poll để xử lý message từ server
  client.poll();
  
  // Cập nhật thời gian frame cuối
  lastFrameTime = currentTime;
  
  // Điều chỉnh delay động dựa trên thời gian gửi
  int dynamicDelay = max(50, (1000 / TARGET_FPS) - (int)sendTime);
  delay(dynamicDelay);
}