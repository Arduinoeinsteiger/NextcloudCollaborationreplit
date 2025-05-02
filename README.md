# SwissAirDry

Ein umfassendes System zur Verwaltung von Trocknungsgeräten für Bausanierungsunternehmen. Das System bietet Echtzeit-Überwachung von Trocknungsgeräten, Auftragsmanagement, Energiekosten-Berechnung und IoT-Integration mit ESP32C6/ESP8266-Geräten.

## Funktionen

- Echtzeit-Überwachung von Trocknungsgeräten
- Verwaltung von Aufträgen und Kunden
- Visualisierung von Energie- und Feuchtigkeitsdaten
- Integration mit Bexio für Rechnungen
- QR-Code-basierte Gerätekonfiguration
- OTA-Updates für ESP32C6 und ESP8266 Geräte
- IoT-Kommunikation über MQTT
- Nextcloud-Integration als ExApp (Externe Anwendung)
- Responsive Web- und Mobile-Oberfläche

## Projektstruktur

Das SwissAirDry-Repository ist wie folgt organisiert:

```
swissairdry/
├── api/                 # API-Server und Endpunkte
│   ├── app/             # Hauptanwendung
│   ├── minimal_http_server.py  # Minimal-Server ohne externe Abhängigkeiten
├── arduino/             # Arduino-Sketches für Wemos D1 Mini
├── ci_tools/            # Tools für CI/CD und Build-Fixes
├── config/              # Konfigurationsdateien
├── docker/              # Docker-Konfiguration und Setup-Skripte
├── docs/                # Projektdokumentation
├── esp/                 # ESP32C6/ESP8266-Firmware
├── ExApp/               # Nextcloud ExApp-Integration
├── mobile/              # Mobile App (Android)
├── mqtt/                # MQTT-Broker-Konfiguration
├── nextcloud/           # Nextcloud-Integration
├── scripts/             # Installations- und Utility-Skripte
├── tools/               # Entwicklerwerkzeuge
```

## Komponenten

### API-Server

Der API-Server stellt die Hauptschnittstelle für Geräte und Benutzeranwendungen bereit.

- **Minimal HTTP Server**: Ein einfacher Server ohne externe Abhängigkeiten (`api/minimal_http_server.py`)
- **FastAPI-Anwendung**: Hauptanwendung mit vollständigen Funktionen (derzeit deaktiviert)

### MQTT-Broker

Der MQTT-Broker ermöglicht die Kommunikation mit IoT-Geräten:

- Läuft auf Port 1883 (MQTT) und 9001 (MQTT über WebSocket)
- Konfiguration in `mqtt/mosquitto.conf`
- Die MQTT-Kommunikation erfolgt ausschließlich über Python (paho-mqtt)
- Die PHP-MQTT-Extension wird nicht mehr verwendet

### ESP-Firmware

Die ESP-Firmware unterstützt verschiedene Gerätetypen:

- ESP32C6 (neuere Geräte): `esp/SwissAirDry_ESP32C6_MQTT.ino`
- ESP8266/Wemos D1 Mini (ältere Geräte): `arduino/SwissAirDry_Wemos_Display_*.ino`

## Entwicklung und Installation

Für Entwickler:

1. Starten Sie den Minimal HTTP Server:
   ```
   cd swissairdry/api
   python minimal_http_server.py
   ```

2. Starten Sie den MQTT Broker:
   ```
   mkdir -p /tmp/mosquitto/data /tmp/mosquitto/log
   chmod -R 777 /tmp/mosquitto
   mosquitto -c swissairdry/mqtt/mosquitto.conf
   ```

Für Produktionsumgebungen, verwenden Sie die Docker-Konfiguration in `docker/`.

## Kontakt

Bei Fragen oder Problemen wenden Sie sich an:

- E-Mail: info@vgnc.org
- Website: https://vgnc.org

## Lizenz

Copyright © 2025 SwissAirDry - Alle Rechte vorbehalten