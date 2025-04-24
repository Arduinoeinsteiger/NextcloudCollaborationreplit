# SwissAirDry - Projekt Update

## Projektübersicht

SwissAirDry ist eine modulare IoT-Plattform für die Überwachung und Steuerung von Trocknungsgeräten, die folgende Komponenten umfasst:

- **API-Server**: FastAPI-basierte REST-API für die Geräteverwaltung
- **MQTT-Broker**: Für die Kommunikation mit IoT-Geräten
- **Nextcloud-Integration**: ExApp für die nahtlose Einbindung in Nextcloud
- **ESP32/ESP8266-Firmware**: MicroPython- und Arduino-basierte Lösungen für die Geräte

## Aktuelle Entwicklungen

### 1. Nextcloud ExApp-Integration

Die Nextcloud-Integration wurde modernisiert und als ExApp nach dem neuesten Standard implementiert:

- **Manifest**: Entspricht den aktuellen Nextcloud ExApp-Anforderungen (v26+)
- **Frontend**: Vue 3-basierte Benutzeroberfläche mit reaktivem Design und Dunkelmodus
- **Dashboard**: Übersichtliche Darstellung aller verbundenen Geräte und Alarme
- **API-Service**: Verbindung zur SwissAirDry API mit vollständiger Fehlerbehandlung
- **Deck-Integration**: Automatische Erstellung von Boards und Karten in Nextcloud Deck

### 2. API-Server (FastAPI)

Der API-Server wurde erweitert um:

- **Dashboard-Endpunkte**: Vollständige Informationen über Geräte und Alarme
- **Pydantic-Schemas**: Umfassende Schemas für alle Entitäten (Geräte, Sensoren, Alarme, Jobs, Berichte)
- **Service-Struktur**: Modulare Dienste für MQTT, Deck-Integration und Datenbankzugriff

### 3. MicroPython-Implementierung für ESP32-C6

Eine vollständige MicroPython-Lösung für ESP32-C6 wurde entwickelt:

- **Modularität**: Separate Module für MQTT, Sensoren und Konfiguration
- **Robustheit**: Automatische Wiederverbindung mit Exponential Backoff
- **Konfigurierbarkeit**: JSON-basierte Konfiguration für einfache Anpassungen

## Port-Konfiguration

| Port | Dienst | Beschreibung |
|------|--------|-------------|
| 80/443 | HTTP/HTTPS | Standard-Webserver (Reverse Proxy) |
| 5000 | SwissAirDry API | Hauptschnittstelle für alle Komponenten |
| 5001 | SwissAirDry Simple API | Vereinfachte API für ressourcenbeschränkte Geräte |
| 1883 | MQTT Broker | Standard MQTT-Port für Gerätekommunikation |
| 9001 | MQTT Websocket | Websocket-Verbindungen für Webanwendungen |
| 5432 | PostgreSQL | Datenbank für Geräte, Sensoren und Alarme |
| 8080 | Nextcloud | Nextcloud-Webserver |
| 3000 | ExApp-Server | Frontend-Server für die ExApp |
| 8701 | ExApp-Daemon | Backend-Daemon für die ExApp-Integration |

## Domainstruktur (vgnc.org)

Die Domain vgnc.org wird für den Zugriff auf die SwissAirDry-Dienste verwendet:

- **vgnc.org**: Hauptwebsite
- **api.vgnc.org**: SwissAirDry API
- **talk.vgnc.org**: Kommunikationsplattform (z.B. Nextcloud Talk)

Die Domain ist bei Cloudflare konfiguriert mit:
- IPv4: 83.78.73.133
- IPv6: 2a02:1210:3a07:2700:3ea8:2aff:fe9f:a9c

## Nächste Schritte

1. **Vue-Router-Konfiguration**: Implementierung der fehlenden Routen für Geräte, Alarme, Einstellungen
2. **API-Endpunkte**: Vervollständigung der API mit allen notwendigen Endpunkten
3. **Datenbank-Migration**: Implementierung von Alembic für strukturierte Datenbankmigrationen
4. **Authentifizierung**: OAuth2-basierte Authentifizierung mit JWT-Tokens
5. **Dokumentation**: Vollständige API-Dokumentation mit Swagger/OpenAPI

## Verwendete Technologien

- **Backend**: Python 3.11, FastAPI, SQLAlchemy, Pydantic
- **Frontend**: Vue 3, Composition API, Vite
- **Datenbank**: PostgreSQL
- **IoT**: MQTT, MicroPython, ESP32-C6/ESP8266
- **Nextcloud**: ExApp API, Deck API, OCS API
- **Container**: Docker, Docker Compose
- **Proxy**: Nginx