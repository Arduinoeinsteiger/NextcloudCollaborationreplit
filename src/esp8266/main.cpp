/**
 * SwissAirDry ESP8266 RestAPI mit Membranschalter
 * 
 * PlatformIO-Version
 * 
 * @version 1.0.0
 * @author Swiss Air Dry Team <info@swissairdry.com>
 * @copyright 2023-2025 Swiss Air Dry Team
 */

#include <Arduino.h>
#include <ESP8266WiFi.h>          // ESP8266 WiFi
#include <ESP8266HTTPClient.h>     // HTTP-Client
#include <ESP8266WebServer.h>      // Webserver
#include <ESP8266mDNS.h>           // mDNS für einfache Erreichbarkeit
#include <ArduinoOTA.h>            // OTA-Updates
#include <ArduinoJson.h>           // JSON-Verarbeitung
#include <EEPROM.h>                // Konfigurationsspeicherung
#include <DNSServer.h>             // Captive Portal
#include <WiFiManager.h>           // WiFi-Konfiguration
#include <OneButton.h>             // Für Membranschalter

// Konstanten
#define DEVICE_VERSION "1.0.0"
#define CONFIG_SIZE 512
#define SENSOR_READ_INTERVAL 5000    // 5 Sekunden
#define API_SEND_INTERVAL 30000      // 30 Sekunden
#define LED_UPDATE_INTERVAL 1000     // 1 Sekunde
#define WEB_CONFIG_PORT 80           // Webserver-Port
#define MAX_FAILED_API_ATTEMPTS 5    // Max. Anzahl fehlgeschlagener API-Verbindungen

// Pinnummern für ESP8266 (Wemos D1 Mini)
#define RELAY1_PIN D1    // Relais 1
#define RELAY2_PIN D2    // Relais 2
#define SENSOR_PIN D4    // DHT Sensor
#define LED_PIN LED_BUILTIN // Eingebaute LED

// Membranschalter-Konfiguration (3-Tasten-Modul mit 4 Pins)
#define MEMBRANE_PIN A0   // Analoger Pin für Membranschalter
#define BTN_UP 0          // Nach oben (>)
#define BTN_DOWN 1        // Nach unten (<)
#define BTN_OK 2          // OK-Taste

// OneButton-Objekte für die 3 Tasten des Membranschalters
OneButton btnUp(MEMBRANE_PIN, true);
OneButton btnDown(MEMBRANE_PIN, true);
OneButton btnOk(MEMBRANE_PIN, true);

// Globale Variablen
struct Config {
  char device_id[32];      // Geräte-ID
  char api_host[64];       // API-Host
  int api_port;            // API-Port
  char api_path[64];       // API-Pfad
  bool use_ssl;            // HTTPS verwenden
  char auth_token[64];     // API-Authentifizierung
  bool relay1_enabled;     // Relais 1 aktiviert
  bool relay2_enabled;     // Relais 2 aktiviert
  float temp_threshold;    // Temperaturschwelle
  float humid_threshold;   // Feuchtigkeitsschwelle
  bool initialized;        // Konfiguration initialisiert
};

Config config;
ESP8266WebServer server(WEB_CONFIG_PORT);
unsigned long lastSensorRead = 0;
unsigned long lastApiSend = 0;
unsigned long lastLedUpdate = 0;
unsigned long startTime = 0;
unsigned long runTime = 0;
bool wifiConnected = false;
bool apiConnected = false;
bool relay1State = false;
bool relay2State = false;
float temperature = 0.0;
float humidity = 0.0;
float power = 0.0;
float energy = 0.0;
int failedApiAttempts = 0;

// Funktionsprototypen
void setupWifi();
void setupWebServer();
void setupOTA();
void loadConfig();
void saveConfig();
bool sendDataToApi();
void readSensors();
void updateLedStatus();
void handleRoot();
void handleConfig();
void handleSave();
void handleReset();
void handleRestart();
void handleStatus();
void generateDeviceId();

