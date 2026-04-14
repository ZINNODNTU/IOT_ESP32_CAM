#include "esp_camera.h"
#include <WiFi.h>
#include <ArduinoWebsockets.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

using namespace websockets;

// ================= WIFI =================
const char* ssid = "1";
const char* password = "14022021i";

// ⚠️ SỬA IP SERVER (máy bạn)
const char* ws_url = "ws://192.168.5.183:3000/ws";

// ⚠️ ID CAMERA
const char* DEVICE_ID = "esp32cam_1";

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

// ================= LOOP =================
void loop() {

  // nếu mất kết nối → reconnect
  if (!client.available()) {
    Serial.println("⚠️ Reconnecting WS...");
    connectWebSocket();
    delay(2000);
    return;
  }

  // chụp ảnh
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("❌ Capture failed");
    delay(1000);
    return;
  }

  // gửi ảnh
  client.sendBinary((const char*)fb->buf, fb->len);

  Serial.println("📸 Frame sent");

  esp_camera_fb_return(fb);

  client.poll();

  delay(30); // ~30fps (giảm lag)
}