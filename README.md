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

## Systemarchitektur

Das SwissAirDry-System besteht aus folgenden Komponenten:

1. **API-Server**: FastAPI-basierter Backend-Server
2. **Datenbank**: PostgreSQL für persistente Datenspeicherung
3. **MQTT-Broker**: Für IoT-Kommunikation mit ESP-Geräten
4. **Nextcloud-Integration**: ExApp für Nextcloud
5. **Nginx**: Reverse Proxy für HTTPS und Routing
6. **ESP-Firmware**: Angepasste Firmware für ESP32C6/ESP8266-Geräte

## Installation

### Voraussetzungen

- Docker und Docker Compose
- SSL-Zertifikate (optional, für Produktionsumgebung empfohlen)
- Domain mit DNS-Konfiguration (für Produktionsumgebung)

### Schnellinstallation

1. Repository klonen:
   ```
   git clone https://github.com/swissairdry/swissairdry.git
   cd swissairdry
   ```

2. Installation ausführen:
   ```
   chmod +x install.sh
   ./install.sh
   ```

3. Konfigurieren Sie die `.env`-Datei mit Ihren Einstellungen

4. System starten:
   ```
   docker-compose up -d
   ```

### Manuelle Installation

1. Verzeichnisstruktur erstellen:
   ```
   chmod +x mkdir.sh
   ./mkdir.sh
   ```

2. SSL-Zertifikate in `ssl/certs/` und `ssl/private/` ablegen

3. `.env`-Datei aus `.env.example` erstellen und anpassen

4. System starten:
   ```
   docker-compose up -d
   ```

## ESP-Firmware

Die aktuelle ESP-Firmware unterstützt folgende Geräte:

- ESP32C6 (empfohlen für neue Installationen)
- ESP8266 (Wemos D1 Mini, für bestehende Installationen)

### ESP32C6-Firmware installieren

1. Arduino IDE öffnen
2. ESP32C6-Board-Support installieren
3. Benötigte Bibliotheken installieren
4. `SwissAirDry_ESP32C6_MQTT.ino` öffnen und hochladen

## Wartung und Update

- System aktualisieren:
  ```
  docker-compose pull
  docker-compose up -d
  ```

- Logs anzeigen:
  ```
  docker-compose logs -f
  ```

- System neustarten:
  ```
  docker-compose restart
  ```

- System stoppen:
  ```
  docker-compose down
  ```

## Kontakt

Bei Fragen oder Problemen wenden Sie sich an:

- E-Mail: info@vgnc.org
- Website: https://vgnc.org

## Lizenz

Copyright © 2025 SwissAirDry - Alle Rechte vorbehalten