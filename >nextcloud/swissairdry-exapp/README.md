# SwissAirDry ExApp für Nextcloud

Diese App integriert die SwissAirDry IoT-Plattform nahtlos in Nextcloud und ermöglicht die Steuerung und Überwachung von Trocknungsgeräten direkt aus Ihrer Nextcloud-Umgebung.

## Features

- **Dashboard**: Übersicht über alle verbundenen Geräte mit Echtzeitstatus
- **Geräteüberwachung**: Detaillierte Ansicht aller Sensordaten und Telemetrieinformationen
- **Alarmmanagement**: Sofortige Benachrichtigung bei Problemen oder Warnungen
- **Deck-Integration**: Automatische Erstellung von Boards und Karten in Nextcloud Deck
- **Dunkelmodus**: Vollständige Unterstützung für den Nextcloud-Dunkelmodus

## Installationsanleitung

### Installation via App Store (empfohlen)

1. Öffnen Sie Ihre Nextcloud-Instanz als Administrator
2. Gehen Sie zu "Apps" → "App-Verwaltung"
3. Wählen Sie die Kategorie "Monitoring" oder suchen Sie nach "SwissAirDry"
4. Klicken Sie auf "Installieren"

### Manuelle Installation

1. Laden Sie die neueste Version herunter: [Releases](https://github.com/swissairdry/swissairdry-exapp/releases)
2. Entpacken Sie die ZIP-Datei in das `apps`-Verzeichnis Ihrer Nextcloud-Installation
3. Aktivieren Sie die App in der Nextcloud-App-Verwaltung

### Docker-Installation

Bei Verwendung von Docker für Ihre Nextcloud-Instanz:

```bash
# Docker-Compose Beispiel
version: '3'
services:
  nextcloud:
    image: nextcloud
    volumes:
      - ./swissairdry-exapp:/var/www/html/custom_apps/swissairdry
    # ... andere Nextcloud-Konfigurationen
```

## Port-Konfiguration

Die SwissAirDry ExApp und ihre Komponenten verwenden standardmäßig die folgenden Ports:

- **Nextcloud-Webserver**: 8080
- **Reverse Proxy**: 80, 443
- **SwissAirDry API**: 5000
- **SwissAirDry Simple API**: 5001
- **ExApp-Server**: 3000
- **ExApp-Daemon**: 8701
- **MQTT-Broker**: 1883 (MQTT), 9001 (Websocket)
- **PostgreSQL**: 5432

Stellen Sie sicher, dass diese Ports in Ihrer Firewall freigeschaltet sind.

## Konfiguration

Nach der Installation erfolgt die Konfiguration über die Nextcloud-Admin-Einstellungen:

1. Gehen Sie zu "Einstellungen" → "Administration" → "SwissAirDry ExApp"
2. Konfigurieren Sie die Verbindung zur SwissAirDry API
3. Optional: Aktivieren Sie die Deck-Integration und andere Features

## Betriebsmodi

### Standalone-Modus

Im Standalone-Modus benötigt die App einen externen SwissAirDry API-Server. 
Konfigurieren Sie die API-URL in den Einstellungen.

### Integrierter Modus

Im integrierten Modus startet die App automatisch einen eigenen SwissAirDry API-Server 
als Daemon-Prozess und verwaltet die Verbindung zu Ihren Geräten.

## Entwicklung

### Anforderungen

- Node.js 16+
- NPM 7+
- PHP 8.0+
- Nextcloud 26+

### Setup für Entwicklung

```bash
# Repository klonen
git clone https://github.com/swissairdry/swissairdry-exapp.git
cd swissairdry-exapp

# Abhängigkeiten installieren
npm install

# Dev-Server starten
npm run dev
```

### Build für Produktion

```bash
npm run build
```

## Support

Bei Fragen oder Problemen kontaktieren Sie uns:

- GitHub Issues: [https://github.com/swissairdry/swissairdry-exapp/issues](https://github.com/swissairdry/swissairdry-exapp/issues)
- E-Mail: [support@swissairdry.com](mailto:support@swissairdry.com)

## Lizenz

GNU Affero General Public License v3.0 (AGPL-3.0)