// Funktionen für Membranschalter
void setupButtons();
void checkMembraneButtons();
int getMembraneButtonPressed();
void onUpPressed();
void onDownPressed();
void onOkPressed();
void onUpLongPressed();
void onDownLongPressed();
void onOkLongPressed();

// Implementierung der Membranschalter-Funktionen
void setupButtons() {
  Serial.println("Membranschalter-Tasten einrichten...");
  
  // Konfiguriere die Funktionen für jede Taste
  btnUp.attachClick(onUpPressed);
  btnUp.attachLongPressStart(onUpLongPressed);
  
  btnDown.attachClick(onDownPressed);
  btnDown.attachLongPressStart(onDownLongPressed);
  
  btnOk.attachClick(onOkPressed);
  btnOk.attachLongPressStart(onOkLongPressed);
  
  Serial.println("Membranschalter-Tasten eingerichtet");
}

// Prüft, welche Taste gedrückt wurde anhand des Analogwerts
int getMembraneButtonPressed() {
  int value = analogRead(MEMBRANE_PIN);
  
  // Diese Werte müssen je nach Hardware angepasst werden
  // Typische Werte für ein 3-Tasten-Modul:
  if (value < 100) {  // Entspricht ca. 0-0.2V
    return BTN_UP;    // UP/Rechts-Taste
  } 
  else if (value < 300) {  // Entspricht ca. 0.2-0.6V
    return BTN_DOWN;  // DOWN/Links-Taste
  } 
  else if (value < 500) {  // Entspricht ca. 0.6-1.0V
    return BTN_OK;    // OK-Taste
  }
  
  return -1;  // Keine Taste gedrückt
}

// Regelmäßig die Membrantasten prüfen
void checkMembraneButtons() {
  // Aktuelle Taste ermitteln
  int button = getMembraneButtonPressed();
  
  // OneButton-Bibliothek für die entsprechende Taste aktualisieren
  if (button == BTN_UP) {
    btnUp.tick();
  } 
  else if (button == BTN_DOWN) {
    btnDown.tick();
  } 
  else if (button == BTN_OK) {
    btnOk.tick();
  }
}

// Aktionen für Tastendrücke
void onUpPressed() {
  Serial.println("UP-Taste gedrückt");
  // Hier die Aktion für die UP-Taste (>) implementieren
  // z.B. Menünavigation nach rechts oder Wert erhöhen
}

void onDownPressed() {
  Serial.println("DOWN-Taste gedrückt");
  // Hier die Aktion für die DOWN-Taste (<) implementieren
  // z.B. Menünavigation nach links oder Wert verringern
}

void onOkPressed() {
  Serial.println("OK-Taste gedrückt");
  // Hier die Aktion für die OK-Taste implementieren
  // z.B. Menüpunkt auswählen oder Einstellung bestätigen
  
  // Beispiel: Relais 1 umschalten
  relay1State = !relay1State;
  digitalWrite(RELAY1_PIN, relay1State ? HIGH : LOW);
  Serial.print("Relais 1 manuell auf ");
  Serial.println(relay1State ? "EIN" : "AUS");
}

// Aktionen für langes Drücken
void onUpLongPressed() {
  Serial.println("UP-Taste lange gedrückt");
  // Hier die Aktion für langes Drücken der UP-Taste implementieren
  // z.B. schnelles Erhöhen eines Wertes
}

void onDownLongPressed() {
  Serial.println("DOWN-Taste lange gedrückt");
  // Hier die Aktion für langes Drücken der DOWN-Taste implementieren
  // z.B. schnelles Verringern eines Wertes
}

void onOkLongPressed() {
  Serial.println("OK-Taste lange gedrückt");
  // Hier die Aktion für langes Drücken der OK-Taste implementieren
  // z.B. Reset oder Speichern von Einstellungen
  
  // Beispiel: Beide Relais ausschalten
  relay1State = false;
  relay2State = false;
  digitalWrite(RELAY1_PIN, LOW);
  digitalWrite(RELAY2_PIN, LOW);
  Serial.println("Alle Relais ausgeschaltet");
}

