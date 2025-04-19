# SwissAirDry Installation Guide

This document provides detailed instructions for installing and configuring the SwissAirDry system on your server. The system consists of multiple components that work together to provide a comprehensive solution for managing drying equipment.

## System Requirements

- Docker and Docker Compose (version 1.29.0 or higher)
- Minimum 4GB RAM
- 20GB free disk space
- Internet connection for container downloads
- Open ports for services:
  - 5000: API Server
  - 1883: MQTT Broker
  - 9001: MQTT WebSocket
  - 5432: PostgreSQL (optional, internal only)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/swissairdry/swissairdry.git
cd swissairdry
```

### 2. Configure Environment Variables

Create a `.env` file by copying the example file and adjusting the values:

```bash
cp .env.example .env
```

Edit the `.env` file with your preferred text editor and set appropriate values for your environment:

```bash
# Essential settings to modify:
POSTGRES_PASSWORD=your_secure_password
MQTT_PASSWORD=your_mqtt_password
AUTH_SECRET_KEY=your_very_long_secure_random_key
```

### 3. Create Folder Structure

Create the required directories for persistent data:

```bash
mkdir -p swissairdry/mqtt/auth
mkdir -p data/postgres
mkdir -p data/mqtt
```

### 4. Configure MQTT Authentication (Optional but Recommended)

If you want to secure your MQTT broker with authentication:

```bash
# Create password file
docker run --rm -it eclipse-mosquitto mosquitto_passwd -c /mosquitto/config/passwd swissairdry
# You will be prompted to enter a password

# Copy the generated passwd file
docker cp <container_id>:/mosquitto/config/passwd swissairdry/mqtt/auth/
```

Then edit `swissairdry/mqtt/mosquitto.conf` to enable authentication:

```
# Uncomment these lines:
password_file /mosquitto/config/auth/passwd
allow_anonymous false
```

### 5. Start the Services

Launch the SwissAirDry stack:

```bash
docker-compose up -d
```

### 6. Verify Installation

Check that all services are running:

```bash
docker-compose ps
```

Access the API server at http://your-server-ip:5000 to verify it's working.

## Component Configuration

### API Server

The API server provides the core functionality and serves as the central hub for all components. It's configured through environment variables in the `.env` file.

Key settings:
- `API_PORT`: The port on which the API server listens (default: 5000)
- `API_HOST`: The host address to bind to (default: 0.0.0.0)
- `DATABASE_URL`: Connection string for the PostgreSQL database

### MQTT Broker

The MQTT broker handles real-time communication with IoT devices. Configuration is stored in `swissairdry/mqtt/mosquitto.conf`.

Key settings:
- `MQTT_PORT`: The port for MQTT communication (default: 1883)
- `MQTT_WS_PORT`: WebSocket port for browser clients (default: 9001)

### Database

PostgreSQL stores all persistent data. The database is automatically initialized during first startup.

Key settings:
- `POSTGRES_USER`: Database username (default: swissairdry)
- `POSTGRES_PASSWORD`: Database password (IMPORTANT: change this!)
- `POSTGRES_DB`: Database name (default: swissairdry)

## Nextcloud Integration

To integrate with Nextcloud, you need to install the SwissAirDry app in your Nextcloud instance.

1. Copy the `swissairdry/nextcloud/app` directory to your Nextcloud apps directory
2. Enable the app in Nextcloud settings
3. Configure the connection to your SwissAirDry API server

## Backup and Maintenance

### Database Backup

To backup the PostgreSQL database:

```bash
docker-compose exec postgres pg_dump -U swissairdry swissairdry > backup.sql
```

### Logs

View logs for troubleshooting:

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs api
docker-compose logs mqtt
docker-compose logs postgres
```

## Troubleshooting

### Connection Issues

If devices cannot connect to the MQTT broker:
- Check that the MQTT port (1883) is open in your firewall
- Verify that the MQTT broker is running (`docker-compose ps`)
- Check the MQTT logs for authentication errors

### Database Problems

If the API server cannot connect to the database:
- Ensure the PostgreSQL container is running
- Check the database credentials in `.env`
- Verify the database connection in the API server logs

### Web Interface Unavailable

If the web interface is not accessible:
- Check that the API server is running
- Verify the API port (5000) is open in your firewall
- Check the API server logs for startup errors

## Updating

To update the SwissAirDry system:

```bash
git pull
docker-compose down
docker-compose pull
docker-compose up -d
```

---

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