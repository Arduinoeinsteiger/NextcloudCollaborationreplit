# SwissAirDry API-Dokumentation

Willkommen bei der Dokumentation für die SwissAirDry API. Diese API ermöglicht die Verwaltung und Überwachung von SwissAirDry-Geräten, sowie die Steuerung von Luftentfeuchtern in Echtzeit.

## Dokumentationsressourcen

Hier finden Sie alle Ressourcen zur API-Dokumentation:

- [**Ausführliche API-Dokumentation**](API_DOCUMENTATION.md): Detaillierte Beschreibung aller API-Endpunkte, Parameter und Antwortformate
- [**Interaktive API-Dokumentation (Swagger)**](https://api.vgnc.org/v1/docs): Interaktive Schnittstelle zum Testen der API-Endpunkte
- [**OpenAPI-Spezifikation**](https://api.vgnc.org/v1/openapi.json): OpenAPI/Swagger-Spezifikation im JSON-Format

## Code-Beispiele

In der Datei [`code_examples.py`](code_examples.py) finden Sie Code-Beispiele für die Verwendung der API in verschiedenen Programmiersprachen:

- **Python**: Beispiele für die Verwendung der API mit Python und der Requests-Bibliothek
- **JavaScript/Node.js**: Beispiele für die Verwendung der API mit JavaScript und Axios
- **ESP8266/Arduino**: Beispiele für die Integration der API in ESP8266- oder ESP32-basierte IoT-Geräte

## API-Versionen

| Version | Status | Beschreibung |
|---------|--------|--------------|
| v1      | Stabil | Aktuelle Haupt-API-Version |
| simple  | Beta   | Vereinfachte API für Testzwecke (Port 5001) |

## MQTT-Integration

Die SwissAirDry API integriert MQTT für Echtzeit-Kommunikation mit Geräten. Der MQTT-Broker ist unter `mqtt.swissairdry.com` oder `api.vgnc.org` auf Port 1883 (unverschlüsselt) und 8883 (TLS/SSL) erreichbar.

MQTT-Themen folgen diesem Muster:
- Gerätedaten: `swissairdry/{device_id}/data`
- Gerätestatus: `swissairdry/{device_id}/status`
- Gerätebefehle: `swissairdry/{device_id}/cmd/{command}`

## Authentifizierung und Sicherheit

Die API verwendet API-Schlüssel zur Authentifizierung. API-Schlüssel müssen im HTTP-Header `X-API-Key` mitgegeben werden.

Der MQTT-Broker kann sowohl mit als auch ohne Authentifizierung genutzt werden, je nach Konfiguration.

## Support und Kontakt

Bei Fragen oder Problemen wenden Sie sich bitte an:

- E-Mail: [info@swissairdry.com](mailto:info@swissairdry.com)
- Support: [support@swissairdry.com](mailto:support@swissairdry.com)
- Website: [www.swissairdry.com](https://www.swissairdry.com)

## Changelog

### v1.0.0 (22. April 2025)
- Erste stabile Version der API
- Unterstützung für Geräte-, Sensordaten-, Kunden- und Auftragsverwaltung
- MQTT-Integration für Echtzeit-Gerätekommunikation
- Verbesserte Authentifizierung und Sicherheit

### v0.9.0 (15. März 2025)
- Beta-Version der API
- Grundlegende Funktionalität für Geräteverwaltung und Sensordaten

## Lizenz

Die Verwendung dieser API und Dokumentation unterliegt den [SwissAirDry-Lizenzbedingungen](https://www.swissairdry.com/license).

© 2023-2025 Swiss Air Dry Team. Alle Rechte vorbehalten.