void setup() {
  // Serielle Schnittstelle initialisieren
  Serial.begin(115200);
  delay(500);
  Serial.println("\n\nSwissAirDry ESP8266 mit REST API");
  Serial.print("Version: ");
  Serial.println(DEVICE_VERSION);
  
  // EEPROM initialisieren
  EEPROM.begin(CONFIG_SIZE);
  
  // Konfiguration laden
  loadConfig();
  
  // Wenn nicht initialisiert, Standardwerte setzen
  if (!config.initialized) {
    Serial.println("Erstinitialisierung...");
    generateDeviceId();
    strcpy(config.api_host, "api.vgnc.org");
    config.api_port = 443;
    strcpy(config.api_path, "/api/device");
    config.use_ssl = true;
    config.relay1_enabled = true;
    config.relay2_enabled = false;
    config.temp_threshold = 20.0;
    config.humid_threshold = 60.0;
    config.initialized = true;
    saveConfig();
  }
  
  // Pins konfigurieren
  pinMode(RELAY1_PIN, OUTPUT);
  pinMode(RELAY2_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  pinMode(MEMBRANE_PIN, INPUT);
  
  // Relais ausschalten
  digitalWrite(RELAY1_PIN, LOW);
  digitalWrite(RELAY2_PIN, LOW);
  
  // Membrantasten einrichten
  setupButtons();
  
  // WiFi-Verbindung aufbauen
  setupWifi();
  
  // Webserver starten
  setupWebServer();
  
  // OTA-Updates konfigurieren
  setupOTA();
  
  // Startzeit speichern
  startTime = millis();
  
  Serial.println("Setup abgeschlossen");
  Serial.print("Geräte-ID: ");
  Serial.println(config.device_id);
}

void loop() {
  // Webserver-Anfragen bearbeiten
  server.handleClient();
  
  // OTA-Updates prüfen
  ArduinoOTA.handle();
  
  // Membranschalter prüfen
  checkMembraneButtons();
  
  // Aktuelle Zeit
  unsigned long currentTime = millis();
  
  // Laufzeit aktualisieren
  runTime = (currentTime - startTime) / 1000;
  
  // WLAN-Status prüfen
  wifiConnected = (WiFi.status() == WL_CONNECTED);
  
  // Sensoren auslesen
  if (currentTime - lastSensorRead >= SENSOR_READ_INTERVAL) {
    readSensors();
    lastSensorRead = currentTime;
  }
  
  // Daten an API senden
  if (wifiConnected && (currentTime - lastApiSend >= API_SEND_INTERVAL)) {
    apiConnected = sendDataToApi();
    lastApiSend = currentTime;
    
    // Bei zu vielen Fehlversuchen WLAN neu verbinden
    if (!apiConnected) {
      failedApiAttempts++;
      if (failedApiAttempts >= MAX_FAILED_API_ATTEMPTS) {
        Serial.println("Zu viele API-Verbindungsfehler. WLAN wird neu verbunden.");
        WiFi.reconnect();
        failedApiAttempts = 0;
      }
    } else {
      failedApiAttempts = 0;
    }
  }
  
  // LED-Status aktualisieren
  if (currentTime - lastLedUpdate >= LED_UPDATE_INTERVAL) {
    updateLedStatus();
    lastLedUpdate = currentTime;
  }
  
  // Kurze Pause
  delay(10);
}

void setupWifi() {
  Serial.println("WLAN-Konfiguration wird gestartet...");
  
  // WiFiManager initialisieren
  WiFiManager wifiManager;
  
  // Timeout nach 3 Minuten im Konfigurationsmodus
  wifiManager.setConfigPortalTimeout(180);
  
  // Im Konfigurationsmodus blaue LED einschalten
  wifiManager.setAPCallback([](WiFiManager* wifiManager) {
    Serial.println("Konfigurationsmodus aktiv");
    digitalWrite(LED_PIN, LOW); // LED einschalten (LOW bei ESP8266)
  });
  
  // AP-Name generieren
  String apName = "SwissAirDry-" + String(config.device_id);
  
  // Verbinden oder Konfigurationsportal starten
  if (!wifiManager.autoConnect(apName.c_str(), "swissairdry")) {
    Serial.println("Verbindung fehlgeschlagen, Timeout. Neustart...");
    delay(3000);
    ESP.restart();
  }
  
  // Verbunden
  Serial.println("WLAN verbunden!");
  Serial.print("IP-Adresse: ");
  Serial.println(WiFi.localIP());
  
  wifiConnected = true;
}

void setupWebServer() {
  // Webserver-Routen definieren
  server.on("/", HTTP_GET, handleRoot);
  server.on("/config", HTTP_GET, handleConfig);
  server.on("/save", HTTP_POST, handleSave);
  server.on("/reset", HTTP_GET, handleReset);
  server.on("/restart", HTTP_GET, handleRestart);
  server.on("/status", HTTP_GET, handleStatus);
  
  // 404-Handler
  server.onNotFound([]() {
    server.send(404, "text/plain", "Nicht gefunden");
  });
  
  // Webserver starten
  server.begin();
  Serial.print("Webserver gestartet auf Port ");
  Serial.println(WEB_CONFIG_PORT);
  
  // mDNS einrichten, wenn WLAN verbunden
  if (wifiConnected) {
    if (MDNS.begin(config.device_id)) {
      Serial.print("mDNS-Responder gestartet. Erreichbar unter http://");
      Serial.print(config.device_id);
      Serial.println(".local");
    }
  }
}

void setupOTA() {
  // OTA-Updates konfigurieren
  ArduinoOTA.setHostname(config.device_id);
  
  // Optional: OTA-Passwort setzen
  // ArduinoOTA.setPassword("admin");
  
  ArduinoOTA.onStart([]() {
    Serial.println("OTA-Update gestartet");
    digitalWrite(RELAY1_PIN, LOW); // Relais sicherheitshalber ausschalten
    digitalWrite(RELAY2_PIN, LOW);
  });
  
  ArduinoOTA.onEnd([]() {
    Serial.println("OTA-Update abgeschlossen");
  });
  
  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    Serial.printf("OTA-Fortschritt: %u%%\r", (progress / (total / 100)));
  });
  
  ArduinoOTA.onError([](ota_error_t error) {
    Serial.printf("OTA-Fehler [%u]: ", error);
    if (error == OTA_AUTH_ERROR) Serial.println("Auth-Fehler");
    else if (error == OTA_BEGIN_ERROR) Serial.println("Begin-Fehler");
    else if (error == OTA_CONNECT_ERROR) Serial.println("Connect-Fehler");
    else if (error == OTA_RECEIVE_ERROR) Serial.println("Receive-Fehler");
    else if (error == OTA_END_ERROR) Serial.println("End-Fehler");
  });
  
  ArduinoOTA.begin();
}

