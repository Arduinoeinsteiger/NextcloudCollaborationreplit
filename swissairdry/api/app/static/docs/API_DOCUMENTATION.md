# SwissAirDry API-Dokumentation

Version: 1.0.0  
Autor: Swiss Air Dry Team <info@swissairdry.com>  
Letzte Aktualisierung: 22. April 2025

## Übersicht

Die SwissAirDry API ermöglicht die Verwaltung von Luftentfeuchtern, Sensordaten, Kunden und Aufträgen. Diese Dokumentation beschreibt die verfügbaren Endpunkte, Anforderungsformate und Antwortstrukturen für die API.

## Basis-URL

```
https://api.vgnc.org/v1
```

Für lokale Entwicklung:
```
http://localhost:5000
```

## Authentifizierung

Die API unterstützt Authentifizierung über API-Schlüssel. Der API-Schlüssel muss in allen Anfragen im HTTP-Header `X-API-Key` mitgegeben werden:

```
X-API-Key: ihr_api_schlüssel
```

## Geräte (Devices)

### Liste aller Geräte abrufen

Gibt eine Liste aller registrierten Geräte zurück.

**Endpunkt:** `GET /api/devices`

**Parameter:**
- `skip` (optional): Anzahl der zu überspringenden Einträge (Standard: 0)
- `limit` (optional): Maximale Anzahl zurückzugebender Einträge (Standard: 100)

**Beispielanfrage:**
```bash
curl -X GET "https://api.vgnc.org/v1/api/devices?limit=10" -H "X-API-Key: ihr_api_schlüssel"
```

**Erfolgreiche Antwort:** (Code 200)
```json
[
  {
    "id": "1",
    "device_id": "device001",
    "name": "Luftentfeuchter 1",
    "description": "Kundengerät im Keller",
    "type": "standard",
    "location": "Zürich",
    "customer_id": 42,
    "job_id": 123,
    "mqtt_topic": "swissairdry/device001",
    "firmware_version": "1.2.3",
    "configuration": {
      "remote_control": {
        "enabled": true,
        "relay_state": false
      }
    },
    "status": "online",
    "last_seen": "2025-04-22T10:30:00",
    "created_at": "2025-01-15T08:00:00",
    "updated_at": "2025-04-22T10:30:00"
  },
  // weitere Geräte...
]
```

### Neues Gerät erstellen

**Endpunkt:** `POST /api/devices`

**Anfragekörper (JSON):**
```json
{
  "device_id": "device003",
  "name": "Neuer Luftentfeuchter",
  "description": "Im Wohnzimmer",
  "type": "premium",
  "location": "Bern",
  "customer_id": 42,
  "job_id": 123,
  "firmware_version": "1.0.0"
}
```

**Erfolgreiche Antwort:** (Code 200)
```json
{
  "id": "3",
  "device_id": "device003",
  "name": "Neuer Luftentfeuchter",
  "description": "Im Wohnzimmer",
  "type": "premium",
  "location": "Bern",
  "customer_id": 42,
  "job_id": 123,
  "mqtt_topic": "swissairdry/device003",
  "firmware_version": "1.0.0",
  "configuration": null,
  "status": "offline",
  "last_seen": null,
  "created_at": "2025-04-22T12:00:00",
  "updated_at": null
}
```

**Fehlerantwort:** (Code 400)
```json
{
  "detail": "Gerät mit dieser ID existiert bereits"
}
```

### Gerät nach ID abrufen

**Endpunkt:** `GET /api/devices/{device_id}`

**Parameter:**
- `device_id`: ID des abzurufenden Geräts

**Beispielanfrage:**
```bash
curl -X GET "https://api.vgnc.org/v1/api/devices/device001" -H "X-API-Key: ihr_api_schlüssel"
```

**Erfolgreiche Antwort:** (Code 200)
```json
{
  "id": "1",
  "device_id": "device001",
  "name": "Luftentfeuchter 1",
  "description": "Kundengerät im Keller",
  "type": "standard",
  "location": "Zürich",
  "customer_id": 42,
  "job_id": 123,
  "mqtt_topic": "swissairdry/device001",
  "firmware_version": "1.2.3",
  "configuration": {
    "remote_control": {
      "enabled": true,
      "relay_state": false
    }
  },
  "status": "online",
  "last_seen": "2025-04-22T10:30:00",
  "created_at": "2025-01-15T08:00:00",
  "updated_at": "2025-04-22T10:30:00"
}
```

**Fehlerantwort:** (Code 404)
```json
{
  "detail": "Gerät nicht gefunden"
}
```

### Gerät aktualisieren

**Endpunkt:** `PUT /api/devices/{device_id}`

**Parameter:**
- `device_id`: ID des zu aktualisierenden Geräts

