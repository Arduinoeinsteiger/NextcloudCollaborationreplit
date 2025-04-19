# ESP32-Konfiguration für SwissAirDry

Diese Anleitung erklärt, wie Sie ESP32-Geräte für die Verwendung mit dem SwissAirDry-System konfigurieren.

## Unterstützte Hardware

- **Empfohlen**: Seeed Studio XIAO ESP32C6 mit 1.47" Display
- **Standard**: Wemos D1 Mini (ESP8266)
- **Alternativ**: ESP32 (alle Varianten)

## Firmware-Varianten

Es stehen zwei Hauptvarianten der Firmware zur Verfügung:

### 1. REST API-Version

Die REST API-Version verwendet HTTP-Anfragen, um mit dem SwissAirDry-API-Server zu kommunizieren.

**Vorteile:**
- Einfache Implementierung ohne zusätzliche Server-Komponenten
- Direkter Zugriff auf API-Endpunkte
- Keine dauerhafte Verbindung nötig

**Nachteile:**
- Höherer Overhead bei der Datenübertragung
- Weniger effizient bei häufigen Updates

### 2. MQTT-Version (empfohlen)

Die MQTT-Version verwendet das MQTT-Protokoll für die Kommunikation.

**Vorteile:**
- Effizienteres Protokoll für IoT-Anwendungen
- Echtzeit-Kommunikation in beide Richtungen
- Geringerer Overhead bei Datenübertragung
- Bessere Unterstützung für Netzwerke mit instabiler Verbindung
- Ermöglicht Gruppierung von Geräten über Topics

**Nachteile:**
- Benötigt einen MQTT-Broker

## Installation der Firmware

### Vorbereitung

1. Installieren Sie die Arduino IDE (Version 2.x empfohlen)
2. Fügen Sie die ESP32-Boardunterstützung hinzu:
   - Gehen Sie zu **Datei** → **Voreinstellungen**
   - Fügen Sie folgende URL zu den zusätzlichen Boardverwalter-URLs hinzu:
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json,http://arduino.esp8266.com/stable/package_esp8266_com_index.json
     ```
   - Gehen Sie zu **Werkzeuge** → **Board** → **Boardverwalter**
   - Suchen und installieren Sie "esp32" und "esp8266"

3. Installieren Sie die benötigten Bibliotheken:
   - **Für alle Geräte**: ArduinoJson, PubSubClient (für MQTT)
   - **Für XIAO ESP32C6 mit Display**: TFT_eSPI
   - **Für Wemos D1 Mini mit OLED**: Adafruit GFX, Adafruit SSD1306

### Konfiguration des TFT_eSPI für XIAO ESP32C6

Wenn Sie den XIAO ESP32C6 mit dem 1.47" Display verwenden:

1. Navigieren Sie zum Installationsverzeichnis der TFT_eSPI-Bibliothek
2. Öffnen Sie die Datei `User_Setup_Select.h` und kommentieren Sie alle `#include`-Zeilen aus
3. Fügen Sie folgende Zeile hinzu: `#include <User_Setups/Setup_XIAO_ESP32C6.h>`
4. Erstellen Sie eine neue Datei `Setup_XIAO_ESP32C6.h` im Verzeichnis `User_Setups` mit folgendem Inhalt:

```c
// Konfiguration für XIAO ESP32C6 mit 1.47" Display

#define ST7789_DRIVER
#define TFT_WIDTH 172
#define TFT_HEIGHT 320
#define TFT_MOSI 10  // SDA
#define TFT_SCLK 8   // SCL
#define TFT_CS 9     // CS
#define TFT_DC 7     // DC
#define TFT_RST 6    // RESET
#define TFT_BL 5     // Hintergrundbeleuchtung
#define TFT_BACKLIGHT_ON HIGH

#define LOAD_GLCD
#define LOAD_FONT2
#define LOAD_FONT4
#define LOAD_FONT6
#define LOAD_FONT7
#define LOAD_FONT8
#define LOAD_GFXFF

#define SMOOTH_FONT

#define SPI_FREQUENCY 40000000
```

### Firmware konfigurieren und hochladen

1. Öffnen Sie die gewünschte Firmware-Datei in der Arduino IDE:
   - `SwissAirDry_ESP32C6_RestAPI.ino` für die REST API-Version
   - `SwissAirDry_ESP32C6_MQTT.ino` für die MQTT-Version

