/*
 * SwissAirDry ESP32-C6 Multifunktionssystem mit Farbdisplay und nativer MQTT
 * 
 * Unterstützt:
 * - 1.47" LCD-Farbdisplay (172x320)
 * - SD-Kartenspeicher
 * - QR-Code Generierung für einfache Verbindung
 * - MQTT für Sensor- und Steuerungsdaten (native ESP32-C6 MQTT-Implementierung)
 * - API-Integration mit lokaler Zwischenspeicherung
 * - OTA Updates
 * 
 * Hardwarevoraussetzungen:
 * - ESP32-C6 Board mit 1.47" LCD-Display
 * - SD-Kartenslot
 */

// ----- BIBLIOTHEKEN -----
#include <WiFi.h>
#include <ESPmDNS.h>
#include <WiFiUdp.h>
#include <ArduinoOTA.h>
#include <TFT_eSPI.h>         // Display-Treiber (muss für das spezifische Display konfiguriert sein)
#include <SPI.h>
#include <FS.h>
#include <SD.h>
#include <EEPROM.h>
#include <ArduinoJson.h>
#include <mqtt_client.h>      // Native ESP32-C6 MQTT-Implementierung
#include <HTTPClient.h>
#include <qrcode.h>           // QR-Code Generator
#include <time.h>
#include <Update.h>
#include <WebServer.h>
#include <DNSServer.h>

// ----- KONFIGURATION -----
// Diese Einstellungen können über die Weboberfläche angepasst werden
#define EEPROM_SIZE 2048
#define JSON_CONFIG_SIZE 1024
#define COLOR_BACKGROUND TFT_BLACK
#define COLOR_TEXT TFT_WHITE
#define COLOR_TITLE TFT_ORANGE
#define COLOR_ERROR TFT_RED
#define COLOR_SUCCESS TFT_GREEN
#define COLOR_WARNING TFT_YELLOW
#define COLOR_INFO TFT_BLUE
#define COLOR_STATUS_BAR TFT_DARKGREY
#define QR_CODE_SIZE 4        // Größenskalierung für QR-Codes

// Standard-WLAN-Einstellungen
#define DEFAULT_AP_SSID "SwissAirDry-Setup"
#define DEFAULT_AP_PASSWORD "12345678"
#define CONFIG_AP_IP IPAddress(192, 168, 4, 1)
#define DNS_PORT 53

// Pins für XIAO ESP32C6
#define SD_CS_PIN 10          // SD-Karten Chip Select Pin (anpassen je nach Board)
#define RELAY_PIN 5           // Relais für die Steuerung

// Zeitintervalle
#define API_UPDATE_INTERVAL 60000        // API-Update alle 60 Sekunden
#define DISPLAY_UPDATE_INTERVAL 1000     // Display-Update alle 1 Sekunde
#define SENSOR_READ_INTERVAL 5000        // Sensor-Leseintervall alle 5 Sekunden
#define LOG_INTERVAL 300000              // Daten-Logging alle 5 Minuten
#define MQTT_RECONNECT_INTERVAL 5000     // MQTT-Wiederverbindung alle 5 Sekunden

// ----- GLOBALE OBJEKTE -----
TFT_eSPI tft = TFT_eSPI();               // Display-Objekt
WebServer server(80);                     // Webserver für Konfiguration
DNSServer dnsServer;                      // DNS-Server für Captive Portal
TaskHandle_t dataLoggingTask;             // Task-Handle für Datenprotokollierung
esp_mqtt_client_handle_t mqttClient;      // ESP32 MQTT-Client

// ----- GLOBALE VARIABLEN -----
// Konfiguration
struct Config {
  char version[8] = "1.0.0";             // Konfigurationsversion
  char deviceName[32] = "SwissAirDry";   // Gerätename
  char wifiSSID[33] = "";                // WLAN-SSID
  char wifiPassword[65] = "";            // WLAN-Passwort
  bool apMode = true;                    // AP-Modus aktiviert
  
  // MQTT-Einstellungen
  char mqttServer[65] = "";              // MQTT-Server
  int mqttPort = 1883;                   // MQTT-Port
  char mqttUser[33] = "";                // MQTT-Benutzername
  char mqttPassword[65] = "";            // MQTT-Passwort
  char mqttTopic[65] = "swissairdry/";   // MQTT-Basistopic
  
  // API-Einstellungen
  char apiServer[65] = "";               // API-Server
  char apiKey[65] = "";                  // API-Schlüssel
  int apiUpdateInterval = 60;            // Update-Intervall in Sekunden
  
  // Relay-Einstellungen
  bool relayEnabled = true;              // Relais aktiviert
  int relayMode = 0;                     // 0=Manuell, 1=Zeit, 2=Sensor
  int relayOnHour = 8;                   // Einschaltzeit (Stunde)
  int relayOnMinute = 0;                 // Einschaltzeit (Minute)
  int relayOffHour = 18;                 // Ausschaltzeit (Stunde)
  int relayOffMinute = 0;                // Ausschaltzeit (Minute)
  float relayThreshold = 60.0;           // Schwellenwert für sensorbasierte Steuerung
  
  // Sensoreinstellungen
  bool temperatureSensor = true;         // Temperatursensor vorhanden
  bool humiditySensor = true;            // Feuchtigkeitssensor vorhanden
  bool energySensor = true;              // Energiesensor vorhanden
  int sensorReadInterval = 5;            // Leseintervall in Sekunden
  
  // Logging-Einstellungen
  bool sdLogging = true;                 // SD-Kartenprotokollierung aktiviert
  int logInterval = 300;                 // Protokollintervall in Sekunden
};

Config config;                           // Konfigurationsobjekt

// Status
bool wifiConnected = false;              // WLAN-Verbindung
bool mqttConnected = false;              // MQTT-Verbindung
bool sdCardAvailable = false;            // SD-Karte verfügbar
bool configMode = false;                 // Konfigurationsmodus aktiv
bool relayState = false;                 // Relais-Status
String networkIP = "";                   // IP-Adresse
String firmwareVersion = "1.0.0";        // Firmware-Version
unsigned long lastApiUpdate = 0;         // Letztes API-Update
unsigned long lastDisplayUpdate = 0;     // Letztes Display-Update
unsigned long lastSensorRead = 0;        // Letzter Sensorwert
unsigned long lastLog = 0;               // Letztes Logging
unsigned long lastMqttReconnect = 0;     // Letzte MQTT-Wiederverbindung
int displayPage = 0;                     // Aktuelle Displayseite
int errorCode = 0;                       // Fehlercode
String errorMessage = "";                // Fehlermeldung

// Sensordaten
struct SensorData {
  float temperature = 0.0;               // Temperatur in °C
  float humidity = 0.0;                  // Luftfeuchtigkeit in %
  float energy = 0.0;                    // Energieverbrauch in kWh
  float power = 0.0;                     // Aktuelle Leistung in W
  long totalRuntime = 0;                 // Gesamtlaufzeit in Sekunden
  long currentRuntime = 0;               // Aktuelle Laufzeit in Sekunden
  bool dataValid = false;                // Daten sind gültig
};

SensorData sensorData;                   // Sensordaten

// ----- MQTT EVENT HANDLER -----
static esp_err_t mqtt_event_handler(esp_mqtt_event_handle_t event) {
  switch (event->event_id) {
    case MQTT_EVENT_CONNECTED:
      Serial.println("MQTT verbunden");
      mqttConnected = true;
      
      // Themen abonnieren
      String controlTopic = String(config.mqttTopic) + String(config.deviceName) + "/control";
      esp_mqtt_client_subscribe(mqttClient, controlTopic.c_str(), 0);
      
      // Verbindungsstatus veröffentlichen
      String statusTopic = String(config.mqttTopic) + String(config.deviceName) + "/status";
      esp_mqtt_client_publish(mqttClient, statusTopic.c_str(), "online", 0, 1, 1); // QoS 0, Retain
      break;
      
    case MQTT_EVENT_DISCONNECTED:
      Serial.println("MQTT getrennt");
      mqttConnected = false;
      break;
      
    case MQTT_EVENT_SUBSCRIBED:
      Serial.print("MQTT abonniert: ");
      Serial.println(event->topic);
      break;
      
    case MQTT_EVENT_UNSUBSCRIBED:
      Serial.println("MQTT Abonnement beendet");
      break;
      
    case MQTT_EVENT_PUBLISHED:
      // Nachricht erfolgreich veröffentlicht
      break;
      
    case MQTT_EVENT_DATA:
      handleMqttMessage(event);
      break;
      
    case MQTT_EVENT_ERROR:
      Serial.println("MQTT Fehler");
      break;
      
    default:
      break;
  }
  return ESP_OK;
}

// MQTT-Nachricht verarbeiten
void handleMqttMessage(esp_mqtt_event_handle_t event) {
  // Thema und Nutzlast als Strings kopieren
  char topic[128];
  char payload[512];
  
  strncpy(topic, event->topic, event->topic_len);
  topic[event->topic_len] = '\0';
  
  strncpy(payload, event->data, event->data_len);
  payload[event->data_len] = '\0';
  
  Serial.print("MQTT-Nachricht: ");
  Serial.print(topic);
  Serial.print(" = ");
  Serial.println(payload);
  
  // Kontrolldaten verarbeiten
  String controlTopic = String(config.mqttTopic) + String(config.deviceName) + "/control";
  
  if (String(topic) == controlTopic) {
    // JSON-Kontrolldaten analysieren
    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, payload);
    
    if (!error) {
      // Relais steuern
      if (doc.containsKey("relay")) {
        bool state = doc["relay"];
        setRelayState(state);
      }
      
      // Display-Seite ändern
      if (doc.containsKey("display_page")) {
        displayPage = doc["display_page"];
      }
      
      // Relais-Modus ändern
      if (doc.containsKey("relay_mode")) {
        config.relayMode = doc["relay_mode"];
        saveConfig();
      }
      
      // Schwellenwert ändern
      if (doc.containsKey("threshold")) {
        config.relayThreshold = doc["threshold"];
        saveConfig();
      }
    }
  }
}

// ----- FUNKTIONEN -----

