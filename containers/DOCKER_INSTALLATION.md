# SwissAirDry Docker-Installation und Konfiguration

Diese Anleitung beschreibt die Installation und Konfiguration von SwissAirDry mit Docker Desktop.

## Voraussetzungen

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installiert und konfiguriert
- Mindestens 4 GB RAM für Docker reserviert
- 10 GB freier Festplattenspeicher

## Schnellstart

1. Öffne ein Terminal/Kommandozeile
2. Navigiere zum SwissAirDry/containers Verzeichnis
3. Führe `./start.sh` aus (oder unter Windows: `docker-compose up -d`)
4. Öffne im Browser: http://localhost:8080 für Nextcloud und http://localhost:5000 für die API

## Detaillierte Installationsanleitung

### 1. Docker Desktop starten

Stelle sicher, dass Docker Desktop läuft und ausreichend Ressourcen zugewiesen sind.

### 2. Umgebungsvariablen konfigurieren (optional)

Die Standardkonfiguration ist für die meisten Anwendungsfälle ausreichend. Für benutzerdefinierte Einstellungen:

1. Öffne die Datei `.env` im Container-Verzeichnis
2. Passe die Werte an deine Anforderungen an
3. Speichere die Datei

### 3. Container starten

Führe einen der folgenden Befehle aus:

```bash
# Mit dem Startskript (empfohlen)
./start.sh

# Oder direkt mit Docker Compose
docker-compose up -d
```

Die Container werden heruntergeladen, erstellt und gestartet.

### 4. Überprüfen der Installation

Nach dem Start sind folgende Dienste verfügbar:

| Dienst | URL | Beschreibung |
|--------|-----|-------------|
| Nextcloud | http://localhost:8080 | Cloud-Speicher und Kollaboration |
| SwissAirDry API | http://localhost:5000 | Hauptschnittstelle |
| SwissAirDry API Docs | http://localhost:5000/docs | API-Dokumentation |
| Simple API | http://localhost:5001 | Vereinfachte API für Geräte |
| MQTT Broker | localhost:1883 | MQTT-Verbindungen |
| MQTT WebSockets | localhost:9001 | MQTT über WebSockets |

### 5. Nextcloud einrichten

Beim ersten Zugriff auf Nextcloud:

1. Melde dich mit dem Admin-Konto an (Zugangsdaten aus der `.env`-Datei)
2. Installiere die SwissAirDry ExApp aus dem App Store
3. Konfiguriere den Speicherort und weitere Einstellungen

## Container-Verwaltung

### Container anzeigen

```bash
docker-compose ps
```

### Container-Logs anzeigen

```bash
# Alle Logs
docker-compose logs

# Logs eines bestimmten Dienstes
docker-compose logs swissairdry-api

# Logs kontinuierlich anzeigen (-f)
docker-compose logs -f
```

### Container stoppen

```bash
# Mit dem Stopskript (empfohlen)
./stop.sh

# Oder direkt mit Docker Compose
docker-compose down
```

### Container zurücksetzen (alle Daten löschen!)

```bash
# Mit dem Resetskript (empfohlen)
./reset.sh

# Oder direkt mit Docker Compose
docker-compose down -v
```

## Update auf neue Version

```bash
# Aktualisiere das Repository (wenn aus Git geklont)
git pull

# Stoppe die Container
./stop.sh

# Starte die Container neu mit aktualisiertem Image
./start.sh
```

## Fehlerbehebung

### Container starten nicht

Überprüfe Docker-Logs:

```bash
docker-compose logs
```

### Nextcloud-Verbindungsprobleme

1. Stelle sicher, dass der Container läuft: `docker-compose ps`
2. Prüfe die Nextcloud-Logs: `docker-compose logs nextcloud`
3. Überprüfe die Konfiguration in der `.env`-Datei

### MQTT-Verbindungsprobleme

1. Teste die MQTT-Verbindung mit einem MQTT-Client
2. Überprüfe die Mosquitto-Konfiguration in `mqtt/config/mosquitto.conf`
3. Prüfe die Firewall-Einstellungen

## Erweiterte Konfiguration

### SSL-Zertifikate hinzufügen

1. Lege deine Zertifikate im Verzeichnis `nginx/ssl/` ab:
   - `cert.pem` - Dein Zertifikat
   - `key.pem` - Dein privater Schlüssel
2. Aktualisiere die Nginx-Konfiguration in `nginx/conf/default.conf`, um SSL zu aktivieren
3. Starte die Container neu: `./stop.sh && ./start.sh`

### Persönliche Domain verwenden

1. Aktualisiere den DOMAIN-Wert in der `.env`-Datei
2. Aktualisiere die Nginx-Konfiguration in `nginx/conf/default.conf`
3. Starte die Container neu

### MQTT-Authentifizierung aktivieren

1. Erstelle eine Passwortdatei: `mosquitto_passwd -c mqtt/config/passwd username`
2. Aktualisiere die Mosquitto-Konfiguration
3. Setze `allow_anonymous` auf `false`
4. Starte die Container neu