void loadConfig() {
  Serial.println("Lade Konfiguration aus EEPROM...");
  EEPROM.get(0, config);
  
  // Prüfen, ob initialized = true ist
  if (!config.initialized) {
    Serial.println("Keine gültige Konfiguration gefunden");
    return;
  }
  
  Serial.println("Konfiguration geladen:");
  Serial.print("Geräte-ID: ");
  Serial.println(config.device_id);
  Serial.print("API-Host: ");
  Serial.println(config.api_host);
  Serial.print("API-Port: ");
  Serial.println(config.api_port);
}

void saveConfig() {
  Serial.println("Speichere Konfiguration im EEPROM...");
  EEPROM.put(0, config);
  EEPROM.commit();
  Serial.println("Konfiguration gespeichert");
}

void generateDeviceId() {
  // MAC-Adresse als Basis für Geräte-ID verwenden
  uint8_t mac[6];
  WiFi.macAddress(mac);
  
  // Format: esp-XXXX (letzten 4 Bytes der MAC in Hex)
  sprintf(config.device_id, "esp-%02x%02x%02x", mac[3], mac[4], mac[5]);
}

void readSensors() {
  // Hier echte Sensorauslesung einbauen
  // Momentan simulierte Werte für den Test
  
  // Simulierte Temperatur: 18-30°C
  temperature = 18.0 + (float)random(0, 120) / 10.0;
  
  // Simulierte Luftfeuchtigkeit: 30-90%
  humidity = 30.0 + (float)random(0, 600) / 10.0;
  
  // Leistung berechnen, wenn Relais eingeschaltet ist
  if (relay1State) {
    power = 800.0 + (float)random(0, 100) / 10.0;  // ~800W für einen Trockner
    energy += power / 3600.0 * (SENSOR_READ_INTERVAL / 1000.0);  // kWh berechnen
  } else {
    power = 0.0;
  }
  
  Serial.println("Sensordaten aktualisiert:");
  Serial.print("Temperatur: ");
  Serial.print(temperature);
  Serial.println(" °C");
  Serial.print("Luftfeuchtigkeit: ");
  Serial.print(humidity);
  Serial.println(" %");
  Serial.print("Leistung: ");
  Serial.print(power);
  Serial.println(" W");
  Serial.print("Energie: ");
  Serial.print(energy);
  Serial.println(" kWh");
  
  // Automatische Steuerung basierend auf Schwellenwerten
  if (config.relay1_enabled) {
    bool newRelayState = (humidity > config.humid_threshold);
    
    if (newRelayState != relay1State) {
      relay1State = newRelayState;
      digitalWrite(RELAY1_PIN, relay1State ? HIGH : LOW);
      
      Serial.print("Automatische Relais-Steuerung: ");
      Serial.println(relay1State ? "EIN" : "AUS");
    }
  }
}

