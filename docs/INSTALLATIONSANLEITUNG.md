# SwissAirDry Installationsanleitung

Dieses Dokument bietet detaillierte Anweisungen zur Installation und Konfiguration des SwissAirDry-Systems auf Ihrem Server. Das System besteht aus mehreren Komponenten, die zusammenarbeiten, um eine umfassende Lösung für die Verwaltung von Trocknungsgeräten zu bieten.

## Systemanforderungen

- Docker und Docker Compose (Version 1.29.0 oder höher)
- Mindestens 4GB RAM
- 20GB freier Festplattenspeicher
- Internetverbindung für Container-Downloads
- Offene Ports für Dienste:
  - 5000: API-Server
  - 1883: MQTT-Broker
  - 9001: MQTT WebSocket
  - 5432: PostgreSQL (optional, nur intern)

## Installationsschritte

### 1. Repository klonen

```bash
git clone https://github.com/swissairdry/swissairdry.git
cd swissairdry
```

### 2. Umgebungsvariablen konfigurieren

Erstellen Sie eine `.env`-Datei, indem Sie die Beispieldatei kopieren und die Werte anpassen:

```bash
cp .env.example .env
```

Bearbeiten Sie die `.env`-Datei mit Ihrem bevorzugten Texteditor und setzen Sie geeignete Werte für Ihre Umgebung:

```bash
# Wichtigste Einstellungen, die angepasst werden sollten:
POSTGRES_PASSWORD=your_secure_password
MQTT_PASSWORD=your_mqtt_password
AUTH_SECRET_KEY=your_very_long_secure_random_key
```

### 3. Verzeichnisstruktur erstellen

Erstellen Sie die erforderlichen Verzeichnisse für persistente Daten:

```bash
mkdir -p swissairdry/mqtt/auth
mkdir -p data/postgres
mkdir -p data/mqtt
```

### 4. MQTT-Authentifizierung konfigurieren (Optional, aber empfohlen)

Wenn Sie Ihren MQTT-Broker mit Authentifizierung sichern möchten:

```bash
# Passwortdatei erstellen
docker run --rm -it eclipse-mosquitto mosquitto_passwd -c /mosquitto/config/passwd swissairdry
# Sie werden aufgefordert, ein Passwort einzugeben

# Die generierte Passwortdatei kopieren
docker cp <container_id>:/mosquitto/config/passwd swissairdry/mqtt/auth/
```

Bearbeiten Sie dann `swissairdry/mqtt/mosquitto.conf`, um die Authentifizierung zu aktivieren:

```
# Kommentieren Sie diese Zeilen aus:
password_file /mosquitto/config/auth/passwd
allow_anonymous false
```

### 5. Dienste starten

Starten Sie den SwissAirDry-Stack:

```bash
docker-compose up -d
```

### 6. Installation überprüfen

Überprüfen Sie, ob alle Dienste laufen:

```bash
docker-compose ps
```

Greifen Sie auf den API-Server unter http://ihre-server-ip:5000 zu, um zu überprüfen, ob er funktioniert.

## Komponentenkonfiguration

### API-Server

Der API-Server stellt die Kernfunktionalität bereit und dient als zentraler Hub für alle Komponenten. Er wird über Umgebungsvariablen in der `.env`-Datei konfiguriert.

Wichtige Einstellungen:
- `API_PORT`: Der Port, auf dem der API-Server lauscht (Standard: 5000)
- `API_HOST`: Die Host-Adresse, an die gebunden werden soll (Standard: 0.0.0.0)
- `DATABASE_URL`: Verbindungszeichenfolge für die PostgreSQL-Datenbank

### MQTT-Broker

Der MQTT-Broker handhabt die Echtzeit-Kommunikation mit IoT-Geräten. Die Konfiguration wird in `swissairdry/mqtt/mosquitto.conf` gespeichert.

Wichtige Einstellungen:
- `MQTT_PORT`: Der Port für die MQTT-Kommunikation (Standard: 1883)
- `MQTT_WS_PORT`: WebSocket-Port für Browser-Clients (Standard: 9001)

### Datenbank

PostgreSQL speichert alle persistenten Daten. Die Datenbank wird beim ersten Start automatisch initialisiert.

Wichtige Einstellungen:
- `POSTGRES_USER`: Datenbank-Benutzername (Standard: swissairdry)
- `POSTGRES_PASSWORD`: Datenbank-Passwort (WICHTIG: ändern Sie dies!)
- `POSTGRES_DB`: Datenbankname (Standard: swissairdry)

## Nextcloud-Integration

Um mit Nextcloud zu integrieren, müssen Sie die SwissAirDry-App in Ihrer Nextcloud-Instanz installieren.

1. Kopieren Sie das Verzeichnis `swissairdry/nextcloud/app` in Ihr Nextcloud-Apps-Verzeichnis
2. Aktivieren Sie die App in den Nextcloud-Einstellungen
3. Konfigurieren Sie die Verbindung zu Ihrem SwissAirDry API-Server

## ESP32-Gerätekonfiguration

Um ESP32-Geräte für die Arbeit mit dem SwissAirDry-System zu konfigurieren:

1. Flashen Sie die entsprechende Firmware auf Ihr ESP32-Gerät (ESP32C6 empfohlen)
2. Konfigurieren Sie die WLAN-Einstellungen in der Firmware
3. Setzen Sie die MQTT-Broker-Adresse auf Ihren Server
4. Weisen Sie jedem Gerät eine eindeutige Geräte-ID zu

## Backup und Wartung

### Datenbank-Backup

Um die PostgreSQL-Datenbank zu sichern:

```bash
docker-compose exec postgres pg_dump -U swissairdry swissairdry > backup.sql
```

### Logs

Logs für die Fehlerbehebung anzeigen:

```bash
# Alle Dienste
docker-compose logs

# Spezifischer Dienst
docker-compose logs api
docker-compose logs mqtt
docker-compose logs postgres
```

## Fehlerbehebung

### Verbindungsprobleme

Wenn Geräte keine Verbindung zum MQTT-Broker herstellen können:
- Überprüfen Sie, ob der MQTT-Port (1883) in Ihrer Firewall geöffnet ist
- Verifizieren Sie, dass der MQTT-Broker läuft (`docker-compose ps`)
- Überprüfen Sie die MQTT-Logs auf Authentifizierungsfehler

### Datenbankprobleme

Wenn der API-Server keine Verbindung zur Datenbank herstellen kann:
- Stellen Sie sicher, dass der PostgreSQL-Container läuft
- Überprüfen Sie die Datenbank-Anmeldedaten in `.env`
- Verifizieren Sie die Datenbankverbindung in den API-Server-Logs

### Weboberfläche nicht verfügbar

Wenn die Weboberfläche nicht zugänglich ist:
- Überprüfen Sie, ob der API-Server läuft
- Verifizieren Sie, dass der API-Port (5000) in Ihrer Firewall geöffnet ist
- Überprüfen Sie die API-Server-Logs auf Startfehler

## Aktualisierung

Um das SwissAirDry-System zu aktualisieren:

```bash
git pull
docker-compose down
docker-compose pull
docker-compose up -d
```