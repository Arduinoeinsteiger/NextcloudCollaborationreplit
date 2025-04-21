/**
 * SwissAirDry ESP32-C6 mit TFT-Display und SD-Karten-Unterstützung
 * 
 * PlatformIO-Version
 * 
 * @version 1.0.0
 * @author Swiss Air Dry Team <info@swissairdry.com>
 * @copyright 2023-2025 Swiss Air Dry Team
 */

// Diese Datei VOR allen anderen Includes einfügen, um SPI-Kompatibilitätsprobleme zu beheben
#include "spi_fix.h"

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <ArduinoOTA.h>
#include <ArduinoJson.h>
#include <Preferences.h>
#include <DNSServer.h>
#include <WiFiManager.h>
#include <OneButton.h>
#include <SPI.h>
#include <SD.h>
#include <TFT_eSPI.h>
#include <FS.h>
#include <LittleFS.h>

// Konstanten
#define DEVICE_VERSION "1.0.0"
#define SENSOR_READ_INTERVAL 5000    // 5 Sekunden
#define API_SEND_INTERVAL 30000      // 30 Sekunden
#define LED_UPDATE_INTERVAL 1000     // 1 Sekunde
#define WEB_CONFIG_PORT 80           // Webserver-Port
#define MAX_FAILED_API_ATTEMPTS 5    // Max. Anzahl fehlgeschlagener API-Verbindungen

// Pinnummern für ESP32-C6 XIAO Board
#define RELAY1_PIN 7     // GPIO7 für Relais 1
#define RELAY2_PIN 6     // GPIO6 für Relais 2
#define SENSOR_PIN 5     // GPIO5 für DHT Sensor (falls verwendet)
#define LED_PIN 21       // Eingebaute LED
#define SD_CS_PIN 10     // GPIO10 für SD-Karten-CS

// Display-Einstellungen
#define TFT_WIDTH 172
#define TFT_HEIGHT 320

// Physische Tasten
#define BTN_BOOT 9       // BOOT-Taste
#define BTN_RESET 3      // RESET-Taste (Hardware Reset)

// SD-Karten-Verzeichnisstruktur
#define WEB_DIR "/web"           // Webdateien auf der SD-Karte
#define CSS_DIR "/web/css"       // CSS-Dateien
#define JS_DIR "/web/js"         // JavaScript-Dateien
#define IMAGES_DIR "/web/images" // Bilddateien

// OneButton-Objekt für die BOOT-Taste
OneButton btnBoot(BTN_BOOT, true);

// TFT-Display initialisieren
TFT_eSPI tft = TFT_eSPI();

// Webserver initialisieren
WebServer server(WEB_CONFIG_PORT);

// Preferences für die Konfigurationsspeicherung
Preferences preferences;

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
};

Config config;
unsigned long lastSensorRead = 0;
unsigned long lastApiSend = 0;
unsigned long lastLedUpdate = 0;
unsigned long startTime = 0;
unsigned long runTime = 0;
bool wifiConnected = false;
bool apiConnected = false;
bool relay1State = false;
bool relay2State = false;
bool sdCardAvailable = false;
float temperature = 0.0;
float humidity = 0.0;
float power = 0.0;
float energy = 0.0;
int failedApiAttempts = 0;
int currentMenuPage = 0;
int maxMenuPages = 3;

// Funktionsprototypen
void setupWifi();
void setupWebServer();
void setupOTA();
void loadConfig();
void saveConfig();
bool sendDataToApi();
void readSensors();
void updateLedStatus();
bool setupSDCard();
void setupTFTDisplay();
void updateDisplay();
void handleRoot();
void handleConfig();
void handleSave();
void handleReset();
void handleRestart();
void handleStatus();
void handleStaticFiles(String path);
void generateDeviceId();
void setupButtons();
void onBootButtonPressed();
void onBootButtonLongPressed();

// TFT-Display initialisieren
void setupTFTDisplay() {
  Serial.println("TFT-Display wird initialisiert...");
  tft.init();
  tft.setRotation(0); // Portrait-Modus (0 oder 2)
  tft.fillScreen(TFT_BLACK);
  Serial.println("TFT-Display initialisiert");
}