// MQTT-Client initialisieren
void setupMQTT() {
  if (strlen(config.mqttServer) == 0) {
    mqttConnected = false;
    return;
  }
  
  char clientId[50];
  sprintf(clientId, "SwissAirDry-%08X", (uint32_t)ESP.getEfuseMac());
  
  esp_mqtt_client_config_t mqtt_cfg = {};
  mqtt_cfg.uri = config.mqttServer;
  mqtt_cfg.port = config.mqttPort;
  
  // Anmeldedaten, falls konfiguriert
  if (strlen(config.mqttUser) > 0) {
    mqtt_cfg.username = config.mqttUser;
    mqtt_cfg.password = config.mqttPassword;
  }
  
  mqtt_cfg.client_id = clientId;
  mqtt_cfg.keepalive = 15; // 15 Sekunden Keep-Alive
  mqtt_cfg.disable_auto_reconnect = false;
  mqtt_cfg.reconnect_timeout_ms = 2000; // 2 Sekunden
  
  mqttClient = esp_mqtt_client_init(&mqtt_cfg);
  esp_mqtt_client_register_event(mqttClient, MQTT_EVENT_ANY, (esp_event_handler_t)mqtt_event_handler, NULL);
  esp_mqtt_client_start(mqttClient);
  
  Serial.print("MQTT-Client initialisiert, verbinde mit ");
  Serial.println(config.mqttServer);
}

// MQTT-Daten veröffentlichen
void publishMqttData() {
  if (!mqttConnected) return;
  
  // JSON-Daten vorbereiten
  JsonDocument doc;
  doc["temperature"] = sensorData.temperature;
  doc["humidity"] = sensorData.humidity;
  doc["power"] = sensorData.power;
  doc["energy"] = sensorData.energy;
  doc["relay"] = relayState;
  doc["runtime"] = sensorData.currentRuntime;
  doc["total_runtime"] = sensorData.totalRuntime;
  
  char buffer[512];
  size_t n = serializeJson(doc, buffer);
  
  // Daten veröffentlichen
  String dataTopic = String(config.mqttTopic) + String(config.deviceName) + "/data";
  esp_mqtt_client_publish(mqttClient, dataTopic.c_str(), buffer, n, 0, 0);
}

// MQTT-Verbindung prüfen und ggf. wiederherstellen
void checkMqttConnection() {
  if (mqttConnected || !wifiConnected) return;
  
  // Nicht zu oft versuchen
  unsigned long now = millis();
  if ((now - lastMqttReconnect) < MQTT_RECONNECT_INTERVAL) return;
  
  lastMqttReconnect = now;
  
  // MQTT-Client neustarten
  esp_mqtt_client_reconnect(mqttClient);
}

// ----- SETUP -----
void setup() {
  // Serielle Schnittstelle initialisieren
  Serial.begin(115200);
  Serial.println("\nSwissAirDry ESP32-C6 mit Farbdisplay startet...");
  
  // Pins initialisieren
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);  // Relais aus
  
  // EEPROM initialisieren
  EEPROM.begin(EEPROM_SIZE);
  
  // Konfiguration laden
  loadConfig();
  
  // Display initialisieren
  tft.begin();
  tft.setRotation(3);  // Rotation einstellen (0-3) für 1.47" Display
  tft.fillScreen(COLOR_BACKGROUND);
  
  // Startbildschirm anzeigen
  showSplashScreen();
  
  // SD-Karte initialisieren
  initSDCard();
  
  // Mit WLAN verbinden oder AP-Modus starten
  if (!config.apMode && strlen(config.wifiSSID) > 0) {
    connectWiFi();
  } else {
    startAPMode();
  }
  
  // Webserver-Routen definieren
  setupWebServer();
  
  // MQTT initialisieren, wenn konfiguriert
  if (strlen(config.mqttServer) > 0) {
    setupMQTT();
  }
  
  // OTA initialisieren
  setupOTA();
  
  // Datenprotokollierung als separaten Task starten
  xTaskCreatePinnedToCore(
    dataLoggingTaskFunction,   // Task-Funktion
    "DataLogging",             // Name
    10000,                     // Stack-Größe
    NULL,                      // Parameter
    1,                         // Priorität
    &dataLoggingTask,          // Task-Handle
    0                          // Core
  );
  
  Serial.println("Setup abgeschlossen");
}

// ----- LOOP -----
void loop() {
  // DNS-Server für Captive Portal
  if (config.apMode) {
    dnsServer.processNextRequest();
  }
  
  // Webserver-Anfragen bearbeiten
  server.handleClient();
  
  // OTA-Updates prüfen
  ArduinoOTA.handle();
  
  // MQTT-Verbindung prüfen
  if (wifiConnected && strlen(config.mqttServer) > 0) {
    checkMqttConnection();
  }
  
  // WLAN-Verbindung überprüfen
  if (!config.apMode && WiFi.status() != WL_CONNECTED) {
    reconnectWiFi();
  }
  
  // Sensordaten lesen
  if (millis() - lastSensorRead >= SENSOR_READ_INTERVAL) {
    readSensors();
    lastSensorRead = millis();
    
    // MQTT-Daten veröffentlichen, wenn verbunden und Sensor-Daten gültig
    if (mqttConnected && sensorData.dataValid) {
      publishMqttData();
    }
  }
  
  // API aktualisieren
  if (wifiConnected && (millis() - lastApiUpdate >= API_UPDATE_INTERVAL)) {
    updateAPI();
    lastApiUpdate = millis();
  }
  
  // Display aktualisieren
  if (millis() - lastDisplayUpdate >= DISPLAY_UPDATE_INTERVAL) {
    updateDisplay();
    lastDisplayUpdate = millis();
  }
  
  // Relais-Steuerung basierend auf der Konfiguration
  controlRelay();
  
  // Kurze Pause zur CPU-Entlastung
  delay(10);
}

// ----- KONFIGURATION -----
// Konfiguration aus EEPROM laden
void loadConfig() {
  Serial.println("Lade Konfiguration...");
  
  if (EEPROM.read(0) == 'S' && EEPROM.read(1) == 'A' && EEPROM.read(2) == 'D') {
    // Konfiguration aus EEPROM lesen
    EEPROM.get(10, config);
    Serial.println("Konfiguration geladen");
  } else {
    // Standardkonfiguration verwenden
    Serial.println("Keine Konfiguration gefunden, verwende Standardwerte");
    
    // Eindeutige Geräte-ID generieren
    uint32_t chipId = (uint32_t)(ESP.getEfuseMac() >> 32);
    sprintf(config.deviceName, "SwissAirDry-%08X", chipId);
    
    // Konfiguration speichern
    saveConfig();
  }
}

// Konfiguration im EEPROM speichern
void saveConfig() {
  Serial.println("Speichere Konfiguration...");
  
  // Signatur schreiben
  EEPROM.write(0, 'S');
  EEPROM.write(1, 'A');
  EEPROM.write(2, 'D');
  
  // Konfiguration speichern
  EEPROM.put(10, config);
  EEPROM.commit();
  
  Serial.println("Konfiguration gespeichert");
}

// ----- NETZWERK -----
// Mit WLAN verbinden
void connectWiFi() {
  Serial.print("Verbinde mit WLAN ");
  Serial.print(config.wifiSSID);
  Serial.println("...");
  
  // Verbindungsstatus auf dem Display anzeigen
  tft.fillScreen(COLOR_BACKGROUND);
  tft.setTextColor(COLOR_TEXT, COLOR_BACKGROUND);
  tft.setTextSize(1);
  tft.setCursor(10, 10);
  tft.println("WLAN-Verbindung");
  tft.setCursor(10, 30);
  tft.print("SSID: ");
  tft.println(config.wifiSSID);
  
  // Mit WLAN verbinden
  WiFi.mode(WIFI_STA);
  WiFi.setHostname(config.deviceName);
  WiFi.begin(config.wifiSSID, config.wifiPassword);
  
  // Auf Verbindung warten
  int dots = 0;
  int timeout = 0;
  while (WiFi.status() != WL_CONNECTED && timeout < 20) {
    delay(500);
    Serial.print(".");
    
    // Fortschritt auf dem Display anzeigen
    tft.setCursor(10, 50);
    tft.print("Verbinde");
    for (int i = 0; i < dots; i++) {
      tft.print(".");
    }
    tft.print("     ");  // Um überschüssige Punkte zu löschen
    dots = (dots + 1) % 6;
    
    timeout++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    networkIP = WiFi.localIP().toString();
    
    Serial.println();
    Serial.print("Verbunden mit IP: ");
    Serial.println(networkIP);
    
    // Verbindung erfolgreich
    tft.fillRect(0, 50, tft.width(), 30, COLOR_BACKGROUND);
    tft.setCursor(10, 50);
    tft.setTextColor(COLOR_SUCCESS, COLOR_BACKGROUND);
    tft.print("Verbunden!");
    tft.setCursor(10, 70);
    tft.setTextColor(COLOR_TEXT, COLOR_BACKGROUND);
    tft.print("IP: ");
    tft.println(networkIP);
    delay(2000);  // Kurz anzeigen
  } else {
    wifiConnected = false;
    
    Serial.println();
    Serial.println("WLAN-Verbindung fehlgeschlagen");
    
    // Verbindung fehlgeschlagen
    tft.fillRect(0, 50, tft.width(), 30, COLOR_BACKGROUND);
    tft.setCursor(10, 50);
    tft.setTextColor(COLOR_ERROR, COLOR_BACKGROUND);
    tft.println("Verbindung fehlgeschlagen!");
    delay(2000);  // Kurz anzeigen
    
    // AP-Modus starten
    startAPMode();
  }
}

// AP-Modus starten
void startAPMode() {
  Serial.println("Starte Access Point...");
  
  // AP-Modus starten
  String apName = String(config.deviceName);
  WiFi.mode(WIFI_AP);
  WiFi.softAPConfig(CONFIG_AP_IP, CONFIG_AP_IP, IPAddress(255, 255, 255, 0));
  WiFi.softAP(apName.c_str(), DEFAULT_AP_PASSWORD);
  
  networkIP = WiFi.softAPIP().toString();
  config.apMode = true;
  configMode = true;
  
  Serial.print("AP gestartet. IP: ");
  Serial.println(networkIP);
  
  // DNS-Server starten, um alle Domains zum ESP umzuleiten (Captive Portal)
  dnsServer.start(DNS_PORT, "*", CONFIG_AP_IP);
  
  // AP-Informationen auf dem Display anzeigen
  tft.fillScreen(COLOR_BACKGROUND);
  tft.setTextColor(COLOR_TITLE, COLOR_BACKGROUND);
  tft.setTextSize(1);
  tft.setCursor(10, 10);
  tft.println("WLAN-Zugangspunkt");
  
  tft.setTextColor(COLOR_TEXT, COLOR_BACKGROUND);
  tft.setCursor(10, 30);
  tft.print("Name: ");
  tft.println(apName);
  tft.setCursor(10, 50);
  tft.print("Passwort: ");
  tft.println(DEFAULT_AP_PASSWORD);
  tft.setCursor(10, 70);
  tft.print("IP: ");
  tft.println(networkIP);
  
  // QR-Code für WLAN-Zugang anzeigen
  displayWifiQR(apName, DEFAULT_AP_PASSWORD);
}

