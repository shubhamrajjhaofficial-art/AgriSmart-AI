/*
  IoT Based Smart Agriculture System - ESP8266
  Sensors: DHT11, analog soil-moisture module, RS485 NPK sensor, relay module.
  IMPORTANT:
  - Set WIFI_SSID, WIFI_PASSWORD, SERVER_URL and DEVICE_TOKEN.
  - SERVER_URL must be the computer/server LAN IP, e.g. http://192.168.1.20:5000/api/sensors
  - NPK Modbus address/registers/baud rate vary by manufacturer. Defaults below are common examples,
    NOT guaranteed for your exact sensor. Check the sensor manual before relying on NPK values.
  - Keep AUTO_RELAY false until sensor calibration and pump safety are verified.
*/

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <DHT.h>
#include <SoftwareSerial.h>
#include <ModbusMaster.h>
#include <ArduinoJson.h>

// ---------- Wi-Fi / backend ----------
const char* WIFI_SSID = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* SERVER_URL = "http://192.168.1.20:5000/api/sensors";
const char* DEVICE_TOKEN = "change-this-device-token";

// ---------- Pin mapping (adjust to your actual wiring) ----------
#define DHT_PIN D2
#define DHT_TYPE DHT11
#define SOIL_PIN A0
#define RELAY_PIN D1

// SoftwareSerial constructor: RX, TX. RS485 module RO/TXD -> D5; DI/RXD <- D6
#define NPK_RX_PIN D5
#define NPK_TX_PIN D6
#define NPK_DE_RE_PIN D7

// ---------- Configuration ----------
const bool AUTO_RELAY = false;       // Leave false for initial testing
const bool RELAY_ACTIVE_LOW = true; // Many relay modules are active LOW; verify yours
const int SOIL_DRY_RAW = 850;       // Calibrate for your sensor
const int SOIL_WET_RAW = 350;       // Calibrate for your sensor
const int IRRIGATION_START_PERCENT = 30;

// Common example Modbus settings; check the sensor manual:
const uint8_t NPK_SLAVE_ID = 1;
const uint32_t NPK_BAUD = 4800;
const uint16_t REG_N = 0x001E;
const uint16_t REG_P = 0x001F;
const uint16_t REG_K = 0x0020;

DHT dht(DHT_PIN, DHT_TYPE);
SoftwareSerial npkSerial(NPK_RX_PIN, NPK_TX_PIN);
ModbusMaster npk;

float temperatureC = NAN, humidityPct = NAN;
int soilRaw = -1, soilPct = -1;
int nitrogen = -1, phosphorus = -1, potassium = -1;
bool relayOn = false;
String npkStatus = "Waiting for NPK reading";

void preTransmission() { digitalWrite(NPK_DE_RE_PIN, HIGH); }
void postTransmission() { digitalWrite(NPK_DE_RE_PIN, LOW); }

void setRelay(bool on) {
  relayOn = on;
  digitalWrite(RELAY_PIN, RELAY_ACTIVE_LOW ? (on ? LOW : HIGH) : (on ? HIGH : LOW));
}

int readRegister(uint16_t reg, int &outValue) {
  uint8_t result = npk.readHoldingRegisters(reg, 1);
  if (result == npk.ku8MBSuccess) {
    outValue = npk.getResponseBuffer(0);
    return 1;
  }
  return 0;
}

void readNPK() {
  int n = -1, p = -1, k = -1;
  bool okN = readRegister(REG_N, n);
  delay(100);
  bool okP = readRegister(REG_P, p);
  delay(100);
  bool okK = readRegister(REG_K, k);

  if (okN && okP && okK) {
    nitrogen = n; phosphorus = p; potassium = k;
    npkStatus = "OK (verify sensor units/calibration)";
  } else {
    nitrogen = phosphorus = potassium = -1;
    npkStatus = "Modbus read failed: check power, A/B, baud, ID and register map";
  }
}

void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to Wi-Fi");
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 20000) {
    delay(500); Serial.print(".");
  }
  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("ESP IP: "); Serial.println(WiFi.localIP());
  } else {
    Serial.println("Wi-Fi not connected yet; will retry later.");
  }
}

void postReadings() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
    if (WiFi.status() != WL_CONNECTED) return;
  }

  WiFiClient client;
  HTTPClient http;
  if (!http.begin(client, SERVER_URL)) {
    Serial.println("Could not start HTTP connection");
    return;
  }
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Token", DEVICE_TOKEN);

  StaticJsonDocument<512> doc;
  if (isnan(temperatureC)) doc["temperature_c"] = nullptr;
  else doc["temperature_c"] = temperatureC;
  if (isnan(humidityPct)) doc["humidity_pct"] = nullptr;
  else doc["humidity_pct"] = humidityPct;

  if (soilRaw < 0) doc["soil_raw"] = nullptr;
  else doc["soil_raw"] = soilRaw;
  if (soilPct < 0) doc["soil_pct"] = nullptr;
  else doc["soil_pct"] = soilPct;

  if (nitrogen < 0) doc["nitrogen_mgkg"] = nullptr;
  else doc["nitrogen_mgkg"] = nitrogen;
  if (phosphorus < 0) doc["phosphorus_mgkg"] = nullptr;
  else doc["phosphorus_mgkg"] = phosphorus;
  if (potassium < 0) doc["potassium_mgkg"] = nullptr;
  else doc["potassium_mgkg"] = potassium;

  doc["npk_status"] = npkStatus;
  doc["relay_on"] = relayOn;

  String payload;
  serializeJson(doc, payload);
  int code = http.POST(payload);
  Serial.printf("POST result: %d\n", code);
  if (code > 0) Serial.println(http.getString());
  http.end();
}

void setup() {
  Serial.begin(115200);
  pinMode(NPK_DE_RE_PIN, OUTPUT);
  digitalWrite(NPK_DE_RE_PIN, LOW); // receive mode
  pinMode(RELAY_PIN, OUTPUT);
  setRelay(false);

  dht.begin();
  npkSerial.begin(NPK_BAUD);
  npk.begin(NPK_SLAVE_ID, npkSerial);
  npk.preTransmission(preTransmission);
  npk.postTransmission(postTransmission);

  connectWiFi();
}

void loop() {
  temperatureC = dht.readTemperature();
  humidityPct = dht.readHumidity();

  soilRaw = analogRead(SOIL_PIN);
  if (SOIL_DRY_RAW != SOIL_WET_RAW) {
    soilPct = constrain(map(soilRaw, SOIL_DRY_RAW, SOIL_WET_RAW, 0, 100), 0, 100);
  } else {
    soilPct = -1;
  }

  readNPK();

  // Optional simple rule-based relay control. Keep AUTO_RELAY false during setup.
  if (AUTO_RELAY && soilPct >= 0) {
    setRelay(soilPct < IRRIGATION_START_PERCENT);
  } else {
    setRelay(false);
  }

  Serial.printf("Temp: %.1f C | Humidity: %.1f %% | Soil raw: %d | Soil %%: %d\n",
                temperatureC, humidityPct, soilRaw, soilPct);
  Serial.printf("N: %d P: %d K: %d | %s\n", nitrogen, phosphorus, potassium, npkStatus.c_str());

  postReadings();
  delay(5000);
}