// Aktualisiert Display mit den neuesten Daten
void updateDisplay() {
  // Bildschirmseite basierend auf currentMenuPage anzeigen
  tft.fillScreen(TFT_BLACK);
  
  switch (currentMenuPage) {
    case 0: // Hauptseite - Statusübersicht
      tft.setTextColor(TFT_WHITE, TFT_BLACK);
      tft.setCursor(10, 10);
      tft.setTextSize(2);
      tft.println("SwissAirDry");
      
      tft.setTextSize(1);
      tft.setCursor(10, 40);
      tft.println("Temperatur: " + String(temperature, 1) + " C");
      
      tft.setCursor(10, 60);
      tft.println("Feuchtigkeit: " + String(humidity, 1) + " %");
      
      tft.setCursor(10, 80);
      tft.println("Leistung: " + String(power, 1) + " W");
      
      tft.setCursor(10, 100);
      tft.println("Energie: " + String(energy, 3) + " kWh");
      
      tft.setCursor(10, 120);
      tft.println("Laufzeit: " + String(runTime) + " s");
      
      tft.setCursor(10, 140);
      tft.println("Relais 1: " + String(relay1State ? "EIN" : "AUS"));
      
      tft.setCursor(10, 160);
      tft.println("Relais 2: " + String(relay2State ? "EIN" : "AUS"));
      
      tft.setCursor(10, 180);
      tft.println("WLAN: " + String(wifiConnected ? "Verbunden" : "Getrennt"));
      
      tft.setCursor(10, 200);
      tft.println("API: " + String(apiConnected ? "Verbunden" : "Getrennt"));
      
      tft.setCursor(10, 220);
      tft.println("SD-Karte: " + String(sdCardAvailable ? "OK" : "Fehlt"));
      
      tft.setCursor(10, 240);
      tft.setTextColor(TFT_YELLOW, TFT_BLACK);
      tft.println("< Drucken fur Menu >");
      break;
      
    case 1: // Einstellungsseite
      tft.setTextColor(TFT_WHITE, TFT_BLACK);
      tft.setCursor(10, 10);
      tft.setTextSize(2);
      tft.println("Einstellungen");
      
      tft.setTextSize(1);
      tft.setCursor(10, 40);
      tft.println("Geraete-ID: " + String(config.device_id));
      
      tft.setCursor(10, 60);
      tft.println("API Host: " + String(config.api_host));
      
      tft.setCursor(10, 80);
      tft.println("API Port: " + String(config.api_port));
      
      tft.setCursor(10, 100);
      tft.println("API Pfad: " + String(config.api_path));
      
      tft.setCursor(10, 120);
      tft.println("SSL: " + String(config.use_ssl ? "Ja" : "Nein"));
      
      tft.setCursor(10, 140);
      tft.println("Temp. Schwelle: " + String(config.temp_threshold, 1) + " C");
      
      tft.setCursor(10, 160);
      tft.println("Feuchte Schwelle: " + String(config.humid_threshold, 1) + " %");
      
      tft.setCursor(10, 240);
      tft.setTextColor(TFT_YELLOW, TFT_BLACK);
      tft.println("< Drucken fur Relais >");
      break;
      
    case 2: // Relais-Steuerungsseite
      tft.setTextColor(TFT_WHITE, TFT_BLACK);
      tft.setCursor(10, 10);
      tft.setTextSize(2);
      tft.println("Relais-Steuerung");
      
      tft.setTextSize(1);
      tft.setCursor(10, 40);
      tft.println("Relais 1: " + String(relay1State ? "EIN" : "AUS"));
      
      tft.setCursor(10, 60);
      tft.println("Relais 2: " + String(relay2State ? "EIN" : "AUS"));
      
      tft.setCursor(10, 100);
      tft.println("Kurz Druecken: Relais 1 umschalten");
      
      tft.setCursor(10, 120);
      tft.println("Lang Druecken: Relais 2 umschalten");
      
      tft.setCursor(10, 240);
      tft.setTextColor(TFT_YELLOW, TFT_BLACK);
      tft.println("< Drucken fur Hauptseite >");
      break;
  }
}