**Anfragekörper (JSON):**
```json
{
  "name": "Aktualisierter Name",
  "description": "Neue Beschreibung",
  "firmware_version": "1.2.4"
}
```

**Erfolgreiche Antwort:** (Code 200)
```json
{
  "id": "1",
  "device_id": "device001",
  "name": "Aktualisierter Name",
  "description": "Neue Beschreibung",
  "type": "standard",
  "location": "Zürich",
  "customer_id": 42,
  "job_id": 123,
  "mqtt_topic": "swissairdry/device001",
  "firmware_version": "1.2.4",
  "configuration": {
    "remote_control": {
      "enabled": true,
      "relay_state": false
    }
  },
  "status": "online",
  "last_seen": "2025-04-22T10:30:00",
  "created_at": "2025-01-15T08:00:00",
  "updated_at": "2025-04-22T14:00:00"
}
```

**Fehlerantwort:** (Code 404)
```json
{
  "detail": "Gerät nicht gefunden"
}
```

### Gerät löschen

**Endpunkt:** `DELETE /api/devices/{device_id}`

**Parameter:**
- `device_id`: ID des zu löschenden Geräts

**Beispielanfrage:**
```bash
curl -X DELETE "https://api.vgnc.org/v1/api/devices/device001" -H "X-API-Key: ihr_api_schlüssel"
```

**Erfolgreiche Antwort:** (Code 200)
```json
{
  "message": "Gerät device001 gelöscht"
}
```

**Fehlerantwort:** (Code 404)
```json
{
  "detail": "Gerät nicht gefunden"
}
```

## Sensordaten

### Sensordaten eines Geräts abrufen

**Endpunkt:** `GET /api/device/{device_id}/data`

**Parameter:**
- `device_id`: ID des Geräts
- `limit` (optional): Maximale Anzahl zurückzugebender Einträge (Standard: 100)

**Beispielanfrage:**
```bash
curl -X GET "https://api.vgnc.org/v1/api/device/device001/data?limit=10" -H "X-API-Key: ihr_api_schlüssel"
```

**Erfolgreiche Antwort:** (Code 200)
```json
[
  {
    "id": 1,
    "device_id": "1",
    "timestamp": "2025-04-22T14:30:00",
    "temperature": 22.5,
    "humidity": 65.8,
    "power": 450.0,
    "energy": 12.5,
    "relay_state": true,
    "runtime": 3600,
    "extra_data": null
  },
  // weitere Sensordaten...
]
```

**Fehlerantwort:** (Code 404)
```json
{
  "detail": "Gerät nicht gefunden"
}
```

### Sensordaten hinzufügen

**Endpunkt:** `POST /api/device/{device_id}/data`

**Parameter:**
- `device_id`: ID des Geräts

**Anfragekörper (JSON):**
```json
{
  "temperature": 23.1,
  "humidity": 64.5,
  "power": 420.0,
  "energy": 13.2,
  "relay_state": true,
  "runtime": 4200
}
```

**Erfolgreiche Antwort:** (Code 200)
```json
{
  "status": "ok",
  "relay_control": false
}
```

**Hinweis:** Wenn das Gerät nicht gefunden wird, wird es automatisch erstellt.

## Gerätebefehle

### Befehl an Gerät senden

**Endpunkt:** `POST /api/device/{device_id}/command`

**Parameter:**
- `device_id`: ID des Geräts

**Anfragekörper (JSON):**
```json
{
  "command": "relay",
  "value": true
}
```

**Erfolgreiche Antwort:** (Code 200)
```json
{
  "message": "Befehl gesendet"
}
```

**Fehlerantwort:** (Code 404)
```json
{
  "detail": "Gerät nicht gefunden"
}
```

## Kunden

### Liste aller Kunden abrufen

**Endpunkt:** `GET /api/customers`

**Parameter:**
- `skip` (optional): Anzahl der zu überspringenden Einträge (Standard: 0)
- `limit` (optional): Maximale Anzahl zurückzugebender Einträge (Standard: 100)

**Beispielanfrage:**
```bash
curl -X GET "https://api.vgnc.org/v1/api/customers?limit=10" -H "X-API-Key: ihr_api_schlüssel"
```

**Erfolgreiche Antwort:** (Code 200)
```json
[
  {
    "id": 1,
    "name": "Max Mustermann",
    "email": "max@example.com",
    "phone": "+41 12 345 67 89",
    "address": "Musterstraße 123",
    "postal_code": "8000",
    "city": "Zürich",
    "country": "Schweiz",
    "notes": "Wichtiger Kunde",
    "external_id": "CUST001",
    "created_at": "2025-01-15T08:00:00",
    "updated_at": "2025-04-20T09:00:00"
  },
  // weitere Kunden...
]
```

