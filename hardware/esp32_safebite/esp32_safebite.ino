#include <Arduino.h>
#include <DallasTemperature.h>
#include <HTTPClient.h>
#include <OneWire.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>

// ============================================================
// SafeBite ESP32 IoT prototype
//
// Current physical sensor:
//   - Waterproof DS18B20: temperature only
//
// Optional future sensors:
//   - DHT22 for humidity
//   - Magnetic reed switch for refrigerator door state
//
// Production demo path:
//   ESP32 -> HTTPS -> SafeBite Render API -> PostgreSQL -> Dashboard
// ============================================================

#define DS18B20_PIN 4

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

OneWire oneWire(DS18B20_PIN);
DallasTemperature temperatureSensor(&oneWire);

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

void sendReading(float temperatureC) {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Skipping upload: Wi-Fi unavailable.");
    return;
  }

  HTTPClient http;
  int statusCode = -1;

  // Humidity and door state are not measured by the current DS18B20-only
  // prototype. The API accepts null humidity rather than inventing data.
  String payload = "{";
  payload += "\"device_id\":\"" + String(DEVICE_ID) + "\",";
  payload += "\"temperature\":" + String(temperatureC, 2) + ",";
  payload += "\"humidity\":null,";
  payload += "\"door_open\":false";
  payload += "}";

  if (USE_LOCAL_SERVER) {
    if (!http.begin(LOCAL_SERVER_URL)) {
      Serial.println("Unable to initialise local HTTP client.");
      return;
    }
  } else {
    // Prototype convenience. For production, use proper TLS certificate
    // validation rather than setInsecure().
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
  Serial.print("Temperature: ");
  Serial.print(temperatureC, 2);
  Serial.println(" C");
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

  temperatureSensor.begin();
  connectWiFi();
}

void loop() {
  temperatureSensor.requestTemperatures();
  float temperatureC = temperatureSensor.getTempCByIndex(0);

  if (temperatureC == DEVICE_DISCONNECTED_C) {
    Serial.println("DS18B20 read failed; check wiring and 4.7k pull-up.");
    delay(SEND_INTERVAL_MS);
    return;
  }

  sendReading(temperatureC);
  delay(SEND_INTERVAL_MS);
}