bool setupSDCard() {
  Serial.println("SD-Karte wird initialisiert...");
  if (!SD.begin(SD_CS_PIN)) {
    Serial.println("SD-Karteninitialisierung fehlgeschlagen!");
    return false;
  }
  
  uint8_t cardType = SD.cardType();
  if (cardType == CARD_NONE) {
    Serial.println("Keine SD-Karte eingelegt");
    return false;
  }
  
  uint64_t cardSize = SD.cardSize() / (1024 * 1024);
  Serial.printf("SD-Karte gefunden. Typ: ");
  
  switch (cardType) {
    case CARD_MMC:
      Serial.println("MMC");
      break;
    case CARD_SD:
      Serial.println("SDSC");
      break;
    case CARD_SDHC:
      Serial.println("SDHC");
      break;
    default:
      Serial.println("UNBEKANNT");
      break;
  }
  
  Serial.printf("Kapazität: %lluMB\n", cardSize);
  
  // Prüfen, ob die erforderlichen Verzeichnisse existieren, sonst erstellen
  if (!SD.exists(WEB_DIR)) {
    Serial.println("Erstelle Web-Verzeichnis...");
    SD.mkdir(WEB_DIR);
  }
  
  if (!SD.exists(CSS_DIR)) {
    Serial.println("Erstelle CSS-Verzeichnis...");
    SD.mkdir(CSS_DIR);
  }
  
  if (!SD.exists(JS_DIR)) {
    Serial.println("Erstelle JS-Verzeichnis...");
    SD.mkdir(JS_DIR);
  }
  
  if (!SD.exists(IMAGES_DIR)) {
    Serial.println("Erstelle Images-Verzeichnis...");
    SD.mkdir(IMAGES_DIR);
  }
  
  // Prüfen, ob index.html existiert
  if (!SD.exists(WEB_DIR "/index.html")) {
    Serial.println("index.html nicht gefunden, erstelle Standard-Datei...");
    File indexFile = SD.open(WEB_DIR "/index.html", FILE_WRITE);
    if (indexFile) {
      indexFile.println("<!DOCTYPE html>");
      indexFile.println("<html>");
      indexFile.println("<head>");
      indexFile.println("  <meta name='viewport' content='width=device-width, initial-scale=1'>");
      indexFile.println("  <title>SwissAirDry</title>");
      indexFile.println("  <link rel='stylesheet' href='css/style.css'>");
      indexFile.println("</head>");
      indexFile.println("<body>");
      indexFile.println("  <h1>SwissAirDry</h1>");
      indexFile.println("  <div id='status'></div>");
      indexFile.println("  <script src='js/app.js'></script>");
      indexFile.println("</body>");
      indexFile.println("</html>");
      indexFile.close();
      Serial.println("Standard index.html erstellt");
    } else {
      Serial.println("Fehler beim Erstellen von index.html");
    }
  }
  
  // Weitere Standarddateien erstellen (style.css, app.js)...
  
  return true;
}

void setupButtons() {
  Serial.println("BOOT-Taste wird eingerichtet...");
  
  // Konfiguriere die Funktionen für die Taste
  btnBoot.attachClick(onBootButtonPressed);
  btnBoot.attachLongPressStart(onBootButtonLongPressed);
  
  Serial.println("BOOT-Taste eingerichtet");
}

void onBootButtonPressed() {
  Serial.println("BOOT-Taste gedrückt");
  
  // Zwischen den Menüseiten wechseln
  currentMenuPage = (currentMenuPage + 1) % maxMenuPages;
  updateDisplay();
  
  // Relais-Steuerung auf Seite 2
  if (currentMenuPage == 2) {
    relay1State = !relay1State;
    digitalWrite(RELAY1_PIN, relay1State ? HIGH : LOW);
    Serial.print("Relais 1 manuell auf ");
    Serial.println(relay1State ? "EIN" : "AUS");
    updateDisplay();
  }
}