// WiFi-Verbindung wiederherstellen
void reconnectWiFi() {
  static unsigned long lastReconnectAttempt = 0;
  
  // Nicht zu oft versuchen
  if (millis() - lastReconnectAttempt < 30000) return;
  
  lastReconnectAttempt = millis();
  
  Serial.println("WLAN-Verbindung verloren, versuche neu zu verbinden...");
  
  // Kurze Statusanzeige
  showToastMessage("WLAN-Verbindung wird wiederhergestellt...", COLOR_WARNING);
  
  // Verbindung neu herstellen
  WiFi.disconnect();
  delay(1000);
  WiFi.begin(config.wifiSSID, config.wifiPassword);
  
  // Kurz warten und Status prüfen
  delay(5000);
  
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    networkIP = WiFi.localIP().toString();
    showToastMessage("WLAN-Verbindung wiederhergestellt", COLOR_SUCCESS);
  } else {
    wifiConnected = false;
  }
}

// Relais-Status setzen
void setRelayState(bool state) {
  relayState = state;
  digitalWrite(RELAY_PIN, relayState ? HIGH : LOW);
  
  // Status auf dem Display aktualisieren
  updateDisplay();
  
  // MQTT-Status senden, wenn verbunden
  if (mqttConnected) {
    String stateTopic = String(config.mqttTopic) + String(config.deviceName) + "/relay";
    esp_mqtt_client_publish(mqttClient, stateTopic.c_str(), relayState ? "ON" : "OFF", 0, 1, 1);
  }
}

// Relais basierend auf der Konfiguration steuern
void controlRelay() {
  if (!config.relayEnabled) {
    if (relayState) setRelayState(false);
    return;
  }
  
  switch (config.relayMode) {
    case 0:  // Manueller Modus - keine Änderung
      break;
      
    case 1:  // Zeitgesteuerter Modus
      {
        // Aktuelle Zeit mit NTP
        struct tm timeinfo;
        if (!getLocalTime(&timeinfo)) {
          break;  // Keine gültige Zeit verfügbar
        }
        
        int currentHour = timeinfo.tm_hour;
        int currentMinute = timeinfo.tm_min;
        int currentTimeMinutes = currentHour * 60 + currentMinute;
        
        int onTimeMinutes = config.relayOnHour * 60 + config.relayOnMinute;
        int offTimeMinutes = config.relayOffHour * 60 + config.relayOffMinute;
        
        // Umschalten basierend auf der Zeit
        if (onTimeMinutes <= offTimeMinutes) {
          // Normaler Zeitbereich (z.B. 8:00 bis 18:00)
          if (currentTimeMinutes >= onTimeMinutes && currentTimeMinutes < offTimeMinutes) {
            if (!relayState) setRelayState(true);
          } else {
            if (relayState) setRelayState(false);
          }
        } else {
          // Über Mitternacht (z.B. 22:00 bis 6:00)
          if (currentTimeMinutes >= onTimeMinutes || currentTimeMinutes < offTimeMinutes) {
            if (!relayState) setRelayState(true);
          } else {
            if (relayState) setRelayState(false);
          }
        }
      }
      break;
      
    case 2:  // Sensorbasierter Modus
      if (sensorData.dataValid) {
        if (sensorData.humidity > config.relayThreshold && !relayState) {
          setRelayState(true);
        } else if (sensorData.humidity <= config.relayThreshold && relayState) {
          setRelayState(false);
        }
      }
      break;
  }
}

// OTA-Updates initialisieren
void setupOTA() {
  // Hostname für OTA-Updates festlegen
  ArduinoOTA.setHostname(config.deviceName);
  
  // OTA-Ereignisse
  ArduinoOTA.onStart([]() {
    String type;
    if (ArduinoOTA.getCommand() == U_FLASH) {
      type = "Firmware";
    } else {
      type = "Dateisystem";
    }
    
    Serial.println("OTA-Update beginnt: " + type);
    tft.fillScreen(COLOR_BACKGROUND);
    tft.setTextColor(COLOR_WARNING, COLOR_BACKGROUND);
    tft.setTextSize(1);
    tft.setCursor(10, 10);
    tft.println("OTA-Update");
    tft.setCursor(10, 30);
    tft.println("Update läuft...");
  });
  
  ArduinoOTA.onEnd([]() {
    Serial.println("\nOTA-Update abgeschlossen");
    tft.fillScreen(COLOR_BACKGROUND);
    tft.setTextColor(COLOR_SUCCESS, COLOR_BACKGROUND);
    tft.setTextSize(1);
    tft.setCursor(10, 10);
    tft.println("OTA-Update");
    tft.setCursor(10, 30);
    tft.println("Update erfolgreich!");
    tft.setCursor(10, 50);
    tft.println("Neustart...");
  });
  
  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    static int lastPercentage = 0;
    int percentage = (progress / (total / 100));
    
    if (percentage != lastPercentage) {
      lastPercentage = percentage;
      Serial.printf("Fortschritt: %u%%\r", percentage);
      
      // Fortschrittsbalken anzeigen
      tft.fillRect(10, 60, percentage * 1.5, 10, COLOR_INFO);
      tft.fillRect(10 + percentage * 1.5, 60, 150 - percentage * 1.5, 10, COLOR_BACKGROUND);
      
      // Prozentsatz anzeigen
      tft.fillRect(70, 80, 50, 20, COLOR_BACKGROUND);
      tft.setCursor(70, 80);
      tft.setTextColor(COLOR_TEXT, COLOR_BACKGROUND);
      tft.print(percentage);
      tft.print("%");
    }
  });
  
  ArduinoOTA.onError([](ota_error_t error) {
    Serial.printf("OTA-Fehler[%u]: ", error);
    String errorMsg;
    
    switch (error) {
      case OTA_AUTH_ERROR:
        errorMsg = "Authentifizierungsfehler";
        break;
      case OTA_BEGIN_ERROR:
        errorMsg = "Begin-Fehler";
        break;
      case OTA_CONNECT_ERROR:
        errorMsg = "Verbindungsfehler";
        break;
      case OTA_RECEIVE_ERROR:
        errorMsg = "Empfangsfehler";
        break;
      case OTA_END_ERROR:
        errorMsg = "End-Fehler";
        break;
      default:
        errorMsg = "Unbekannter Fehler";
    }
    
    Serial.println(errorMsg);
    
    tft.fillScreen(COLOR_BACKGROUND);
    tft.setTextColor(COLOR_ERROR, COLOR_BACKGROUND);
    tft.setTextSize(1);
    tft.setCursor(10, 10);
    tft.println("OTA-Fehler");
    tft.setCursor(10, 30);
    tft.println(errorMsg);
  });
  
  ArduinoOTA.begin();
  Serial.println("OTA-Updates bereit");
}

// SD-Karte initialisieren
void initSDCard() {
  Serial.print("Initialisiere SD-Karte... ");
  
  if (!SD.begin(SD_CS_PIN)) {
    Serial.println("Fehler");
    sdCardAvailable = false;
    return;
  }
  
  uint64_t cardSize = SD.cardSize() / (1024 * 1024);
  Serial.print("OK (");
  Serial.print(cardSize);
  Serial.println(" MB)");
  
  sdCardAvailable = true;
  
  // Verzeichnisstruktur prüfen und erstellen
  if (!SD.exists("/logs")) {
    SD.mkdir("/logs");
    Serial.println("Logs-Verzeichnis erstellt");
  }
}

// Sensordaten lesen
void readSensors() {
  // TODO: Hier die tatsächliche Sensorauslesung implementieren
  
  // Beispieldaten für Testzwecke
  sensorData.temperature += random(-100, 100) / 100.0;
  if (sensorData.temperature < 15.0) sensorData.temperature = 15.0;
  if (sensorData.temperature > 30.0) sensorData.temperature = 30.0;
  
  sensorData.humidity += random(-100, 100) / 100.0;
  if (sensorData.humidity < 40.0) sensorData.humidity = 40.0;
  if (sensorData.humidity > 80.0) sensorData.humidity = 80.0;
  
  if (relayState) {
    sensorData.power = 1000 + random(-50, 50);
    sensorData.energy += sensorData.power / 3600.0 / 1000.0 * (SENSOR_READ_INTERVAL / 1000.0);
    sensorData.currentRuntime += SENSOR_READ_INTERVAL / 1000;
    sensorData.totalRuntime += SENSOR_READ_INTERVAL / 1000;
  } else {
    sensorData.power = 0;
    sensorData.currentRuntime = 0;
  }
  
  sensorData.dataValid = true;
}

// API aktualisieren
void updateAPI() {
  if (!wifiConnected || strlen(config.apiServer) == 0) return;
  
  Serial.println("API-Update wird gesendet...");
  
  HTTPClient http;
  
  // Verbindung aufbauen
  String url = String(config.apiServer);
  if (!url.startsWith("http")) {
    url = "http://" + url;
  }
  url += "/api/v1/device/update";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", config.apiKey);
  
  // JSON-Daten vorbereiten
  JsonDocument doc;
  JsonObject device = doc.createNestedObject("device");
  device["id"] = config.deviceName;
  device["ip"] = networkIP;
  device["uptime"] = millis() / 1000;
  device["version"] = firmwareVersion;
  
  JsonObject data = doc.createNestedObject("data");
  data["temperature"] = sensorData.temperature;
  data["humidity"] = sensorData.humidity;
  data["power"] = sensorData.power;
  data["energy"] = sensorData.energy;
  data["relay_state"] = relayState;
  data["runtime"] = sensorData.currentRuntime;
  data["total_runtime"] = sensorData.totalRuntime;
  
  String requestBody;
  serializeJson(doc, requestBody);
  
  // Anfrage senden
  int httpCode = http.POST(requestBody);
  
  // Antwort überprüfen
  if (httpCode > 0) {
    Serial.printf("API-Antwort: %d\n", httpCode);
    
    if (httpCode == HTTP_CODE_OK) {
      String payload = http.getString();
      Serial.println("API-Antwort: " + payload);
      
      // JSON-Antwort analysieren
      JsonDocument response;
      DeserializationError error = deserializeJson(response, payload);
      
      if (!error) {
        // Befehle ausführen, falls vorhanden
        if (response.containsKey("commands")) {
          JsonArray commands = response["commands"];
          
          for (JsonObject command : commands) {
            if (command.containsKey("type") && command.containsKey("value")) {
              String type = command["type"];
              
              if (type == "relay") {
                bool state = command["value"];
                setRelayState(state);
              } else if (type == "display_page") {
                displayPage = command["value"];
              } else if (type == "reset") {
                ESP.restart();
              }
            }
          }
        }
      }
    }
  } else {
    Serial.printf("API-Fehler: %s\n", http.errorToString(httpCode).c_str());
  }
  
  http.end();
}

