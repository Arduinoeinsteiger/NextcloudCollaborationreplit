# Swiss Air Dry - Nextcloud App

Eine umfassende IoT-Geräteverwaltungsplattform für Swiss Air Dry Systeme, integriert in Nextcloud.

## Features

- **Echtzeit-Überwachung**: Überwachung von Trocknungsgeräten in Echtzeit
- **Sensordaten-Visualisierung**: Anzeige von Temperatur, Luftfeuchtigkeit, Druck und Energieverbrauch
- **Standortverfolgung**: Ortung von Geräten über BLE/WiFi
- **Gerätekontrolle**: Fernsteuerung von Geräten über MQTT
- **Benachrichtigungen**: Automatische Benachrichtigungen bei kritischen Ereignissen
- **Berichterstellung**: Erstellung von Berichten und Visualisierung von Daten

## Installation

1. Platzieren Sie den `swissairdry`-Ordner in Ihrem Nextcloud-Apps-Verzeichnis
2. Aktivieren Sie die App in den Nextcloud-Einstellungen unter "Apps"
3. Konfigurieren Sie die App-Einstellungen (API-Endpunkt etc.)

## Konfiguration

In den App-Einstellungen können Sie folgende Parameter konfigurieren:

- **API-Endpunkt**: Die Adresse des SwissAirDry API-Servers (Standard: api.vgnc.org)
- **API-Port**: Der Port des API-Servers (Standard: 443)
- **API-Basispfad**: Der Basispfad der API (Standard: /v1)
- **MQTT-Broker**: Die Adresse des MQTT-Brokers (Standard: mqtt.vgnc.org)
- **MQTT-Port**: Der Port des MQTT-Brokers (Standard: 8883)

## Systemanforderungen

- Nextcloud 22 oder höher
- PHP 7.4 oder höher
- Internet-Verbindung zum SwissAirDry API-Server

## Hinweise für Entwickler

Die App kommuniziert mit der SwissAirDry API unter api.vgnc.org. Die Authentifizierung erfolgt über den Nextcloud-Benutzer. Die MQTT-Kommunikation dient der Echtzeit-Aktualisierung und Steuerung der Geräte.

### Entwicklungsumgebung einrichten

```bash
cd /path/to/nextcloud/apps
git clone https://github.com/swissairdry/nextcloud-app.git swissairdry
cd swissairdry
npm install   # für Frontend-Entwicklung
```

## Support

Bei Fragen oder Problemen wenden Sie sich bitte an:

- E-Mail: support@swissairdry.com
- Website: https://swissairdry.com

## Lizenz

AGPL v3