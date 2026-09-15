#include <Arduino.h>
#include <DHT.h>
#include <HTTPClient.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>

// ============================================================
// SafeBite ESP32 IoT prototype
//
// Current physical sensors:
//   - DHT22: temperature + humidity
//   - Magnetic reed switch: refrigerator/cold-storage door state
//
// Production demo path:
//   ESP32 -> HTTPS -> SafeBite Render API -> PostgreSQL -> Dashboard
// ============================================================

#define DHT_PIN 4
#define DHT_TYPE DHT22
#define DOOR_PIN 27

const char *WIFI_SSID = "YOUR_WIFI_NAME";
const char *WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// Set USE_LOCAL_SERVER to true only when running FastAPI locally.
const bool USE_LOCAL_SERVER = false;

const char *PRODUCTION_SERVER_URL =
    "https://safebite-sje5.onrender.com/sensors/readings";

const char *LOCAL_SERVER_URL =
    "http://192.168.1.20:8000/sensors/readings";

const char *DEVICE_ID = "SB-MGM-ESP32-001";
const unsigned long SEND_INTERVAL_MS = 10000;

DHT dht(DHT_PIN, DHT_TYPE);

void connectWiFi() {
  Serial.print("Connecting to Wi-Fi");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long started = millis();

  while (WiFi.status() != WL_CONNECTED && millis() - started < 20000) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("Wi-Fi connected. ESP32 IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("Wi-Fi connection timed out.");
  }
}

void sendReading(float temperature, float humidity, bool doorOpen) {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Skipping upload: Wi-Fi unavailable.");
    return;
  }

  HTTPClient http;
  int statusCode = -1;

  String payload = "{";
  payload += "\"device_id\":\"" + String(DEVICE_ID) + "\",";
  payload += "\"temperature\":" + String(temperature, 2) + ",";
  payload += "\"humidity\":" + String(humidity, 2) + ",";
  payload += "\"door_open\":" + String(doorOpen ? "true" : "false");
  payload += "}";

  if (USE_LOCAL_SERVER) {
    if (!http.begin(LOCAL_SERVER_URL)) {
      Serial.println("Unable to initialise local HTTP client.");
      return;
    }
  } else {
    // Prototype convenience: skip certificate pinning. For a production
    // deployment, use certificate validation instead of setInsecure().
    WiFiClientSecure secureClient;
    secureClient.setInsecure();

    if (!http.begin(secureClient, PRODUCTION_SERVER_URL)) {
      Serial.println("Unable to initialise HTTPS client.");
      return;
    }
  }

  http.addHeader("Content-Type", "application/json");
  statusCode = http.POST(payload);

  Serial.println("----------------------------------------");
  Serial.print("Endpoint: ");
  Serial.println(USE_LOCAL_SERVER ? LOCAL_SERVER_URL : PRODUCTION_SERVER_URL);
  Serial.print("Payload: ");
  Serial.println(payload);
  Serial.print("HTTP status: ");
  Serial.println(statusCode);

  if (statusCode > 0) {
    Serial.println("Server response:");
    Serial.println(http.getString());
  } else {
    Serial.print("HTTP error: ");
    Serial.println(http.errorToString(statusCode));
  }

  http.end();
}

void setup() {
  Serial.begin(115200);
  delay(500);

  pinMode(DOOR_PIN, INPUT_PULLUP);
  dht.begin();

  connectWiFi();
}

void loop() {
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("DHT22 read failed; retrying next cycle.");
    delay(SEND_INTERVAL_MS);
    return;
  }

  // With INPUT_PULLUP, the circuit is LOW when the reed switch is closed.
  // Adjust this interpretation if the physical mounting/wiring is reversed.
  bool doorOpen = digitalRead(DOOR_PIN) == HIGH;

  sendReading(temperature, humidity, doorOpen);

  delay(SEND_INTERVAL_MS);
}