// Startbildschirm anzeigen
void showSplashScreen() {
  tft.fillScreen(COLOR_BACKGROUND);
  
  // Logo (vereinfacht)
  int centerX = tft.width() / 2;
  int centerY = tft.height() / 3;
  
  // Kreis zeichnen
  tft.fillCircle(centerX, centerY, 40, COLOR_TITLE);
  tft.fillCircle(centerX, centerY, 35, COLOR_BACKGROUND);
  
  // Text zeichnen
  tft.setTextColor(COLOR_TITLE, COLOR_BACKGROUND);
  tft.setTextSize(2);
  tft.setCursor(centerX - 70, centerY + 50);
  tft.println("SwissAirDry");
  
  tft.setTextColor(COLOR_TEXT, COLOR_BACKGROUND);
  tft.setTextSize(1);
  tft.setCursor(centerX - 50, centerY + 75);
  tft.println("Version " + firmwareVersion);
  
  delay(2000);
}

// Display aktualisieren
void updateDisplay() {
  // Verschiedene Seiten implementieren
  switch (displayPage) {
    case 0:
      displayMainPage();
      break;
    case 1:
      displaySensorPage();
      break;
    case 2:
      displayEnergyPage();
      break;
    case 3:
      displayInfoPage();
      break;
    default:
      displayPage = 0;
      displayMainPage();
  }
}

// Hauptseite anzeigen
void displayMainPage() {
  tft.fillScreen(COLOR_BACKGROUND);
  
  // Titel
  tft.setTextColor(COLOR_TITLE, COLOR_BACKGROUND);
  tft.setTextSize(2);
  tft.setCursor(10, 10);
  tft.println("SwissAirDry");
  
  // Statusinformationen
  tft.setTextColor(COLOR_TEXT, COLOR_BACKGROUND);
  tft.setTextSize(1);
  
  // Netzwerkstatus
  tft.setCursor(10, 40);
  tft.print("Netzwerk: ");
  if (wifiConnected) {
    tft.setTextColor(COLOR_SUCCESS, COLOR_BACKGROUND);
    tft.println("Verbunden");
  } else {
    tft.setTextColor(COLOR_WARNING, COLOR_BACKGROUND);
    tft.println("AP-Modus");
  }
  
  // IP-Adresse
  tft.setTextColor(COLOR_TEXT, COLOR_BACKGROUND);
  tft.setCursor(10, 55);
  tft.print("IP: ");
  tft.println(networkIP);
  
  // MQTT-Status
  tft.setCursor(10, 70);
  tft.print("MQTT: ");
  if (mqttConnected) {
    tft.setTextColor(COLOR_SUCCESS, COLOR_BACKGROUND);
    tft.println("Verbunden");
  } else {
    tft.setTextColor(COLOR_ERROR, COLOR_BACKGROUND);
    tft.println("Getrennt");
  }
  
  // Relaisstatus
  tft.setTextColor(COLOR_TEXT, COLOR_BACKGROUND);
  tft.setCursor(10, 95);
  tft.print("Relais: ");
  if (relayState) {
    tft.setTextColor(COLOR_SUCCESS, COLOR_BACKGROUND);
    tft.println("AN");
  } else {
    tft.setTextColor(COLOR_ERROR, COLOR_BACKGROUND);
    tft.println("AUS");
  }
  
  // Aktuelle Sensorwerte
  tft.setTextColor(COLOR_TEXT, COLOR_BACKGROUND);
  tft.setCursor(10, 120);
  tft.print("Temperatur: ");
  tft.print(sensorData.temperature, 1);
  tft.println(" C");
  
  tft.setCursor(10, 135);
  tft.print("Feuchtigkeit: ");
  tft.print(sensorData.humidity, 1);
  tft.println(" %");
  
  // Leistung anzeigen
  tft.setCursor(10, 150);
  tft.print("Leistung: ");
  tft.print(sensorData.power, 0);
  tft.println(" W");
  
  // Statusleiste unten
  tft.fillRect(0, tft.height() - 20, tft.width(), 20, COLOR_STATUS_BAR);
  tft.setTextColor(COLOR_TEXT, COLOR_STATUS_BAR);
  tft.setCursor(5, tft.height() - 15);
  tft.print(config.deviceName);
  
  // Uhrzeit (falls verfügbar)
  struct tm timeinfo;
  if (getLocalTime(&timeinfo)) {
    char timeString[9];
    sprintf(timeString, "%02d:%02d:%02d", timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec);
    
    tft.setCursor(tft.width() - 60, tft.height() - 15);
    tft.print(timeString);
  }
}

// Sensorseite anzeigen
void displaySensorPage() {
  tft.fillScreen(COLOR_BACKGROUND);
  
  // Titel
  tft.setTextColor(COLOR_TITLE, COLOR_BACKGROUND);
  tft.setTextSize(2);
  tft.setCursor(10, 10);
  tft.println("Sensordaten");
  
  // Detaillierte Sensorinformationen
  tft.setTextColor(COLOR_TEXT, COLOR_BACKGROUND);
  tft.setTextSize(1);
  
  tft.setCursor(10, 40);
  tft.print("Temperatur: ");
  tft.print(sensorData.temperature, 1);
  tft.println(" C");
  
  tft.setCursor(10, 55);
  tft.print("Feuchtigkeit: ");
  tft.print(sensorData.humidity, 1);
  tft.println(" %");
  
  // Relaisstatus
  tft.setCursor(10, 80);
  tft.print("Relais Status: ");
  if (relayState) {
    tft.setTextColor(COLOR_SUCCESS, COLOR_BACKGROUND);
    tft.println("AN");
    tft.setTextColor(COLOR_TEXT, COLOR_BACKGROUND);
    
    // Laufzeit anzeigen
    tft.setCursor(10, 95);
    tft.print("Aktuelle Laufzeit: ");
    
    // Laufzeit formatieren
    int hours = sensorData.currentRuntime / 3600;
    int minutes = (sensorData.currentRuntime % 3600) / 60;
    int seconds = sensorData.currentRuntime % 60;
    
    char runtime[12];
    sprintf(runtime, "%02d:%02d:%02d", hours, minutes, seconds);
    tft.println(runtime);
  } else {
    tft.setTextColor(COLOR_ERROR, COLOR_BACKGROUND);
    tft.println("AUS");
    tft.setTextColor(COLOR_TEXT, COLOR_BACKGROUND);
  }
  
  // Relais-Modus
  tft.setCursor(10, 120);
  tft.print("Relais-Modus: ");
  switch (config.relayMode) {
    case 0:
      tft.println("Manuell");
      break;
    case 1:
      tft.println("Zeit");
      // Zeiteinstellungen anzeigen
      tft.setCursor(20, 135);
      tft.printf("AN: %02d:%02d, AUS: %02d:%02d", 
          config.relayOnHour, config.relayOnMinute,
          config.relayOffHour, config.relayOffMinute);
      break;
    case 2:
      tft.println("Sensor");
      // Schwellenwert anzeigen
      tft.setCursor(20, 135);
      tft.print("Schwelle: ");
      tft.print(config.relayThreshold, 1);
      tft.println(" %");
      break;
  }
  
  // Statusleiste
  tft.fillRect(0, tft.height() - 20, tft.width(), 20, COLOR_STATUS_BAR);
  tft.setTextColor(COLOR_TEXT, COLOR_STATUS_BAR);
  tft.setCursor(5, tft.height() - 15);
  tft.print("Seite 2/4");
  
  // Seitennavigation
  tft.setCursor(tft.width() - 60, tft.height() - 15);
  tft.print("<< >>");
}

// Energieseite anzeigen
void displayEnergyPage() {
  tft.fillScreen(COLOR_BACKGROUND);
  
  // Titel
  tft.setTextColor(COLOR_TITLE, COLOR_BACKGROUND);
  tft.setTextSize(2);
  tft.setCursor(10, 10);
  tft.println("Energie");
  
  // Energiedaten
  tft.setTextColor(COLOR_TEXT, COLOR_BACKGROUND);
  tft.setTextSize(1);
  
  tft.setCursor(10, 40);
  tft.print("Aktuelle Leistung: ");
  tft.print(sensorData.power, 0);
  tft.println(" W");
  
  tft.setCursor(10, 55);
  tft.print("Energieverbrauch: ");
  tft.print(sensorData.energy, 3);
  tft.println(" kWh");
  
  // Gesamtlaufzeit
  tft.setCursor(10, 80);
  tft.print("Gesamtlaufzeit: ");
  
  // Laufzeit formatieren
  int days = sensorData.totalRuntime / 86400;
  int hours = (sensorData.totalRuntime % 86400) / 3600;
  int minutes = (sensorData.totalRuntime % 3600) / 60;
  
  if (days > 0) {
    tft.print(days);
    tft.print(" T ");
  }
  
  tft.print(hours);
  tft.print(" Std ");
  tft.print(minutes);
  tft.println(" Min");
  
  // Zusätzliche Berechnungen
  float energyCost = sensorData.energy * 0.30; // 0,30 € pro kWh
  
  tft.setCursor(10, 105);
  tft.print("Energiekosten: ");
  tft.print(energyCost, 2);
  tft.println(" EUR");
  
  // Berechnung der CO2-Einsparung (vereinfacht)
  float co2Saved = sensorData.energy * 0.5; // 0,5 kg CO2 pro kWh
  
  tft.setCursor(10, 120);
  tft.print("CO2-Einsparung: ");
  tft.print(co2Saved, 2);
  tft.println(" kg");
  
  // Statusleiste
  tft.fillRect(0, tft.height() - 20, tft.width(), 20, COLOR_STATUS_BAR);
  tft.setTextColor(COLOR_TEXT, COLOR_STATUS_BAR);
  tft.setCursor(5, tft.height() - 15);
  tft.print("Seite 3/4");
  
  // Seitennavigation
  tft.setCursor(tft.width() - 60, tft.height() - 15);
  tft.print("<< >>");
}