bool sendDataToApi() {
  if (!wifiConnected) {
    Serial.println("Keine WLAN-Verbindung, Daten werden nicht gesendet");
    return false;
  }
  
  // API-Client
  HTTPClient http;
  WiFiClient client;
  
  // URL zusammensetzen
  String url;
  if (config.use_ssl) {
    // Für HTTPS müsste hier WiFiClientSecure verwendet werden
    Serial.println("HTTPS wird auf ESP8266 nicht unterstützt, verwende HTTP");
    url = "http://";
  } else {
    url = "http://";
  }
  
  url += String(config.api_host);
  url += ":" + String(config.api_port);
  url += String(config.api_path);
  url += "/" + String(config.device_id) + "/data";
  
  Serial.print("Sende Daten an API: ");
  Serial.println(url);
  
  // HTTP-Verbindung einrichten
  http.begin(client, url);
  http.addHeader("Content-Type", "application/json");
  
  // Optional: Authentifizierung
  if (strlen(config.auth_token) > 0) {
    http.addHeader("Authorization", "Bearer " + String(config.auth_token));
  }
  
  // JSON-Daten erstellen
  StaticJsonDocument<256> doc;
  doc["temperature"] = temperature;
  doc["humidity"] = humidity;
  doc["power"] = power;
  doc["energy"] = energy;
  doc["relay1_state"] = relay1State;
  doc["relay2_state"] = relay2State;
  doc["runtime"] = runTime;
  doc["version"] = DEVICE_VERSION;
  
  String json;
  serializeJson(doc, json);
  
  // Daten senden
  int httpCode = http.POST(json);
  bool success = false;
  
  if (httpCode > 0) {
    Serial.print("HTTP-Antwortcode: ");
    Serial.println(httpCode);
    
    if (httpCode == HTTP_CODE_OK || httpCode == HTTP_CODE_CREATED) {
      String response = http.getString();
      Serial.println("Antwort: " + response);
      
      // Antwort verarbeiten
      StaticJsonDocument<384> responseDoc;
      DeserializationError error = deserializeJson(responseDoc, response);
      
      if (!error) {
        // Steuerungsbefehle verarbeiten
        if (responseDoc.containsKey("relay1_control")) {
          bool newRelay1State = responseDoc["relay1_control"];
          if (relay1State != newRelay1State) {
            relay1State = newRelay1State;
            digitalWrite(RELAY1_PIN, relay1State ? HIGH : LOW);
            Serial.print("Relais 1 auf ");
            Serial.println(relay1State ? "EIN" : "AUS");
          }
        }
        
        if (responseDoc.containsKey("relay2_control")) {
          bool newRelay2State = responseDoc["relay2_control"];
          if (relay2State != newRelay2State) {
            relay2State = newRelay2State;
            digitalWrite(RELAY2_PIN, relay2State ? HIGH : LOW);
            Serial.print("Relais 2 auf ");
            Serial.println(relay2State ? "EIN" : "AUS");
          }
        }
        
        success = true;
      } else {
        Serial.print("JSON-Parsing-Fehler: ");
        Serial.println(error.c_str());
      }
    }
  } else {
    Serial.print("HTTP-Fehler: ");
    Serial.println(http.errorToString(httpCode));
  }
  
  http.end();
  return success;
}

