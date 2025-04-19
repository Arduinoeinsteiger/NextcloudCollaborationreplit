# SwissAirDry Dokumentation

Diese Dokumentation enthält alle Informationen zur Installation, Konfiguration und Verwendung des SwissAirDry-Systems.

## Verfügbare Dokumentationen

### Installation und Konfiguration
- [Installationsanleitung (Deutsch)](INSTALLATIONSANLEITUNG.md) - Detaillierte Installationsanleitung in deutscher Sprache
- [Installation Guide for Warp (English)](WARP_INSTALLATION_GUIDE.md) - Installation guide in English for Warp

### Integration und Erweiterungen
- [Nextcloud-Integration](NEXTCLOUD_INTEGRATION.md) - Anleitung zur Integration mit Nextcloud
- [ESP32-Konfiguration](ESP32_KONFIGURATION.md) - Anleitung zur Konfiguration von ESP32-Geräten

### Problemlösung
- [Fehlerbehebung](FEHLERBEHEBUNG.md) - Lösungen für häufige Probleme

## Architektur des SwissAirDry-Systems

Das SwissAirDry-System besteht aus mehreren Komponenten, die zusammenarbeiten:

1. **API-Server**: Zentraler Hub, der alle Komponenten verbindet und Funktionen bereitstellt
   - Implementiert in FastAPI (Python)
   - RESTful API-Endpunkte für Geräteverwaltung, Sensordaten, Benutzerauthentifizierung, etc.
   - Verbindung zur Datenbank und zum MQTT-Broker

2. **MQTT-Broker**: Kommunikationsplattform für IoT-Geräte
   - Verwendet Mosquitto
   - Ermöglicht Echtzeit-Kommunikation zwischen Geräten und dem Server
   - Unterstützt WebSockets für Web-Clients

3. **Datenbank**: Speichert alle persistenten Daten
   - PostgreSQL-Datenbank
   - Speichert Geräte, Sensordaten, Benutzer, etc.

4. **Nextcloud-Integration**: Integration mit Nextcloud für Dateiverwaltung
   - Als External App implementiert
   - Sichere Kommunikation mit dem API-Server

5. **ESP-Firmware**: Firmware für ESP8266/ESP32-Geräte
   - Kommunikation über REST API oder MQTT
   - Unterstützung für verschiedene Sensoren und Displays
   - OTA-Update-Funktionalität

## Datenbankschema

Die Datenbank enthält folgende Haupttabellen:

- **devices**: Informationen über registrierte Geräte
- **sensor_data**: Sensordaten von den Geräten
- **users**: Benutzerinformationen (in der vollständigen Implementierung)
- **jobs**: Auftragsinformationen (in der vollständigen Implementierung)
- **customers**: Kundeninformationen (in der vollständigen Implementierung)

## MQTT-Topics

Das System verwendet folgende MQTT-Topics:

- `swissairdry/{device_id}/data`: Sensordaten vom Gerät
- `swissairdry/{device_id}/cmd/{command}`: Befehle an das Gerät
- `swissairdry/{device_id}/status`: Status des Geräts

## API-Endpunkte

Die wichtigsten API-Endpunkte sind:

- `/api/devices`: Verwaltung von Geräten
- `/api/devices/{device_id}/data`: Sensordaten eines Geräts
- `/api/devices/{device_id}/command`: Befehle an ein Gerät senden

## Docker-Konfiguration

Alle Komponenten sind in Docker-Containern gekapselt:

- `api`: FastAPI-Server
- `postgres`: PostgreSQL-Datenbank
- `mqtt`: Mosquitto MQTT-Broker
- `nextcloud_app`: Nextcloud-Integration (optional)

## Sicherheit

Das System implementiert folgende Sicherheitsmaßnahmen:

- JWT-basierte Authentifizierung
- MQTT-Authentifizierung (optional)
- HTTPS für API-Endpunkte (in Produktionsumgebungen)
- Sichere Speicherung von Passwörtern
- CORS-Konfiguration für Web-Clients