// Infoseite anzeigen
void displayInfoPage() {
  tft.fillScreen(COLOR_BACKGROUND);
  
  // Titel
  tft.setTextColor(COLOR_TITLE, COLOR_BACKGROUND);
  tft.setTextSize(2);
  tft.setCursor(10, 10);
  tft.println("Information");
  
  // Geräteinformationen
  tft.setTextColor(COLOR_TEXT, COLOR_BACKGROUND);
  tft.setTextSize(1);
  
  tft.setCursor(10, 40);
  tft.print("Geräte-ID: ");
  tft.println(config.deviceName);
  
  tft.setCursor(10, 55);
  tft.print("Firmware: v");
  tft.println(firmwareVersion);
  
  tft.setCursor(10, 70);
  tft.print("IP-Adresse: ");
  tft.println(networkIP);
  
  // SD-Karte
  tft.setCursor(10, 95);
  tft.print("SD-Karte: ");
  if (sdCardAvailable) {
    tft.setTextColor(COLOR_SUCCESS, COLOR_BACKGROUND);
    tft.println("Vorhanden");
    tft.setTextColor(COLOR_TEXT, COLOR_BACKGROUND);
    
    // Speicherplatz anzeigen (wenn verfügbar)
    uint64_t cardSize = SD.cardSize() / (1024 * 1024);
    tft.setCursor(20, 110);
    tft.print("Größe: ");
    tft.print(cardSize);
    tft.println(" MB");
  } else {
    tft.setTextColor(COLOR_ERROR, COLOR_BACKGROUND);
    tft.println("Nicht gefunden");
    tft.setTextColor(COLOR_TEXT, COLOR_BACKGROUND);
  }
  
  // Uptime
  tft.setCursor(10, 130);
  tft.print("Betriebszeit: ");
  
  // Uptime formatieren
  unsigned long uptime = millis() / 1000;
  int days = uptime / 86400;
  int hours = (uptime % 86400) / 3600;
  int minutes = (uptime % 3600) / 60;
  int seconds = uptime % 60;
  
  char uptimeStr[20];
  if (days > 0) {
    sprintf(uptimeStr, "%dd %02d:%02d:%02d", days, hours, minutes, seconds);
  } else {
    sprintf(uptimeStr, "%02d:%02d:%02d", hours, minutes, seconds);
  }
  tft.println(uptimeStr);
  
  // QR-Code für Konfigurationsseite anzeigen
  tft.setCursor(10, 150);
  tft.println("Konfiguration:");
  displayConfigQR();
  
  // Statusleiste
  tft.fillRect(0, tft.height() - 20, tft.width(), 20, COLOR_STATUS_BAR);
  tft.setTextColor(COLOR_TEXT, COLOR_STATUS_BAR);
  tft.setCursor(5, tft.height() - 15);
  tft.print("Seite 4/4");
  
  // Seitennavigation
  tft.setCursor(tft.width() - 60, tft.height() - 15);
  tft.print("<< >>");
}

// QR-Code für WLAN-Zugang anzeigen
void displayWifiQR(String ssid, String password) {
  // WLAN-URL im Format: WIFI:S:<SSID>;T:WPA;P:<PASSWORD>;;
  String qrData = "WIFI:S:" + ssid + ";T:WPA;P:" + password + ";;";
  
  // QR-Code generieren
  QRCode qrcode;
  uint8_t qrcodeData[qrcode_getBufferSize(3)];
  qrcode_initText(&qrcode, qrcodeData, 3, 0, qrData.c_str());
  
  // QR-Code anzeigen
  int scale = QR_CODE_SIZE;
  int xOffset = tft.width() - qrcode.size * scale - 10;
  int yOffset = tft.height() / 2 - qrcode.size * scale / 2;
  
  for (int y = 0; y < qrcode.size; y++) {
    for (int x = 0; x < qrcode.size; x++) {
      if (qrcode_getModule(&qrcode, x, y)) {
        tft.fillRect(xOffset + x * scale, yOffset + y * scale, scale, scale, COLOR_TEXT);
      } else {
        tft.fillRect(xOffset + x * scale, yOffset + y * scale, scale, scale, COLOR_BACKGROUND);
      }
    }
  }
}

// QR-Code für Konfigurationsseite anzeigen
void displayConfigQR() {
  // URL im Format: http://IP
  String qrData = "http://" + networkIP;
  
  // QR-Code generieren
  QRCode qrcode;
  uint8_t qrcodeData[qrcode_getBufferSize(2)];
  qrcode_initText(&qrcode, qrcodeData, 2, 0, qrData.c_str());
  
  // QR-Code anzeigen
  int scale = 2;
  int xOffset = tft.width() - qrcode.size * scale - 10;
  int yOffset = 120;
  
  for (int y = 0; y < qrcode.size; y++) {
    for (int x = 0; x < qrcode.size; x++) {
      if (qrcode_getModule(&qrcode, x, y)) {
        tft.fillRect(xOffset + x * scale, yOffset + y * scale, scale, scale, COLOR_TEXT);
      } else {
        tft.fillRect(xOffset + x * scale, yOffset + y * scale, scale, scale, COLOR_BACKGROUND);
      }
    }
  }
}

// Statusmeldung anzeigen
void showToastMessage(String message, uint16_t color) {
  // Aktuellen Displayinhalt speichern ist nicht möglich,
  // daher nur eine einfache Überlagerung
  int boxWidth = tft.width() - 20;
  int boxHeight = 30;
  int boxX = 10;
  int boxY = tft.height() / 2 - boxHeight / 2;
  
  // Box zeichnen
  tft.fillRoundRect(boxX, boxY, boxWidth, boxHeight, 5, COLOR_STATUS_BAR);
  tft.drawRoundRect(boxX, boxY, boxWidth, boxHeight, 5, color);
  
  // Text anzeigen
  tft.setTextColor(color, COLOR_STATUS_BAR);
  tft.setTextSize(1);
  
  // Text zentrieren
  int16_t x1, y1;
  uint16_t w, h;
  tft.getTextBounds(message, 0, 0, &x1, &y1, &w, &h);
  int textX = boxX + (boxWidth - w) / 2;
  int textY = boxY + (boxHeight - h) / 2 + h;
  
  tft.setCursor(textX, textY);
  tft.print(message);
  
  // Kurz anzeigen
  delay(2000);
  
  // Display neu zeichnen
  updateDisplay();
}

// ----- WEBSERVER -----
void setupWebServer() {
  // Webserver-Routen definieren
  server.on("/", handleRoot);
  server.on("/config", handleConfig);
  server.on("/save", HTTP_POST, handleSave);
  server.on("/restart", handleRestart);
  server.on("/reset", handleReset);
  server.on("/update", HTTP_GET, handleUpdateForm);
  server.on("/update", HTTP_POST, handleUpdateResult, handleUpdateUpload);
  server.on("/toggle", handleToggle);
  server.on("/data", handleData);
  server.on("/logs", handleLogs);
  server.on("/style.css", handleCSS);
  server.on("/script.js", handleJS);
  
  // Captive Portal - alle nicht definierten Adressen umleiten
  server.onNotFound([]() {
    if (captivePortal()) { return; }
    handleNotFound();
  });
  
  // Webserver starten
  server.begin();
  Serial.println("Webserver gestartet");
}

// Captive Portal Umleitung
bool captivePortal() {
  if (!config.apMode) return false;
  
  // Wenn es sich nicht um eine IP-Adresse handelt, zum Portal umleiten
  if (server.hostHeader() != networkIP) {
    server.sendHeader("Location", String("http://") + networkIP, true);
    server.send(302, "text/plain", "");
    return true;
  }
  return false;
}

// Hauptseite anzeigen
void handleRoot() {
  String html = "<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1'>";
  html += "<title>SwissAirDry - " + String(config.deviceName) + "</title>";
  html += "<link rel='stylesheet' href='/style.css'>";
  html += "</head><body>";
  html += "<div class='container'>";
  html += "<h1>SwissAirDry</h1>";
  html += "<h2>" + String(config.deviceName) + "</h2>";
  
  // Status-Informationen
  html += "<div class='status-card'>";
  html += "<h3>Status</h3>";
  html += "<p>Firmware: v" + firmwareVersion + "</p>";
  html += "<p>Netzwerk: " + (wifiConnected ? "Verbunden mit " + String(config.wifiSSID) : "AP-Modus") + "</p>";
  html += "<p>IP: " + networkIP + "</p>";
  html += "<p>MQTT: " + String(mqttConnected ? "Verbunden" : "Nicht verbunden") + "</p>";
  html += "<p>SD-Karte: " + String(sdCardAvailable ? "Vorhanden" : "Nicht gefunden") + "</p>";
  html += "</div>";
  
  // Aktuelle Sensordaten
  html += "<div class='data-card'>";
  html += "<h3>Sensordaten</h3>";
  if (sensorData.dataValid) {
    html += "<p>Temperatur: " + String(sensorData.temperature, 1) + " °C</p>";
    html += "<p>Luftfeuchtigkeit: " + String(sensorData.humidity, 1) + " %</p>";
    
    if (config.energySensor) {
      html += "<p>Leistung: " + String(sensorData.power, 0) + " W</p>";
      html += "<p>Energieverbrauch: " + String(sensorData.energy, 3) + " kWh</p>";
    }
    
    // Laufzeit formatieren
    int hours = sensorData.totalRuntime / 3600;
    int minutes = (sensorData.totalRuntime % 3600) / 60;
    
    html += "<p>Gesamtlaufzeit: " + String(hours) + " Std " + String(minutes) + " Min</p>";
  } else {
    html += "<p>Keine gültigen Daten verfügbar</p>";
  }
  html += "</div>";
  
  // Relais-Steuerung
  html += "<div class='control-card'>";
  html += "<h3>Relais</h3>";
  html += "<p>Status: <span id='relayStatus'>" + String(relayState ? "AN" : "AUS") + "</span></p>";
  html += "<p>Modus: ";
  switch (config.relayMode) {
    case 0: html += "Manuell"; break;
    case 1: html += "Zeit"; break;
    case 2: html += "Sensor"; break;
  }
  html += "</p>";
  html += "<a href='/toggle' class='button " + String(relayState ? "red" : "green") + "' id='toggleButton'>" + String(relayState ? "Ausschalten" : "Einschalten") + "</a>";
  html += "</div>";
  
  // Navigation
  html += "<div class='nav-buttons'>";
  html += "<a href='/config' class='button'>Konfiguration</a>";
  html += "<a href='/logs' class='button'>Protokolle</a>";
  html += "<a href='/update' class='button'>Firmware Update</a>";
  html += "</div>";
  
  // Live-Daten-Aktualisierung per JavaScript
  html += "<script src='/script.js'></script>";
  html += "</div></body></html>";
  
  server.send(200, "text/html", html);
}