void updateLedStatus() {
  // LED-Status basierend auf dem Systemstatus
  if (!wifiConnected) {
    // Schnelles Blinken: WLAN-Problem
    digitalWrite(LED_PIN, (millis() / 200) % 2 ? LOW : HIGH);
  } else if (!apiConnected) {
    // Langsames Blinken: API-Problem
    digitalWrite(LED_PIN, (millis() / 1000) % 2 ? LOW : HIGH);
  } else if (relay1State || relay2State) {
    // Dauerhaft an: Alles OK und aktiv
    digitalWrite(LED_PIN, LOW);
  } else {
    // Pulsieren: Alles OK, Standby
    int brightness = (millis() % 2000) / 2000.0 * 255;
    if (brightness > 127) brightness = 255 - brightness;
    // LED_BUILTIN ist beim ESP8266 invertiert (LOW = an)
    digitalWrite(LED_PIN, brightness < 64 ? LOW : HIGH);
  }
}

// Webserver-Handler - Nur prototypisch hier eingebunden, für vollständige Implementierung siehe Original-Sketch
void handleRoot() {
  String html = "<!DOCTYPE html><html><head><title>SwissAirDry</title></head><body>";
  html += "<h1>SwissAirDry - ESP8266</h1>";
  html += "<p>Temperatur: " + String(temperature) + " °C</p>";
  html += "<p>Luftfeuchtigkeit: " + String(humidity) + " %</p>";
  html += "<p>Relais 1: " + String(relay1State ? "EIN" : "AUS") + "</p>";
  html += "<p>Relais 2: " + String(relay2State ? "EIN" : "AUS") + "</p>";
  html += "</body></html>";
  server.send(200, "text/html", html);
}

void handleConfig() {
  server.send(200, "text/html", "Konfigurationsseite");
}

void handleSave() {
  server.send(200, "text/html", "Speichern");
}

void handleReset() {
  server.send(200, "text/html", "Reset");
}

void handleRestart() {
  server.send(200, "text/html", "Neustart");
}

void handleStatus() {
  StaticJsonDocument<256> doc;
  doc["temperature"] = temperature;
  doc["humidity"] = humidity;
  doc["power"] = power;
  doc["energy"] = energy;
  doc["relay1_state"] = relay1State;
  doc["relay2_state"] = relay2State;
  doc["runtime"] = runTime;
  
  String json;
  serializeJson(doc, json);
  
  server.send(200, "application/json", json);
}