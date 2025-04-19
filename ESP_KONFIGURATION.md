# ESP32/ESP8266 Konfigurationsanleitung für SwissAirDry

Diese Anleitung beschreibt die Konfiguration und Verwendung von ESP-Geräten mit dem SwissAirDry-System.

## Unterstützte Hardware

SwissAirDry unterstützt folgende ESP-Plattformen:

### ESP32-Familie
- ESP32-WROOM
- ESP32-S3
- **ESP32-C6** (empfohlen für neue Installationen)
- ESP32-XIAO-C6

### ESP8266-Familie
- Wemos D1 Mini
- NodeMCU
- ESP-01

## Empfohlene Hardware

Für Neuinstallationen empfehlen wir die **ESP32-C6** Plattform aufgrund:
- Verbesserter Energieeffizienz
- Besserer WLAN-Stabilität
- Einfacheres OTA-Update-System
- Unterstützung für mehr Sensoren und Displays
- Nativer MQTT-Bibliothek (ohne PubSubClient)

## Erste Schritte

### Schritt 1: Arduino IDE vorbereiten

1. Installieren Sie die [Arduino IDE](https://www.arduino.cc/en/software)
2. Fügen Sie ESP-Boardunterstützung hinzu:
   - Gehen Sie zu "Datei" > "Voreinstellungen"
   - Fügen Sie folgende URLs zum "Zusätzliche Boardverwalter-URLs" Feld hinzu:
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json,http://arduino.esp8266.com/stable/package_esp8266com_index.json
     ```
   - Klicken Sie OK
   - Gehen Sie zu "Werkzeuge" > "Board" > "Boardverwalter"
   - Installieren Sie "esp32" von Espressif Systems
   - Installieren Sie "esp8266" von ESP8266 Community

### Schritt 2: Bibliotheken installieren

Installieren Sie folgende Bibliotheken über den Arduino Bibliotheksverwalter:

#### ESP32/ESP32-C6:
- ArduinoJson (Version 6.x)
- AsyncTCP
- ESPAsyncWebServer
- Adafruit_GFX
- Adafruit_SSD1306 (für OLED-Displays)
- GFX Library for Arduino (für Farb-Displays)
- TFT_eSPI (für Farb-Displays)
- DHT sensor library (für DHT11/DHT22 Sensoren)
- QRCode (für QR-Code-Generation)

#### ESP8266:
- ArduinoJson (Version 6.x)
- ESP8266WiFi (in der ESP8266 Boardunterstützung enthalten)
- PubSubClient (für MQTT auf ESP8266)
- ESPAsyncTCP
- ESPAsyncWebServer
- Adafruit_GFX
- Adafruit_SSD1306 (für OLED-Displays)
- DHT sensor library (für DHT11/DHT22 Sensoren)
- QRCode (für QR-Code-Generation)

### Schritt 3: Firmware auswählen

Wählen Sie die passende Firmware für Ihr Gerät:

| Firmware-Datei | Board | Features |
|----------------|-------|----------|
| SwissAirDry_ESP32C6_MQTT.ino | ESP32-C6 | Native MQTT-Bibliothek, OTA-Updates, Webkonfiguration |
| SwissAirDry_ESP32C6_ColorDisplay.ino | ESP32-C6 mit Farbdisplay | Alle Features plus farbiges UI auf 1.47" LCD-Display |
| SwissAirDry_ESP32C6_XIAO_ColorDisplay.ino | XIAO ESP32-C6 mit Farbdisplay | Angepasst für den kompakten XIAO-Formfaktor |
| SwissAirDry_ESP32_Simple_OTA.ino | ESP32 (Standard) | OTA-Updates, Web-Konfiguration, keine Displays |
| SwissAirDry_ESP8266_OTA.ino | ESP8266/Wemos D1 Mini | OTA-Updates, Grundlegende Web-Konfiguration |
| SwissAirDry_Wemos_D1_Mini_QR.ino | Wemos D1 Mini mit OLED | QR-Code für einfache Konfiguration |
| SwissAirDry_Minimal_Config.ino | Alle Plattformen | Minimale Version ohne Displays, ohne OTA-Updates |

### Schritt 4: Firmware hochladen

1. Verbinden Sie Ihr ESP-Gerät über USB mit dem Computer
2. Öffnen Sie die gewünschte .ino-Datei in der Arduino IDE
3. Wählen Sie den korrekten Board-Typ unter "Werkzeuge" > "Board"
4. Wählen Sie den richtigen COM-Port
5. Klicken Sie auf "Hochladen"

## MQTT-Konfiguration

SwissAirDry-Geräte kommunizieren über das MQTT-Protokoll. Die Standardeinstellungen sind:

- **MQTT-Topic-Präfix**: `swissairdry/`
- **Gerät-ID-Format**: `esp-[MAC-Adressrest]` (z.B. `esp-b4c21f`)
- **Status-Topic**: `swissairdry/[Gerät-ID]/status`
- **Sensor-Topic**: `swissairdry/[Gerät-ID]/sensor/[Sensor-Name]`
- **Steuerungs-Topic**: `swissairdry/[Gerät-ID]/control`
- **Konfigurations-Topic**: `swissairdry/[Gerät-ID]/config`

## Web-Konfiguration

Alle ESP-Geräte starten im AP-Modus, wenn sie keine WLAN-Konfiguration haben:

1. Verbinden Sie sich mit dem WLAN "SwissAirDry-XXXXX" (XXXXX = letzten 5 Zeichen der MAC-Adresse)
2. Das Passwort lautet standardmäßig "swissairdry"
3. Öffnen Sie die Adresse `192.168.4.1` in Ihrem Browser
4. Konfigurieren Sie das WLAN und den MQTT-Server
5. Nach dem Speichern verbindet sich das Gerät mit dem konfigurierten WLAN und MQTT-Server

## QR-Code-Konfiguration

Bei Geräten mit QR-Code-Unterstützung:

1. Verbinden Sie sich mit dem WLAN "SwissAirDry-XXXXX"
2. Das Display zeigt einen QR-Code
3. Scannen Sie den QR-Code mit der SwissAirDry-App oder einer QR-Code-Scanner-App
4. Folgen Sie den Anweisungen zur Konfiguration
5. Die Konfiguration wird drahtlos zum ESP-Gerät übertragen

## Pin-Belegung

### ESP32-C6 (Standard-Konfiguration)

| Pin | Funktion | Beschreibung |
|-----|----------|-------------|
| 8   | DHT Data | Daten-Pin für DHT11/DHT22 Sensor |
| 9   | Relais 1 | Steuerung für Relais 1 |
| 10  | Relais 2 | Steuerung für Relais 2 |
| 11  | Relais 3 | Steuerung für Relais 3 |
| 12  | Relais 4 | Steuerung für Relais 4 |
| 4   | SDA      | I2C-Datenleitung für Displays/Sensoren |
| 5   | SCL      | I2C-Taktleitung für Displays/Sensoren |
| 18  | TFT_DC   | TFT-Display Datenkontroll-Pin (bei Farbdisplays) |
| 7   | TFT_CS   | TFT-Display Chip-Select (bei Farbdisplays) |
| 6   | TFT_RST  | TFT-Display Reset (bei Farbdisplays) |

### Wemos D1 Mini (ESP8266)

| Pin | Funktion | Beschreibung |
|-----|----------|-------------|
| D4  | DHT Data | Daten-Pin für DHT11/DHT22 Sensor |
| D1  | SDA      | I2C-Datenleitung für OLED-Display |
| D2  | SCL      | I2C-Taktleitung für OLED-Display |
| D5  | Relais 1 | Steuerung für Relais 1 |
| D6  | Relais 2 | Steuerung für Relais 2 |
| D7  | Relais 3 | Steuerung für Relais 3 |
| D8  | Relais 4 | Steuerung für Relais 4 |

## OTA-Updates

### Manuelle Updates

1. Öffnen Sie die Web-Oberfläche des Geräts (IP-Adresse im lokalen Netzwerk)
2. Navigieren Sie zur "Update"-Seite
3. Wählen Sie die neue .bin-Datei aus
4. Klicken Sie auf "Update"

### Automatische Updates

1. Stellen Sie sicher, dass das Gerät mit dem MQTT-Broker verbunden ist
2. Senden Sie ein Update-Kommando an das Kontroll-Topic:
   ```json
   {
     "command": "update",
     "url": "http://api.vgnc.org/esp/firmware/SwissAirDry_ESP32C6_latest.bin"
   }
   ```
3. Das Gerät lädt die Firmware herunter und installiert sie automatisch

## Troubleshooting

### Gerät verbindet sich nicht mit WLAN

1. Überprüfen Sie, ob die SSID und das Passwort korrekt sind
2. Stellen Sie sicher, dass das WLAN-Netzwerk 2.4 GHz unterstützt (5 GHz wird nicht unterstützt)
3. Versuchen Sie, die Konfiguration im AP-Modus zurückzusetzen:
   - Drücken Sie die Reset-Taste zweimal schnell hintereinander
   - Oder trennen Sie die Stromversorgung für 10 Sekunden und schließen Sie sie wieder an

### Gerät verbindet sich nicht mit MQTT

1. Überprüfen Sie, ob die MQTT-Server-Adresse korrekt ist
2. Stellen Sie sicher, dass die erforderlichen Ports freigegeben sind (1883 für MQTT, 9001 für WebSockets)
3. Prüfen Sie, ob Authentifizierung erforderlich ist, und geben Sie Benutzername und Passwort an
4. Überprüfen Sie die Firewall-Einstellungen auf dem Server

### Sensoren werden nicht erkannt

1. Überprüfen Sie die Verkabelung
2. Stellen Sie sicher, dass die richtige Bibliothek installiert ist
3. Prüfen Sie, ob der richtige Pin konfiguriert ist
4. Testen Sie den Sensor mit einem einfachen Beispielsketch aus der Bibliothek

## Weitere Ressourcen

- [Espressif ESP32-C6 Dokumentation](https://docs.espressif.com/projects/esp-idf/en/latest/esp32c6/index.html)
- [ESP8266 Dokumentation](https://arduino-esp8266.readthedocs.io/en/latest/)
- [MQTT-Protokoll Dokumentation](https://mqtt.org/)