// Konfigurationsseite anzeigen
void handleConfig() {
  // Einfache Implementierung - kann erweitert werden
  String html = "<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1'>";
  html += "<title>SwissAirDry - Konfiguration</title>";
  html += "<link rel='stylesheet' href='/style.css'>";
  html += "</head><body>";
  html += "<div class='container'>";
  html += "<h1>Konfiguration</h1>";
  
  html += "<form action='/save' method='post'>";
  
  // Geräteeinstellungen
  html += "<div class='config-section'>";
  html += "<h2>Geräteeinstellungen</h2>";
  html += "<div class='form-group'>";
  html += "<label for='deviceName'>Gerätename:</label>";
  html += "<input type='text' id='deviceName' name='deviceName' value='" + String(config.deviceName) + "'>";
  html += "</div>";
  html += "</div>";
  
  // WLAN-Einstellungen
  html += "<div class='config-section'>";
  html += "<h2>WLAN-Einstellungen</h2>";
  html += "<div class='form-group'>";
  html += "<label for='wifiSSID'>WLAN-Name:</label>";
  html += "<input type='text' id='wifiSSID' name='wifiSSID' value='" + String(config.wifiSSID) + "'>";
  html += "</div>";
  html += "<div class='form-group'>";
  html += "<label for='wifiPassword'>WLAN-Passwort:</label>";
  html += "<input type='password' id='wifiPassword' name='wifiPassword' value='" + String(config.wifiPassword) + "'>";
  html += "</div>";
  html += "<div class='form-group'>";
  html += "<label for='apMode'>AP-Modus:</label>";
  html += "<input type='checkbox' id='apMode' name='apMode' " + String(config.apMode ? "checked" : "") + ">";
  html += "</div>";
  html += "</div>";
  
  // MQTT-Einstellungen
  html += "<div class='config-section'>";
  html += "<h2>MQTT-Einstellungen</h2>";
  html += "<div class='form-group'>";
  html += "<label for='mqttServer'>MQTT-Server:</label>";
  html += "<input type='text' id='mqttServer' name='mqttServer' value='" + String(config.mqttServer) + "'>";
  html += "</div>";
  html += "<div class='form-group'>";
  html += "<label for='mqttPort'>MQTT-Port:</label>";
  html += "<input type='number' id='mqttPort' name='mqttPort' value='" + String(config.mqttPort) + "'>";
  html += "</div>";
  html += "<div class='form-group'>";
  html += "<label for='mqttUser'>MQTT-Benutzername:</label>";
  html += "<input type='text' id='mqttUser' name='mqttUser' value='" + String(config.mqttUser) + "'>";
  html += "</div>";
  html += "<div class='form-group'>";
  html += "<label for='mqttPassword'>MQTT-Passwort:</label>";
  html += "<input type='password' id='mqttPassword' name='mqttPassword' value='" + String(config.mqttPassword) + "'>";
  html += "</div>";
  html += "<div class='form-group'>";
  html += "<label for='mqttTopic'>MQTT-Basistopic:</label>";
  html += "<input type='text' id='mqttTopic' name='mqttTopic' value='" + String(config.mqttTopic) + "'>";
  html += "</div>";
  html += "</div>";
  
  // API-Einstellungen
  html += "<div class='config-section'>";
  html += "<h2>API-Einstellungen</h2>";
  html += "<div class='form-group'>";
  html += "<label for='apiServer'>API-Server:</label>";
  html += "<input type='text' id='apiServer' name='apiServer' value='" + String(config.apiServer) + "'>";
  html += "</div>";
  html += "<div class='form-group'>";
  html += "<label for='apiKey'>API-Schlüssel:</label>";
  html += "<input type='text' id='apiKey' name='apiKey' value='" + String(config.apiKey) + "'>";
  html += "</div>";
  html += "<div class='form-group'>";
  html += "<label for='apiUpdateInterval'>Update-Intervall (Sekunden):</label>";
  html += "<input type='number' id='apiUpdateInterval' name='apiUpdateInterval' value='" + String(config.apiUpdateInterval) + "'>";
  html += "</div>";
  html += "</div>";
  
  // Relais-Einstellungen
  html += "<div class='config-section'>";
  html += "<h2>Relais-Einstellungen</h2>";
  html += "<div class='form-group'>";
  html += "<label for='relayEnabled'>Relais aktiviert:</label>";
  html += "<input type='checkbox' id='relayEnabled' name='relayEnabled' " + String(config.relayEnabled ? "checked" : "") + ">";
  html += "</div>";
  html += "<div class='form-group'>";
  html += "<label for='relayMode'>Relais-Modus:</label>";
  html += "<select id='relayMode' name='relayMode'>";
  html += "<option value='0' " + String(config.relayMode == 0 ? "selected" : "") + ">Manuell</option>";
  html += "<option value='1' " + String(config.relayMode == 1 ? "selected" : "") + ">Zeit</option>";
  html += "<option value='2' " + String(config.relayMode == 2 ? "selected" : "") + ">Sensor</option>";
  html += "</select>";
  html += "</div>";
  
  // Zeitsteuerung
  html += "<div id='timeControls' " + String(config.relayMode != 1 ? "style='display:none;'" : "") + ">";
  html += "<div class='form-group'>";
  html += "<label for='relayOnHour'>Einschaltzeit:</label>";
  html += "<input type='number' id='relayOnHour' name='relayOnHour' min='0' max='23' value='" + String(config.relayOnHour) + "'>";
  html += ":<input type='number' id='relayOnMinute' name='relayOnMinute' min='0' max='59' value='" + String(config.relayOnMinute) + "'>";
  html += "</div>";
  html += "<div class='form-group'>";
  html += "<label for='relayOffHour'>Ausschaltzeit:</label>";
  html += "<input type='number' id='relayOffHour' name='relayOffHour' min='0' max='23' value='" + String(config.relayOffHour) + "'>";
  html += ":<input type='number' id='relayOffMinute' name='relayOffMinute' min='0' max='59' value='" + String(config.relayOffMinute) + "'>";
  html += "</div>";
  html += "</div>";
  
  // Sensorbasierte Steuerung
  html += "<div id='sensorControls' " + String(config.relayMode != 2 ? "style='display:none;'" : "") + ">";
  html += "<div class='form-group'>";
  html += "<label for='relayThreshold'>Feuchtigkeitsschwelle (%):</label>";
  html += "<input type='number' id='relayThreshold' name='relayThreshold' min='0' max='100' step='0.1' value='" + String(config.relayThreshold) + "'>";
  html += "</div>";
  html += "</div>";
  html += "</div>";
  
  // Sensoreinstellungen
  html += "<div class='config-section'>";
  html += "<h2>Sensoreinstellungen</h2>";
  html += "<div class='form-group'>";
  html += "<label for='temperatureSensor'>Temperatursensor:</label>";
  html += "<input type='checkbox' id='temperatureSensor' name='temperatureSensor' " + String(config.temperatureSensor ? "checked" : "") + ">";
  html += "</div>";
  html += "<div class='form-group'>";
  html += "<label for='humiditySensor'>Feuchtigkeitssensor:</label>";
  html += "<input type='checkbox' id='humiditySensor' name='humiditySensor' " + String(config.humiditySensor ? "checked" : "") + ">";
  html += "</div>";
  html += "<div class='form-group'>";
  html += "<label for='energySensor'>Energiesensor:</label>";
  html += "<input type='checkbox' id='energySensor' name='energySensor' " + String(config.energySensor ? "checked" : "") + ">";
  html += "</div>";
  html += "<div class='form-group'>";
  html += "<label for='sensorReadInterval'>Leseintervall (Sekunden):</label>";
  html += "<input type='number' id='sensorReadInterval' name='sensorReadInterval' min='1' max='3600' value='" + String(config.sensorReadInterval) + "'>";
  html += "</div>";
  html += "</div>";
  
  // Logging-Einstellungen
  html += "<div class='config-section'>";
  html += "<h2>Logging-Einstellungen</h2>";
  html += "<div class='form-group'>";
  html += "<label for='sdLogging'>SD-Kartenprotokollierung:</label>";
  html += "<input type='checkbox' id='sdLogging' name='sdLogging' " + String(config.sdLogging ? "checked" : "") + ">";
  html += "</div>";
  html += "<div class='form-group'>";
  html += "<label for='logInterval'>Protokollintervall (Sekunden):</label>";
  html += "<input type='number' id='logInterval' name='logInterval' min='10' max='86400' value='" + String(config.logInterval) + "'>";
  html += "</div>";
  html += "</div>";
  
  // Buttons
  html += "<div class='button-group'>";
  html += "<button type='submit' class='button green'>Speichern</button>";
  html += "<a href='/' class='button'>Zurück</a>";
  html += "<a href='/reset' class='button red' onclick='return confirm(\"Wirklich alle Einstellungen zurücksetzen?\");'>Zurücksetzen</a>";
  html += "<a href='/restart' class='button orange' onclick='return confirm(\"Gerät neu starten?\");'>Neustart</a>";
  html += "</div>";
  
  html += "</form>";
  
  // JavaScript für dynamische Formularelemente
  html += "<script>";
  html += "document.getElementById('relayMode').addEventListener('change', function() {";
  html += "  var mode = this.value;";
  html += "  document.getElementById('timeControls').style.display = (mode == 1) ? 'block' : 'none';";
  html += "  document.getElementById('sensorControls').style.display = (mode == 2) ? 'block' : 'none';";
  html += "});";
  html += "</script>";
  
  html += "</div></body></html>";
  
  server.send(200, "text/html", html);
}