void onBootButtonLongPressed() {
  Serial.println("BOOT-Taste lange gedrückt");
  
  // Relais-Steuerung auf Seite 2
  if (currentMenuPage == 2) {
    relay2State = !relay2State;
    digitalWrite(RELAY2_PIN, relay2State ? HIGH : LOW);
    Serial.print("Relais 2 manuell auf ");
    Serial.println(relay2State ? "EIN" : "AUS");
    updateDisplay();
  }
}

void setupWifi() {
  Serial.println("WLAN-Konfiguration wird gestartet...");
  
  // Statusanzeige auf dem Display
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.setCursor(10, 10);
  tft.setTextSize(2);
  tft.println("WLAN-Setup");
  tft.setTextSize(1);
  tft.setCursor(10, 40);
  tft.println("Verbinde mit WLAN...");
  
  // WiFiManager initialisieren
  WiFiManager wifiManager;
  
  // Timeout nach 3 Minuten im Konfigurationsmodus
  wifiManager.setConfigPortalTimeout(180);
  
  // Im Konfigurationsmodus blaue LED einschalten
  wifiManager.setAPCallback([](WiFiManager* wifiManager) {
    Serial.println("Konfigurationsmodus aktiv");
    digitalWrite(LED_PIN, LOW);
    
    tft.fillScreen(TFT_BLACK);
    tft.setTextColor(TFT_WHITE, TFT_BLACK);
    tft.setCursor(10, 10);
    tft.setTextSize(2);
    tft.println("WLAN-Setup");
    tft.setTextSize(1);
    tft.setCursor(10, 40);
    tft.println("Konfigurationsmodus aktiv");
    tft.setCursor(10, 60);
    tft.println("SSID: SwissAirDry-" + String(config.device_id));
    tft.setCursor(10, 80);
    tft.println("Passwort: swissairdry");
    tft.setCursor(10, 100);
    tft.println("IP: 192.168.4.1");
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

void loadConfig() {
  Serial.println("Lade Konfiguration...");
  
  // Preferences öffnen
  preferences.begin("swissairdry", false);
  
  // Wenn keine Geräte-ID vorhanden ist, generieren wir eine
  if (!preferences.isKey("deviceId")) {
    generateDeviceId();
  } else {
    String deviceId = preferences.getString("deviceId", "");
    deviceId.toCharArray(config.device_id, sizeof(config.device_id));
  }
  
  // API-Host laden (Standard: api.vgnc.org)
  String apiHost = preferences.getString("apiHost", "api.vgnc.org");
  apiHost.toCharArray(config.api_host, sizeof(config.api_host));
  
  // API-Port laden (Standard: 443)
  config.api_port = preferences.getInt("apiPort", 443);
  
  // API-Pfad laden (Standard: /api/device)
  String apiPath = preferences.getString("apiPath", "/api/device");
  apiPath.toCharArray(config.api_path, sizeof(config.api_path));
  
  // SSL verwenden (Standard: true)
  config.use_ssl = preferences.getBool("useSSL", true);
  
  // Auth-Token laden (Standard: leer)
  String authToken = preferences.getString("authToken", "");
  authToken.toCharArray(config.auth_token, sizeof(config.auth_token));
  
  // Relais-Einstellungen laden
  config.relay1_enabled = preferences.getBool("relay1Enabled", true);
  config.relay2_enabled = preferences.getBool("relay2Enabled", false);
  
  // Schwellenwerte laden
  config.temp_threshold = preferences.getFloat("tempThreshold", 20.0);
  config.humid_threshold = preferences.getFloat("humidThreshold", 60.0);
  
  preferences.end();
  
  Serial.println("Konfiguration geladen:");
  Serial.print("Geräte-ID: ");
  Serial.println(config.device_id);
}

void generateDeviceId() {
  // MAC-Adresse als Basis für Geräte-ID verwenden
  uint8_t mac[6];
  WiFi.macAddress(mac);
  
  // Format: esp-XXXX (letzten 4 Bytes der MAC in Hex)
  sprintf(config.device_id, "esp-%02x%02x%02x", mac[3], mac[4], mac[5]);
  
  // In Preferences speichern
  preferences.begin("swissairdry", false);
  preferences.putString("deviceId", config.device_id);
  preferences.end();
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
}

void updateLedStatus() {
  // LED-Status basierend auf dem Systemstatus
  if (!wifiConnected) {
    // Schnelles Blinken: WLAN-Problem
    digitalWrite(LED_PIN, (millis() / 200) % 2 ? HIGH : LOW);
  } else if (!apiConnected) {
    // Langsames Blinken: API-Problem
    digitalWrite(LED_PIN, (millis() / 1000) % 2 ? HIGH : LOW);
  } else if (relay1State || relay2State) {
    // Dauerhaft an: Alles OK und aktiv
    digitalWrite(LED_PIN, LOW);
  } else {
    // Pulsieren: Alles OK, Standby
    int brightness = (millis() % 2000) / 2000.0 * 255;
    if (brightness > 127) brightness = 255 - brightness;
    digitalWrite(LED_PIN, brightness < 64 ? LOW : HIGH);
  }
}

void setup() {
  // Serielle Schnittstelle initialisieren
  Serial.begin(115200);
  delay(500);
  Serial.println("\n\nSwissAirDry ESP32-C6 mit TFT-Display und SD-Karte");
  Serial.print("Version: ");
  Serial.println(DEVICE_VERSION);
  
  // Pins konfigurieren
  pinMode(RELAY1_PIN, OUTPUT);
  pinMode(RELAY2_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  
  // Relais ausschalten
  digitalWrite(RELAY1_PIN, LOW);
  digitalWrite(RELAY2_PIN, LOW);
  digitalWrite(LED_PIN, HIGH); // LED ausschalten
  
  // TFT-Display initialisieren
  setupTFTDisplay();
  
  // SD-Karte initialisieren
  sdCardAvailable = setupSDCard();
  
  // LittleFS initialisieren
  if (!LittleFS.begin(true)) {
    Serial.println("LittleFS konnte nicht initialisiert werden");
  } else {
    Serial.println("LittleFS initialisiert");
  }
  
  // Konfiguration laden
  loadConfig();
  
  // Tasten einrichten
  setupButtons();
  
  // WiFi-Verbindung aufbauen
  setupWifi();
  
  // Startzeit speichern
  startTime = millis();
  
  Serial.println("Setup abgeschlossen");
  Serial.print("Geräte-ID: ");
  Serial.println(config.device_id);
  
  // Willkommensnachricht auf dem Display
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.setCursor(10, 10);
  tft.setTextSize(2);
  tft.println("SwissAirDry");
  tft.setTextSize(1);
  tft.setCursor(10, 40);
  tft.println("Version: " + String(DEVICE_VERSION));
  tft.setCursor(10, 60);
  tft.println("ID: " + String(config.device_id));
  tft.setCursor(10, 80);
  tft.println("IP: " + WiFi.localIP().toString());
  tft.setCursor(10, 100);
  tft.println("SD-Karte: " + String(sdCardAvailable ? "OK" : "Fehlt"));
}

void loop() {
  // Tasten prüfen
  btnBoot.tick();
  
  // Aktuelle Zeit
  unsigned long currentTime = millis();
  
  // Laufzeit aktualisieren
  runTime = (currentTime - startTime) / 1000;
  
  // WLAN-Status prüfen
  wifiConnected = (WiFi.status() == WL_CONNECTED);
  
  // Sensoren auslesen
  if (currentTime - lastSensorRead >= SENSOR_READ_INTERVAL) {
    readSensors();
    updateDisplay(); // Display mit aktuellen Werten aktualisieren
    lastSensorRead = currentTime;
  }
  
  // LED-Status aktualisieren
  if (currentTime - lastLedUpdate >= LED_UPDATE_INTERVAL) {
    updateLedStatus();
    lastLedUpdate = currentTime;
  }
  
  // Kurze Pause
  delay(10);
}