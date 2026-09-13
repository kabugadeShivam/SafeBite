#include <Arduino.h>
#include <DHT.h>
#include <HTTPClient.h>
#include <WiFi.h>

// ============================================================
// SafeBite ESP32 IoT prototype
//
// Sensors supported by the current backend contract:
//   - DHT22: temperature + humidity
//   - Magnetic reed switch: refrigerator/cold-storage door state
// ============================================================

#define DHT_PIN 4
#define DHT_TYPE DHT22
#define DOOR_PIN 27

const char *WIFI_SSID = "YOUR_WIFI_NAME";
const char *WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// IMPORTANT: use the laptop's LAN IP, not 127.0.0.1.
const char *SERVER_URL = "http://192.168.1.20:8000/sensors/readings";
const char *DEVICE_ID = "SB-MGM-ESP32-001";

const unsigned long SEND_INTERVAL_MS = 5000;

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

  if (!http.begin(SERVER_URL)) {
    Serial.println("Unable to initialise HTTP client.");
    return;
  }

  http.addHeader("Content-Type", "application/json");

  String payload = "{";
  payload += "\"device_id\":\"" + String(DEVICE_ID) + "\",";
  payload += "\"temperature\":" + String(temperature, 2) + ",";
  payload += "\"humidity\":" + String(humidity, 2) + ",";
  payload += "\"door_open\":" + String(doorOpen ? "true" : "false");
  payload += "}";

  int statusCode = http.POST(payload);

  Serial.println("----------------------------------------");
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
  // Adjust this interpretation if your physical mounting/wiring is reversed.
  bool doorOpen = digitalRead(DOOR_PIN) == HIGH;

  sendReading(temperature, humidity, doorOpen);

  delay(SEND_INTERVAL_MS);
}
