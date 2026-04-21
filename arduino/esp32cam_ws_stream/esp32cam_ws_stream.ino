#include "esp_camera.h"
#include <WiFi.h>
#include <ArduinoWebsockets.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

using namespace websockets;

// ================= WIFI =================
// ⚠️ CẤU HÌNH WIFI CHO MÔI TRƯỜNG SẢN PHẨM
const char* ssid = "1";          // Thay bằng SSID WiFi thực tế
const char* password = "14022021i";   // Thay bằng mật khẩu WiFi

// ⚠️ SỬA IP SERVER AWS (Public IP hoặc Domain)
// Ví dụ: ws://your-ec2-public-ip:3000/ws hoặc wss://your-domain.com/ws
const char* ws_url = "ws://13.239.29.180:3000/ws";

// ⚠️ ID CAMERA - Đặt tên duy nhất cho mỗi camera
const char* DEVICE_ID = "esp32cam_01";

// Hàm utility
int max(int a, int b) {
  return (a > b) ? a : b;
}

// ================= CAMERA PIN (AI Thinker) =================
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

WebsocketsClient client;

// ================= CALLBACK =================
void onMessageCallback(WebsocketsMessage message) {
  Serial.print("📩 Server: ");
  Serial.println(message.data());
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

  if (psramFound()) {
    config.frame_size = FRAMESIZE_VGA;
    config.jpeg_quality = 12;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_QVGA;
    config.jpeg_quality = 15;
    config.fb_count = 1;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.println("❌ Camera init failed");
    return false;
  }

  Serial.println("✅ Camera OK");
  return true;
}

// ================= WIFI + WS =================
bool connectWiFi() {
  WiFi.begin(ssid, password);

  Serial.print("📶 Connecting WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n✅ WiFi connected");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  return true;
}

bool connectWebSocket() {
  client.onMessage(onMessageCallback);

  Serial.println("🔌 Connecting WebSocket...");
  bool connected = client.connect(ws_url);

  if (!connected) {
    Serial.println("❌ WS connect failed");
    return false;
  }

  Serial.println("✅ WebSocket Connected");

  // gửi ID
  client.send(DEVICE_ID);

  return true;
}

// ================= SETUP =================
void setup() {
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

  Serial.begin(115200);
  delay(1000);

  if (!initCamera()) {
    return;
  }

  connectWiFi();

  if (!connectWebSocket()) {
    Serial.println("Retry in 5s...");
    delay(5000);
    ESP.restart();
  }
}

// ================= CẤU HÌNH TỐI ƯU CHO AWS =================
#define MAX_FRAME_SIZE 20000  // Giảm kích thước frame tối đa (20KB)
#define TARGET_FPS 8          // Giảm FPS để giảm tải mạng (từ 10 xuống 8)
#define RECONNECT_DELAY 5000  // Thời gian chờ reconnect
#define SEND_TIMEOUT_MS 3000  // Giảm timeout khi gửi frame (5s -> 3s)
#define DYNAMIC_QUALITY       // Kích hoạt chất lượng động
#define MIN_JPEG_QUALITY 8    // Chất lượng JPEG tối thiểu
#define MAX_JPEG_QUALITY 15   // Chất lượng JPEG tối đa

// ================= LOOP TỐI ƯU =================
void loop() {
  static unsigned long lastFrameTime = 0;
  static unsigned long framesSent = 0;
  static int currentJpegQuality = 12;  // Chất lượng JPEG hiện tại
  
  // Kiểm tra kết nối WebSocket
  if (!client.available()) {
    Serial.println("⚠️ WebSocket disconnected, reconnecting...");
    if (connectWebSocket()) {
      Serial.println("✅ WebSocket reconnected");
    } else {
      Serial.println("❌ Reconnect failed, waiting...");
      delay(RECONNECT_DELAY);
    }
    return;
  }

  // Kiểm tra FPS - chỉ gửi frame khi đủ thời gian
  unsigned long currentTime = millis();
  if (currentTime - lastFrameTime < (1000 / TARGET_FPS)) {
    client.poll();  // Vẫn poll để giữ kết nối
    delay(5);       // Giảm delay từ 10ms xuống 5ms
    return;
  }

  // Chụp ảnh
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("❌ Capture failed");
    delay(50);      // Giảm delay từ 100ms xuống 50ms
    esp_camera_fb_return(fb);
    return;
  }

  // Kiểm tra kích thước frame - nếu quá lớn có thể bỏ qua hoặc giảm chất lượng
  if (fb->len > MAX_FRAME_SIZE) {
    Serial.printf("⚠️ Frame too large: %d bytes, skipping\n", fb->len);
    esp_camera_fb_return(fb);
    delay(10);
    return;
  }

  // Gửi ảnh với timeout
  unsigned long sendStart = millis();
  bool sent = client.sendBinary((const char*)fb->buf, fb->len);
  
  if (!sent) {
    Serial.println("❌ Send failed, connection may be broken");
    esp_camera_fb_return(fb);
    delay(100);
    return;
  }

  // Tính thời gian gửi
  unsigned long sendTime = millis() - sendStart;
  
  framesSent++;
  if (framesSent % 20 == 0) {
    Serial.printf("📸 Frame %d sent (%d bytes, %lu ms)\n",
                  framesSent, fb->len, sendTime);
  }

  esp_camera_fb_return(fb);

  // Poll để xử lý message từ server
  client.poll();

  // Cập nhật thời gian frame cuối
  lastFrameTime = currentTime;

  // Điều chỉnh delay động dựa trên thời gian gửi
  int dynamicDelay = max(50, (1000 / TARGET_FPS) - (int)sendTime);
  delay(dynamicDelay);
}