// Konfiguration speichern
void handleSave() {
  // Parameter auslesen und Konfiguration aktualisieren
  if (server.hasArg("deviceName")) {
    server.arg("deviceName").toCharArray(config.deviceName, sizeof(config.deviceName));
  }
  
  if (server.hasArg("wifiSSID")) {
    server.arg("wifiSSID").toCharArray(config.wifiSSID, sizeof(config.wifiSSID));
  }
  
  if (server.hasArg("wifiPassword")) {
    server.arg("wifiPassword").toCharArray(config.wifiPassword, sizeof(config.wifiPassword));
  }
  
  config.apMode = server.hasArg("apMode");
  
  if (server.hasArg("mqttServer")) {
    server.arg("mqttServer").toCharArray(config.mqttServer, sizeof(config.mqttServer));
  }
  
  if (server.hasArg("mqttPort")) {
    config.mqttPort = server.arg("mqttPort").toInt();
  }
  
  if (server.hasArg("mqttUser")) {
    server.arg("mqttUser").toCharArray(config.mqttUser, sizeof(config.mqttUser));
  }
  
  if (server.hasArg("mqttPassword")) {
    server.arg("mqttPassword").toCharArray(config.mqttPassword, sizeof(config.mqttPassword));
  }
  
  if (server.hasArg("mqttTopic")) {
    server.arg("mqttTopic").toCharArray(config.mqttTopic, sizeof(config.mqttTopic));
  }
  
  if (server.hasArg("apiServer")) {
    server.arg("apiServer").toCharArray(config.apiServer, sizeof(config.apiServer));
  }
  
  if (server.hasArg("apiKey")) {
    server.arg("apiKey").toCharArray(config.apiKey, sizeof(config.apiKey));
  }
  
  if (server.hasArg("apiUpdateInterval")) {
    config.apiUpdateInterval = server.arg("apiUpdateInterval").toInt();
  }
  
  config.relayEnabled = server.hasArg("relayEnabled");
  
  if (server.hasArg("relayMode")) {
    config.relayMode = server.arg("relayMode").toInt();
  }
  
  if (server.hasArg("relayOnHour")) {
    config.relayOnHour = server.arg("relayOnHour").toInt();
  }
  
  if (server.hasArg("relayOnMinute")) {
    config.relayOnMinute = server.arg("relayOnMinute").toInt();
  }
  
  if (server.hasArg("relayOffHour")) {
    config.relayOffHour = server.arg("relayOffHour").toInt();
  }
  
  if (server.hasArg("relayOffMinute")) {
    config.relayOffMinute = server.arg("relayOffMinute").toInt();
  }
  
  if (server.hasArg("relayThreshold")) {
    config.relayThreshold = server.arg("relayThreshold").toFloat();
  }
  
  config.temperatureSensor = server.hasArg("temperatureSensor");
  config.humiditySensor = server.hasArg("humiditySensor");
  config.energySensor = server.hasArg("energySensor");
  
  if (server.hasArg("sensorReadInterval")) {
    config.sensorReadInterval = server.arg("sensorReadInterval").toInt();
  }
  
  config.sdLogging = server.hasArg("sdLogging");
  
  if (server.hasArg("logInterval")) {
    config.logInterval = server.arg("logInterval").toInt();
  }
  
  // Konfiguration speichern
  saveConfig();
  
  // MQTT-Client neu initialisieren, wenn die Konfiguration geändert wurde
  if (strlen(config.mqttServer) > 0) {
    if (mqttClient) {
      esp_mqtt_client_stop(mqttClient);
      esp_mqtt_client_destroy(mqttClient);
    }
    setupMQTT();
  }
  
  // Bestätigungsseite anzeigen
  String html = "<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1'>";
  html += "<title>SwissAirDry - Konfiguration gespeichert</title>";
  html += "<link rel='stylesheet' href='/style.css'>";
  html += "<meta http-equiv='refresh' content='3; URL=/'>";
  html += "</head><body>";
  html += "<div class='container center'>";
  html += "<h1>Konfiguration gespeichert</h1>";
  html += "<p>Die Einstellungen wurden erfolgreich gespeichert.</p>";
  html += "<p>Sie werden in Kürze zur Startseite weitergeleitet...</p>";
  html += "<a href='/' class='button'>Zurück zur Startseite</a>";
  html += "</div></body></html>";
  
  server.send(200, "text/html", html);
}

// Geräteneustart
void handleRestart() {
  String html = "<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1'>";
  html += "<title>SwissAirDry - Neustart</title>";
  html += "<link rel='stylesheet' href='/style.css'>";
  html += "</head><body>";
  html += "<div class='container center'>";
  html += "<h1>Neustart</h1>";
  html += "<p>Das Gerät wird neu gestartet...</p>";
  html += "</div></body></html>";
  
  server.send(200, "text/html", html);
  delay(1000);
  ESP.restart();
}

// Konfiguration zurücksetzen
void handleReset() {
  // EEPROM-Signatur löschen
  EEPROM.write(0, 0);
  EEPROM.write(1, 0);
  EEPROM.write(2, 0);
  EEPROM.commit();
  
  String html = "<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1'>";
  html += "<title>SwissAirDry - Zurücksetzen</title>";
  html += "<link rel='stylesheet' href='/style.css'>";
  html += "</head><body>";
  html += "<div class='container center'>";
  html += "<h1>Zurücksetzen</h1>";
  html += "<p>Die Konfiguration wurde zurückgesetzt. Das Gerät wird neu gestartet...</p>";
  html += "</div></body></html>";
  
  server.send(200, "text/html", html);
  delay(1000);
  ESP.restart();
}

// Firmware-Update-Formular anzeigen
void handleUpdateForm() {
  String html = "<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1'>";
  html += "<title>SwissAirDry - Firmware Update</title>";
  html += "<link rel='stylesheet' href='/style.css'>";
  html += "</head><body>";
  html += "<div class='container'>";
  html += "<h1>Firmware Update</h1>";
  html += "<form method='POST' action='/update' enctype='multipart/form-data'>";
  html += "<div class='form-group'>";
  html += "<label for='update'>Firmware-Datei (.bin):</label>";
  html += "<input type='file' name='update' id='update'>";
  html += "</div>";
  html += "<div class='button-group'>";
  html += "<button type='submit' class='button orange'>Update starten</button>";
  html += "<a href='/' class='button'>Zurück</a>";
  html += "</div>";
  html += "</form>";
  html += "<div class='note'>";
  html += "<p><strong>Hinweis:</strong> Nach dem Update wird das Gerät automatisch neu gestartet.</p>";
  html += "</div>";
  html += "</div></body></html>";
  
  server.send(200, "text/html", html);
}

// Firmware-Update-Ergebnis anzeigen
void handleUpdateResult() {
  String html = "<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1'>";
  html += "<title>SwissAirDry - Update Ergebnis</title>";
  html += "<link rel='stylesheet' href='/style.css'>";
  
  if (Update.hasError()) {
    html += "</head><body>";
    html += "<div class='container center'>";
    html += "<h1>Update fehlgeschlagen!</h1>";
    html += "<p>Das Firmware-Update konnte nicht durchgeführt werden.</p>";
    html += "<a href='/update' class='button'>Erneut versuchen</a>";
    html += "<a href='/' class='button'>Zurück zur Startseite</a>";
  } else {
    html += "<meta http-equiv='refresh' content='10; URL=/'>";
    html += "</head><body>";
    html += "<div class='container center'>";
    html += "<h1>Update erfolgreich!</h1>";
    html += "<p>Die Firmware wurde erfolgreich aktualisiert.</p>";
    html += "<p>Das Gerät startet automatisch neu...</p>";
  }
  
  html += "</div></body></html>";
  server.send(200, "text/html", html);
  
  if (!Update.hasError()) {
    delay(1000);
    ESP.restart();
  }
}

// Firmware-Update-Upload verarbeiten
void handleUpdateUpload() {
  HTTPUpload& upload = server.upload();
  
  if (upload.status == UPLOAD_FILE_START) {
    Serial.printf("Update: %s\n", upload.filename.c_str());
    
    // Bereite das Display vor
    tft.fillScreen(COLOR_BACKGROUND);
    tft.setTextColor(COLOR_WARNING, COLOR_BACKGROUND);
    tft.setTextSize(1);
    tft.setCursor(10, 10);
    tft.println("Firmware-Update");
    tft.setCursor(10, 30);
    tft.println("Übertragung...");
    
    if (!Update.begin(UPDATE_SIZE_UNKNOWN)) {
      Update.printError(Serial);
    }
  } else if (upload.status == UPLOAD_FILE_WRITE) {
    // Fortschritt anzeigen
    int progress = (upload.currentSize * 100) / upload.totalSize;
    
    tft.fillRect(10, 60, progress * 1.5, 10, COLOR_INFO);
    tft.fillRect(10 + progress * 1.5, 60, 150 - progress * 1.5, 10, COLOR_BACKGROUND);
    
    tft.fillRect(70, 80, 50, 20, COLOR_BACKGROUND);
    tft.setCursor(70, 80);
    tft.setTextColor(COLOR_TEXT, COLOR_BACKGROUND);
    tft.print(progress);
    tft.print("%");
    
    // Daten schreiben
    if (Update.write(upload.buf, upload.currentSize) != upload.currentSize) {
      Update.printError(Serial);
    }
  } else if (upload.status == UPLOAD_FILE_END) {
    if (Update.end(true)) {
      Serial.printf("Update erfolgreich: %u Bytes\n", upload.totalSize);
      
      tft.fillScreen(COLOR_BACKGROUND);
      tft.setTextColor(COLOR_SUCCESS, COLOR_BACKGROUND);
      tft.setTextSize(1);
      tft.setCursor(10, 10);
      tft.println("Firmware-Update");
      tft.setCursor(10, 30);
      tft.println("Update erfolgreich!");
      tft.setCursor(10, 50);
      tft.println("Neustart...");
    } else {
      Update.printError(Serial);
    }
  }
}

// Relais umschalten
void handleToggle() {
  setRelayState(!relayState);
  
  // Antwort senden
  server.sendHeader("Location", "/", true);
  server.send(302, "text/plain", "");
}