### Neuen Kunden erstellen

**Endpunkt:** `POST /api/customers`

**Anfragekörper (JSON):**
```json
{
  "name": "Erika Musterfrau",
  "email": "erika@example.com",
  "phone": "+41 98 765 43 21",
  "address": "Beispielweg 42",
  "postal_code": "3000",
  "city": "Bern",
  "country": "Schweiz",
  "notes": "Neukunde",
  "external_id": "CUST002"
}
```

**Erfolgreiche Antwort:** (Code 200)
```json
{
  "id": 2,
  "name": "Erika Musterfrau",
  "email": "erika@example.com",
  "phone": "+41 98 765 43 21",
  "address": "Beispielweg 42",
  "postal_code": "3000",
  "city": "Bern",
  "country": "Schweiz",
  "notes": "Neukunde",
  "external_id": "CUST002",
  "created_at": "2025-04-22T15:00:00",
  "updated_at": null
}
```

## Aufträge

### Liste aller Aufträge abrufen

**Endpunkt:** `GET /api/jobs`

**Parameter:**
- `skip` (optional): Anzahl der zu überspringenden Einträge (Standard: 0)
- `limit` (optional): Maximale Anzahl zurückzugebender Einträge (Standard: 100)

**Beispielanfrage:**
```bash
curl -X GET "https://api.vgnc.org/v1/api/jobs?limit=10" -H "X-API-Key: ihr_api_schlüssel"
```

**Erfolgreiche Antwort:** (Code 200)
```json
[
  {
    "id": 1,
    "customer_id": 1,
    "title": "Wasserschaden sanieren",
    "description": "Wasserschaden im Keller nach Überschwemmung",
    "location": "Zürich",
    "status": "in_bearbeitung",
    "start_date": "2025-04-15T08:00:00",
    "end_date": null,
    "notes": "3 Geräte installiert",
    "photos": ["job1_photo1.jpg", "job1_photo2.jpg"],
    "external_id": "JOB001",
    "invoice_id": null,
    "created_at": "2025-04-15T07:30:00",
    "updated_at": "2025-04-20T10:00:00"
  },
  // weitere Aufträge...
]
```

### Neuen Auftrag erstellen

**Endpunkt:** `POST /api/jobs`

**Anfragekörper (JSON):**
```json
{
  "customer_id": 2,
  "title": "Feuchtigkeitsprüfung",
  "description": "Regelmäßige Feuchtigkeitsprüfung im Neubau",
  "location": "Bern",
  "status": "offen",
  "start_date": "2025-04-25T09:00:00",
  "notes": "Erstprüfung",
  "external_id": "JOB002"
}
```

**Erfolgreiche Antwort:** (Code 200)
```json
{
  "id": 2,
  "customer_id": 2,
  "title": "Feuchtigkeitsprüfung",
  "description": "Regelmäßige Feuchtigkeitsprüfung im Neubau",
  "location": "Bern",
  "status": "offen",
  "start_date": "2025-04-25T09:00:00",
  "end_date": null,
  "notes": "Erstprüfung",
  "photos": null,
  "external_id": "JOB002",
  "invoice_id": null,
  "created_at": "2025-04-22T15:30:00",
  "updated_at": null
}
```

## Fehlerantworten

Die API gibt standardisierte HTTP-Statuscodes zurück, um Erfolg oder Fehler einer Anfrage zu signalisieren:

- `200 OK`: Die Anfrage wurde erfolgreich bearbeitet
- `400 Bad Request`: Die Anfrage enthält ungültige Parameter oder Daten
- `401 Unauthorized`: API-Schlüssel fehlt oder ist ungültig
- `403 Forbidden`: Keine Berechtigung für den angeforderten Zugriff
- `404 Not Found`: Die angeforderte Ressource wurde nicht gefunden
- `500 Internal Server Error`: Serverfehler

## MQTT-Integration

Die SwissAirDry API integriert MQTT für Echtzeit-Kommunikation mit Geräten. MQTT-Themen folgen diesem Muster:

- Gerätedaten: `swissairdry/{device_id}/data`
- Gerätebefehle: `swissairdry/{device_id}/cmd/{command}`

Beispiel: Ein Relay-Befehl wird an das Thema `swissairdry/device001/cmd/relay` gesendet.

## Einfache API

Neben der Haupt-API gibt es auch eine vereinfachte Version der API, die unter Port 5001 läuft und grundlegende Funktionen ohne Datenbankanbindung bietet. Diese ist primär für Testzwecke gedacht.

## Weitere Ressourcen

- [Swagger-UI Dokumentation](/docs) - Interaktive API-Dokumentation
- [API Status](/health) - API-Statusseite mit Verfügbarkeitsinformationen