2. Konfigurieren Sie die Verbindungseinstellungen:

   **Für REST API-Version:**
   ```c
   const char* ssid = "WLAN-SSID";           // WLAN-SSID
   const char* password = "WLAN-PASSWORD";   // WLAN-Passwort
   const char* api_host = "192.168.1.100";   // API-Server-IP oder Hostname
   const int api_port = 5000;                // API-Server-Port
   const char* device_id = "esp32c6_rest";   // Eindeutige Geräte-ID
   ```

   **Für MQTT-Version:**
   ```c
   const char* ssid = "WLAN-SSID";             // WLAN-SSID
   const char* password = "WLAN-PASSWORD";     // WLAN-Passwort
   const char* mqtt_server = "192.168.1.100";  // MQTT-Broker-IP oder Hostname
   const int mqtt_port = 1883;                 // MQTT-Broker-Port
   const char* mqtt_user = "";                 // MQTT-Benutzername (leer = kein Auth)
   const char* mqtt_password = "";             // MQTT-Passwort (leer = kein Auth)
   const char* device_id = "esp32c6_mqtt";     // Eindeutige Geräte-ID
   const char* mqtt_topic_prefix = "swissairdry"; // MQTT-Topic-Präfix
   ```

3. Wählen Sie das richtige Board und den richtigen Port:
   - **Board**: "XIAO_ESP32C6" für ESP32C6 oder "ESP8266" für Wemos D1 Mini
   - **Port**: COM-Port, an dem das Gerät angeschlossen ist

4. Klicken Sie auf "Hochladen", um die Firmware auf das Gerät zu flashen

## LED-Statusanzeigen

Die Firmware verwendet die eingebaute RGB-LED, um den Status des Geräts anzuzeigen:

- **Blinkendes Orange**: WLAN-Verbindungsprobleme
- **Blinkendes Rot**: API/MQTT-Verbindungsprobleme
- **Grün**: Verbunden und aktiv (Relais eingeschaltet)
- **Cyan**: Verbunden und im Standby (Relais ausgeschaltet)

## Display-Anzeige

Das Display zeigt folgende Informationen an:

1. Verbindungsstatus (WLAN, API/MQTT)
2. Sensordaten (Temperatur, Luftfeuchtigkeit)
3. Leistungsdaten (Leistung, Energie)
4. Relais-Status
5. Laufzeit des Geräts

## Fehlerbehebung

### Keine WLAN-Verbindung
- Überprüfen Sie SSID und Passwort
- Stellen Sie sicher, dass das WLAN-Signal stark genug ist
- Prüfen Sie, ob Ihr WLAN-Router 2,4 GHz unterstützt (ESP8266/ESP32 unterstützen kein 5 GHz)

### Keine API-Verbindung
- Überprüfen Sie die IP-Adresse oder den Hostnamen des API-Servers
- Stellen Sie sicher, dass der API-Port (standardmäßig 5000) erreichbar ist
- Prüfen Sie, ob der API-Server läuft

### Keine MQTT-Verbindung
- Überprüfen Sie die IP-Adresse oder den Hostnamen des MQTT-Brokers
- Stellen Sie sicher, dass der MQTT-Port (standardmäßig 1883) erreichbar ist
- Prüfen Sie, ob Authentifizierungsdaten korrekt sind (falls verwendet)

### Display zeigt nichts an
- Überprüfen Sie die TFT_eSPI-Konfiguration
- Prüfen Sie die Verbindungen zum Display
- Stellen Sie sicher, dass die richtigen Pins verwendet werden

## OTA-Updates (Over-the-Air)

Die Firmware unterstützt OTA-Updates, sodass Sie Aktualisierungen ohne physischen Zugriff auf das Gerät durchführen können:

1. Stellen Sie sicher, dass Ihr ESP und Ihr Computer im selben Netzwerk sind
2. Öffnen Sie die Arduino IDE und laden Sie die neue Firmware
3. Wählen Sie unter **Werkzeuge** → **Port** den Netzwerk-Port des ESP-Geräts
4. Klicken Sie auf "Hochladen"

**Hinweis**: OTA-Updates funktionieren nur, wenn das Gerät bereits eine funktionsfähige Firmware mit OTA-Unterstützung hat und mit dem WLAN verbunden ist.