// JSON-Daten für AJAX-Anfragen liefern
void handleData() {
  JsonDocument doc;
  
  doc["device_name"] = config.deviceName;
  doc["wifi_connected"] = wifiConnected;
  doc["mqtt_connected"] = mqttConnected;
  doc["relay_state"] = relayState;
  
  JsonObject sensor = doc.createNestedObject("sensor");
  sensor["temperature"] = sensorData.temperature;
  sensor["humidity"] = sensorData.humidity;
  sensor["power"] = sensorData.power;
  sensor["energy"] = sensorData.energy;
  sensor["current_runtime"] = sensorData.currentRuntime;
  sensor["total_runtime"] = sensorData.totalRuntime;
  sensor["valid"] = sensorData.dataValid;
  
  String response;
  serializeJson(doc, response);
  
  server.send(200, "application/json", response);
}

// Protokolle anzeigen
void handleLogs() {
  String html = "<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1'>";
  html += "<title>SwissAirDry - Protokolle</title>";
  html += "<link rel='stylesheet' href='/style.css'>";
  html += "</head><body>";
  html += "<div class='container'>";
  html += "<h1>Protokolle</h1>";
  
  if (!sdCardAvailable) {
    html += "<div class='error-message'>";
    html += "<p>Keine SD-Karte gefunden. Protokolle sind nicht verfügbar.</p>";
    html += "</div>";
  } else {
    // Protokolldateien auflisten
    html += "<div class='logs-list'>";
    html += "<h2>Verfügbare Protokolle</h2>";
    
    if (SD.exists("/logs")) {
      File root = SD.open("/logs");
      if (root) {
        File file = root.openNextFile();
        bool hasFiles = false;
        
        while (file) {
          if (!file.isDirectory() && String(file.name()).endsWith(".csv")) {
            hasFiles = true;
            String fileName = String(file.name());
            html += "<div class='log-entry'>";
            html += "<span class='log-name'>" + fileName + "</span>";
            html += "<span class='log-size'>" + String(file.size() / 1024) + " KB</span>";
            html += "</div>";
          }
          file = root.openNextFile();
        }
        
        if (!hasFiles) {
          html += "<p>Keine Protokolldateien gefunden.</p>";
        }
      }
    } else {
      html += "<p>Protokollverzeichnis nicht gefunden.</p>";
    }
    
    html += "</div>";
  }
  
  html += "<div class='button-group'>";
  html += "<a href='/' class='button'>Zurück</a>";
  html += "</div>";
  html += "</div></body></html>";
  
  server.send(200, "text/html", html);
}

// CSS-Stil liefern
void handleCSS() {
  String css = "* { box-sizing: border-box; margin: 0; padding: 0; }\n";
  css += "body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f4f4f4; }\n";
  css += ".container { max-width: 800px; margin: 0 auto; padding: 20px; }\n";
  css += ".center { text-align: center; }\n";
  css += "h1, h2, h3 { margin-bottom: 10px; color: #0066cc; }\n";
  css += "p { margin-bottom: 10px; }\n";
  css += ".status-card, .data-card, .control-card, .config-section { background: white; border-radius: 5px; padding: 15px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }\n";
  css += ".form-group { margin-bottom: 15px; }\n";
  css += "label { display: block; margin-bottom: 5px; font-weight: bold; }\n";
  css += "input[type='text'], input[type='password'], input[type='number'], select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }\n";
  css += "input[type='checkbox'] { margin-right: 10px; }\n";
  css += ".button { display: inline-block; padding: 8px 16px; background: #0066cc; color: white; text-decoration: none; border-radius: 4px; border: none; cursor: pointer; font-size: 14px; margin-right: 10px; margin-bottom: 10px; }\n";
  css += ".button:hover { background: #0055aa; }\n";
  css += ".button.green { background: #00cc66; }\n";
  css += ".button.green:hover { background: #00aa55; }\n";
  css += ".button.red { background: #cc0000; }\n";
  css += ".button.red:hover { background: #aa0000; }\n";
  css += ".button.orange { background: #ff8800; }\n";
  css += ".button.orange:hover { background: #dd7700; }\n";
  css += ".nav-buttons, .button-group { margin-top: 20px; }\n";
  css += ".error-message { background: #ffeeee; border-left: 4px solid #cc0000; padding: 10px; margin-bottom: 20px; }\n";
  css += ".note { background: #ffffee; border-left: 4px solid #ffcc00; padding: 10px; margin-top: 20px; }\n";
  css += ".logs-list { background: white; border-radius: 5px; padding: 15px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }\n";
  css += ".log-entry { padding: 8px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; }\n";
  css += "@media (max-width: 600px) { .container { padding: 10px; } }\n";
  
  server.send(200, "text/css", css);
}

// JavaScript für AJAX-Aktualisierung liefern
void handleJS() {
  String js = "document.addEventListener('DOMContentLoaded', function() {\n";
  js += "  // Daten alle 5 Sekunden aktualisieren\n";
  js += "  setInterval(updateData, 5000);\n";
  js += "  \n";
  js += "  // Toggle-Button-Event\n";
  js += "  var toggleButton = document.getElementById('toggleButton');\n";
  js += "  if (toggleButton) {\n";
  js += "    toggleButton.addEventListener('click', function(e) {\n";
  js += "      e.preventDefault();\n";
  js += "      fetch('/toggle')\n";
  js += "        .then(response => updateData())\n";
  js += "        .catch(error => console.error('Fehler:', error));\n";
  js += "    });\n";
  js += "  }\n";
  js += "});\n";
  js += "\n";
  js += "function updateData() {\n";
  js += "  fetch('/data')\n";
  js += "    .then(response => response.json())\n";
  js += "    .then(data => {\n";
  js += "      updateSensorData(data);\n";
  js += "      updateRelayState(data.relay_state);\n";
  js += "    })\n";
  js += "    .catch(error => console.error('Fehler:', error));\n";
  js += "}\n";
  js += "\n";
  js += "function updateSensorData(data) {\n";
  js += "  if (!data.sensor || !data.sensor.valid) return;\n";
  js += "  \n";
  js += "  var elements = document.querySelectorAll('.data-card p');\n";
  js += "  if (elements.length >= 2) {\n";
  js += "    elements[0].textContent = 'Temperatur: ' + data.sensor.temperature.toFixed(1) + ' °C';\n";
  js += "    elements[1].textContent = 'Luftfeuchtigkeit: ' + data.sensor.humidity.toFixed(1) + ' %';\n";
  js += "  }\n";
  js += "  \n";
  js += "  if (elements.length >= 4) {\n";
  js += "    elements[2].textContent = 'Leistung: ' + data.sensor.power.toFixed(0) + ' W';\n";
  js += "    elements[3].textContent = 'Energieverbrauch: ' + data.sensor.energy.toFixed(3) + ' kWh';\n";
  js += "  }\n";
  js += "}\n";
  js += "\n";
  js += "function updateRelayState(state) {\n";
  js += "  var relayStatus = document.getElementById('relayStatus');\n";
  js += "  var toggleButton = document.getElementById('toggleButton');\n";
  js += "  \n";
  js += "  if (relayStatus) {\n";
  js += "    relayStatus.textContent = state ? 'AN' : 'AUS';\n";
  js += "  }\n";
  js += "  \n";
  js += "  if (toggleButton) {\n";
  js += "    toggleButton.textContent = state ? 'Ausschalten' : 'Einschalten';\n";
  js += "    toggleButton.className = 'button ' + (state ? 'red' : 'green');\n";
  js += "  }\n";
  js += "}\n";
  
  server.send(200, "application/javascript", js);
}

// 404-Seite anzeigen
void handleNotFound() {
  String html = "<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1'>";
  html += "<title>SwissAirDry - 404 Nicht gefunden</title>";
  html += "<link rel='stylesheet' href='/style.css'>";
  html += "</head><body>";
  html += "<div class='container center'>";
  html += "<h1>404</h1>";
  html += "<h2>Seite nicht gefunden</h2>";
  html += "<p>Die angeforderte Seite konnte nicht gefunden werden.</p>";
  html += "<a href='/' class='button'>Zurück zur Startseite</a>";
  html += "</div></body></html>";
  
  server.send(404, "text/html", html);
}

// ----- DATEN-LOGGING -----
// Task-Funktion für Datenprotokollierung
void dataLoggingTaskFunction(void * parameter) {
  for (;;) {
    // Prüfen, ob es Zeit für das Logging ist
    if (millis() - lastLog >= LOG_INTERVAL && sensorData.dataValid && sdCardAvailable && config.sdLogging) {
      logData();
      lastLog = millis();
    }
    
    // Kurze Pause
    delay(1000);
  }
}

// Daten protokollieren
void logData() {
  if (!sdCardAvailable) return;
  
  // Aktuelles Datum und Uhrzeit
  struct tm timeinfo;
  char timestamp[20];
  
  if (getLocalTime(&timeinfo)) {
    sprintf(timestamp, "%04d-%02d-%02d %02d:%02d:%02d", 
        timeinfo.tm_year + 1900, timeinfo.tm_mon + 1, timeinfo.tm_mday,
        timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec);
  } else {
    // Fallback, wenn keine Zeit verfügbar ist
    unsigned long uptime = millis() / 1000;
    sprintf(timestamp, "Uptime: %lu s", uptime);
  }
  
  // Dateiname im Format YYYY-MM-DD.csv
  char filename[20];
  sprintf(filename, "/logs/%04d-%02d-%02d.csv", 
      timeinfo.tm_year + 1900, timeinfo.tm_mon + 1, timeinfo.tm_mday);
  
  // Prüfen, ob Datei existiert und ggf. Header schreiben
  bool fileExists = SD.exists(filename);
  
  File dataFile = SD.open(filename, FILE_APPEND);
  if (dataFile) {
    // CSV-Header, falls Datei neu ist
    if (!fileExists) {
      dataFile.println("Zeitstempel,Temperatur,Luftfeuchtigkeit,Leistung,Energie,Relais");
    }
    
    // Daten ins CSV-Format schreiben
    String dataString = String(timestamp) + "," +
                        String(sensorData.temperature, 1) + "," +
                        String(sensorData.humidity, 1) + "," +
                        String(sensorData.power, 0) + "," +
                        String(sensorData.energy, 6) + "," +
                        String(relayState ? "AN" : "AUS");
    
    dataFile.println(dataString);
    dataFile.close();
    
    Serial.println("Daten protokolliert: " + dataString);
  } else {
    Serial.println("Fehler beim Öffnen der Protokolldatei!");
  }
}