# SwissAirDry Installation

Diese Datei enthält detaillierte Installationsanweisungen für das SwissAirDry-System.

## Systemanforderungen

- Docker und Docker Compose
- Python 3.8 oder höher
- MQTT-Broker (Mosquitto)
- PostgreSQL Datenbank
- Nextcloud-Installation (optional für ExApp-Funktionalität)

## Installation der Entwicklungsumgebung

### 1. Repository klonen

```bash
git clone https://github.com/yourusername/swissairdry.git
cd swissairdry
```

### 2. Python-Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### 3. Minimalen HTTP-Server starten

```bash
cd swissairdry/api
python minimal_http_server.py
```

### 4. MQTT-Broker starten

```bash
mkdir -p /tmp/mosquitto/data /tmp/mosquitto/log
chmod -R 777 /tmp/mosquitto
mosquitto -c swissairdry/mqtt/mosquitto.conf
```

## Docker-Installation für Produktion

Für Produktionsumgebungen wird die Verwendung von Docker empfohlen.

### Netzwerkkonfigurationen

Stellen Sie sicher, dass folgende Netzwerkkonfigurationen korrekt eingerichtet sind:

#### 1. Portweiterleitungen (Router/Firewall)

| Port | Dienst | Beschreibung |
|------|--------|--------------|
| 80 | HTTP | Web-Zugriff |
| 443 | HTTPS | Sicherer Web-Zugriff |
| 8080 | Nextcloud | Nextcloud Weboberfläche |
| 3000 | ExApp Frontend | SwissAirDry ExApp |
| 5000 | SwissAirDry API | Hauptschnittstelle |
| 5001 | Simple API | Vereinfachte API |
| 8701 | ExApp Daemon | Synchronisationsdienst |
| 1883 | MQTT Broker | IoT-Kommunikation |
| 9001 | MQTT WebSocket | Browser-MQTT-Zugriff |
| 5432 | PostgreSQL | Datenbank |

#### 2. Docker Compose Netzwerke

Docker Compose erstellt folgende Netzwerke:
- **frontend**: Für Webzugriffe (Nextcloud, ExApp-Frontend, Reverse Proxy)
- **backend**: Für interne Kommunikation (API, Datenbank, Daemon)
- **mqtt-net**: Für MQTT-Kommunikation (Broker, API, Daemon)

#### 3. Firewall-Regeln (Beispiel für UFW)

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8080/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 5000/tcp
sudo ufw allow 5001/tcp
sudo ufw allow 8701/tcp
sudo ufw allow 1883/tcp
sudo ufw allow 9001/tcp
sudo ufw allow 5432/tcp
```

#### 4. Cloudflare-Konfiguration (falls verwendet)

- DNS-Einträge für alle relevanten Subdomains (z.B. cloud.domain.tld, api.domain.tld)
- Proxy-Status für Zertifikats- und API-Zugriffe ggf. deaktivieren (orange/gray cloud)
- SSL/TLS auf "Full" oder "Full (strict)" stellen, je nach Zertifikatslage

### 1. Vorbereitung der Docker-Umgebung

Prüfen Sie, ob Docker und Docker Compose installiert sind:
```bash
docker --version
docker-compose --version
```

### 2. Konfiguration anpassen

Passen Sie die Umgebungsvariablen an:
```bash
cp .env.example .env
nano .env  # Konfiguration anpassen
```

### 3. System starten mit Docker Compose

Das gesamte System mit allen Komponenten starten:
```bash
cd docker
docker-compose up -d
```

### 4. Einzelne Container starten

Bei Bedarf können auch einzelne Komponenten gestartet werden:
```bash
# Nur API starten
docker-compose up -d swissairdry-api

# Nur MQTT-Broker starten
docker-compose up -d swissairdry-mqtt
```

### 5. Container-Status überprüfen

```bash
docker-compose ps
# Oder detaillierter
docker ps -a
```

### 6. Docker-Logs einsehen

```bash
# Logs aller Container
docker-compose logs

# Logs eines bestimmten Containers
docker-compose logs swissairdry-api
```

### 7. Build-Prozess

Bei Änderungen am Code oder an den Dockerfiles:
```bash
# Container neu bauen
docker-compose build

# Bestimmten Container neu bauen
docker-compose build swissairdry-api
```

## Hinweise zu MQTT

**Wichtig:** Das SwissAirDry-System verwendet ausschließlich Python (paho-mqtt) für die MQTT-Kommunikation. Die PHP-MQTT-Extension (Mosquitto-0.4.0) wird nicht mehr verwendet, da sie mit aktuellen PHP-Versionen nicht kompatibel ist.

### MQTT-Kommunikation über Python

Die Kommunikation mit IoT-Geräten erfolgt über folgende Komponenten:

1. **Python-MQTT-Implementierung:**
   - Hauptklasse: `swissairdry/api/mqtt_client.py` (MQTTClient-Klasse)
   - Diese Klasse nutzt die paho-mqtt Bibliothek und bietet robuste Fehlerbehandlung
   - Unterstützt alle neueren Python-Versionen (3.8+)

2. **Installation der benötigten Bibliotheken:**
   ```bash
   pip install paho-mqtt
   ```

3. **Konfiguration:**
   - MQTT-Broker: `swissairdry/mqtt/mosquitto.conf`
   - Default-Ports: 1883 (MQTT), 9001 (MQTT WebSocket)
   - Konfigurationsparameter können über Umgebungsvariablen gesetzt werden

4. **Beispiel für die Verwendung:**
   ```python
   from swissairdry.api.mqtt_client import MQTTClient
   import asyncio
   
   async def main():
       # Client initialisieren
       client = MQTTClient(host="localhost", port=1883)
       
       # Verbindung herstellen
       connected = await client.connect()
       if not connected:
           print("Verbindung fehlgeschlagen")
           return
       
       # Message-Handler hinzufügen
       def on_message(topic, payload):
           print(f"Nachricht erhalten: {topic} - {payload}")
       
       client.add_message_callback("swissairdry/#", on_message)
       
       # Thema abonnieren
       await client.subscribe("swissairdry/+/status")
       
       # Nachricht senden
       await client.publish("swissairdry/control", {"command": "status"})
       
       # Kurz warten auf Nachrichten
       await asyncio.sleep(10)
       
       # Verbindung trennen
       await client.disconnect()
   
   asyncio.run(main())
   ```

5. **Debugging von MQTT-Verbindungen:**
   ```bash
   # MQTT-Nachrichten überwachen
   mosquitto_sub -h localhost -p 1883 -t "swissairdry/#" -v
   
   # MQTT-Testnachricht senden
   mosquitto_pub -h localhost -p 1883 -t "swissairdry/test" -m '{"status":"test"}'
   ```

### Entfernung der PHP-MQTT-Extension

Die PHP-MQTT-Extension (Mosquitto-0.4.0) wurde aus folgenden Gründen entfernt:

1. **Kompatibilitätsprobleme:** Die Extension ist nicht mit PHP 8.x kompatibel (Fehler: "expected ')' before 'TSRMLS_CC'").
2. **Keine aktive Wartung:** Die Extension wird nicht mehr aktiv gepflegt.
3. **Ersatz durch PHP-Alternative:** In den wenigen Fällen, wo PHP-MQTT-Kommunikation benötigt wird, nutzen wir jetzt HTTP-Requests zur API, die dann über Python mit MQTT kommuniziert.

Alle Dockerfiles wurden entsprechend angepasst, insbesondere:
- In `swissairdry/nextcloud/Dockerfile.appapi` wurden folgende Zeilen entfernt:
  - `libmosquitto-dev` aus der Paketinstallation
  - `pecl install Mosquitto-0.4.0`
  - `docker-php-ext-enable mosquitto`

## ExApp-Daemon

Der ExApp-Daemon ist verantwortlich für die Synchronisation zwischen der SwissAirDry API und der Nextcloud ExApp.

### Übersicht und Funktionen

Der ExApp-Daemon bietet folgende Funktionen:
- Überwachung der Verbindung zwischen API und Nextcloud ExApp
- Synchronisierung von Daten zwischen den Komponenten
- Verarbeitung von Benachrichtigungen
- Monitoring und Health-Checks

### Technische Details

- **Hauptskript:** `swissairdry/api/app/exapp_daemon.py`
- **Log-Datei:** `/app/logs/exapp_daemon.log` (im Container)
- **Ausführung:** Läuft als eigenständiger Prozess im Docker-Container
- **Port:** 8701 (für Health-Check-Endpunkt)

### Konfiguration über Umgebungsvariablen

Der ExApp-Daemon kann über folgende Umgebungsvariablen konfiguriert werden:

| Variable | Beschreibung | Standardwert |
|----------|--------------|--------------|
| NEXTCLOUD_URL | URL der Nextcloud-Instanz | https://localhost |
| API_URL | URL der SwissAirDry API | http://localhost:5000 |
| EXAPP_URL | URL der ExApp | https://exapp.localhost |
| SYNC_INTERVAL | Synchronisationsintervall in Sekunden | 300 |

### Installation und Start

Um den ExApp-Daemon zu starten:

1. **In der Entwicklungsumgebung:**
   ```bash
   cd swissairdry/api/app
   python exapp_daemon.py
   ```

2. **Mit Docker (empfohlen für Produktion):**
   ```bash
   # Wird automatisch über Docker Compose gestartet
   cd docker
   docker-compose up -d exapp-daemon
   ```

### Fehlerbehebung für den ExApp-Daemon

1. **Prüfen, ob der Daemon läuft:**
   ```bash
   docker ps | grep exapp-daemon
   # oder im Container
   docker logs swissairdry-exapp-daemon
   ```

2. **Health-Check ausführen:**
   ```bash
   curl http://localhost:8701/health
   ```

3. **Verbindungsprobleme zwischen API und Nextcloud:**
   - Überprüfen Sie die Umgebungsvariablen im Container
   - Prüfen Sie die Nextcloud-Erreichbarkeit
   - Prüfen Sie die Log-Dateien

## Fehlerbehebung

### MQTT-Verbindungsprobleme

1. Prüfen Sie, ob der MQTT-Broker läuft:
   ```bash
   netstat -tuln | grep 1883
   ```

2. Überprüfen Sie die Firewall-Einstellungen:
   ```bash
   sudo ufw status
   ```

### Skript für automatisierte Installation

Für eine vollständig automatisierte Installation können folgende Schritte in ein Bash-Skript integriert werden:

```bash
#!/bin/bash
# SwissAirDry Installationsskript

echo "SwissAirDry Installation beginnt..."

# Prüfe Systemvoraussetzungen
command -v docker >/dev/null 2>&1 || { echo "Docker ist nicht installiert. Bitte zuerst Docker installieren."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "Docker Compose ist nicht installiert. Bitte zuerst Docker Compose installieren."; exit 1; }

# Netzwerkkonfiguration prüfen
echo "Prüfe Netzwerkkonfiguration..."
ports=(80 443 8080 3000 5000 5001 8701 1883 9001 5432)
for port in "${ports[@]}"; do
    nc -z localhost $port >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "WARNUNG: Port $port ist bereits belegt. Dies könnte zu Konflikten führen."
    fi
done

# Firewall-Regeln (bei Bedarf)
if command -v ufw >/dev/null 2>&1; then
    echo "UFW-Firewall gefunden. Konfiguriere Ports..."
    for port in "${ports[@]}"; do
        sudo ufw allow $port/tcp
    done
    echo "Firewall-Regeln hinzugefügt."
fi

# Projekt-Setup
echo "Erstelle notwendige Ordner und Konfigurationsdateien..."
mkdir -p data/db data/mqtt/data data/mqtt/log

# Konfiguration kopieren
if [ -f .env.example ] && [ ! -f .env ]; then
    cp .env.example .env
    echo ".env-Datei aus Vorlage erstellt. Bitte passen Sie diese an Ihre Umgebung an."
fi

# Docker-Netzwerke erstellen
echo "Erstelle Docker-Netzwerke..."
docker network create frontend 2>/dev/null || true
docker network create backend 2>/dev/null || true
docker network create mqtt-net 2>/dev/null || true

# Starte die Services
echo "Starte Docker-Container..."
cd docker
docker-compose up -d

echo "Installation abgeschlossen. Prüfe Status mit 'docker-compose ps'"
```

Dieses Skript ist ein Beispiel und sollte an die spezifischen Anforderungen der Installation angepasst werden.

### Docker-Build-Fehler mit PHP-MQTT-Extension

**Problem:** Wenn beim Docker-Build Fehler im Zusammenhang mit der PHP-MQTT-Extension auftreten, können folgende Fehlermeldungen erscheinen:

```
pecl install Mosquitto-0.4.0
Compiling ...
Error: expected ')' before 'TSRMLS_CC'
...
```

**Lösung:**

1. **Überprüfen Sie alle Dockerfile-Dateien:**
   Stellen Sie sicher, dass in allen Dockerfiles die folgenden Zeilen entfernt wurden:
   - ~~`libmosquitto-dev` aus der Paketinstallation~~
   - ~~`pecl install Mosquitto-0.4.0`~~
   - ~~`docker-php-ext-enable mosquitto`~~

2. **Wichtige Dateien zu prüfen:**
   - `swissairdry/nextcloud/Dockerfile.appapi`
   - `swissairdry/nextcloud/Dockerfile.exapp`
   - `swissairdry/nextcloud/Dockerfile`

3. **Bei weiterhin auftretenden Fehlern:**
   - Prüfen Sie externes Base-Image (z.B. `FROM php:8.1-apache`)
   - Entfernen Sie den Docker-Build-Cache: `docker-compose build --no-cache`
   - Überprüfen Sie entfernte Docker-Volumes mit möglicherweise gecachten Konfigurationen

4. **Manueller Test:**
   Sie können einen manuellen Test durchführen, um sicherzustellen, dass kein Base-Image die PHP-MQTT-Extension installiert:
   ```bash
   docker run --rm php:8.1-apache bash -c "command -v pecl && pecl list | grep -i mosq"
   # Sollte keine Ausgabe liefern
   ```

5. **Alternatives PHP-Image:**
   Falls das Problem weiterhin besteht, können Sie ein alternatives PHP-Image verwenden:
   ```
   # In Dockerfile.appapi ändern
   FROM php:8.1-apache
   # zu
   FROM php:8.1-apache-bullseye
   ```

## Systemwartung und Betrieb

### Backup und Wiederherstellung

#### 1. Datenbank-Backup

```bash
# Backup der PostgreSQL-Datenbank
docker exec -t swissairdry-db pg_dump -U swissairdry swissairdry > backup_$(date +%Y%m%d).sql

# Wiederherstellen des Backups
cat backup_20230101.sql | docker exec -i swissairdry-db psql -U swissairdry -d swissairdry
```

#### 2. Konfigurationsbackup

```bash
# Sichern aller Konfigurationsdateien
mkdir -p backups/config
cp .env backups/config/
cp -r swissairdry/mqtt/mosquitto.conf backups/config/
# Weitere wichtige Konfigurationen...
```

#### 3. Daten-Backup

```bash
# Sichern der Datenverzeichnisse
mkdir -p backups/data
cp -r data/mqtt backups/data/
# Weitere Datenverzeichnisse...
```

### Update und Upgrades

#### 1. System aktualisieren

```bash
# Neueste Images holen
docker-compose pull

# Container neustarten mit neuen Images
docker-compose up -d

# Bei Änderungen an den Dockerfiles
docker-compose build --no-cache
docker-compose up -d
```

#### 2. Datenbank-Migration

Nach Updates der Anwendung können Datenbankmigrationen erforderlich sein:

```bash
# Datenbankmigrationen durchführen
docker exec -t swissairdry-api python migrate.py
```

### Sicherheitshinweise

#### 1. Passwörter ändern

- Ändern Sie nach der Installation alle Standard-Passwörter
- Verwenden Sie starke, eindeutige Passwörter für:
  - Datenbank
  - MQTT-Broker
  - Nextcloud-Admin
  - API-Zugriffe

#### 2. SSL/TLS-Konfiguration

```bash
# Let's Encrypt mit Certbot (Beispiel)
docker run -it --rm --name certbot \
  -v "./certs:/etc/letsencrypt" \
  -v "./certs-data:/var/lib/letsencrypt" \
  certbot/certbot certonly --standalone \
  -d swissairdry.example.com
```

#### 3. Sichern der MQTT-Kommunikation

- Konfigurieren Sie TLS für den MQTT-Broker
- Setzen Sie Benutzername/Passwort für MQTT-Zugriffe
- Beschränken Sie die Zugriffe auf bestimmte Themen

## Troubleshooting

### Häufige Probleme und Lösungen

#### 1. Container starten nicht

```bash
# Logs ansehen
docker-compose logs

# Prüfen, ob alle erforderlichen Dienste laufen
docker-compose ps
```

#### 2. Datenbank-Verbindungsprobleme

- Prüfen Sie die Datenbank-Umgebungsvariablen in der .env-Datei
- Stellen Sie sicher, dass der PostgreSQL-Container läuft
- Prüfen Sie die Netzwerkverbindung zwischen den Containern

```bash
# Direkter Test der Datenbankverbindung
docker exec -it swissairdry-db psql -U swissairdry -d swissairdry -c "SELECT 1"
```

#### 3. MQTT-Verbindungsprobleme

- Prüfen Sie die MQTT-Broker-Konfiguration
- Stellen Sie sicher, dass die erforderlichen Ports offen sind
- Überprüfen Sie die Client-Konfiguration

```bash
# MQTT-Verbindungstest
mosquitto_sub -h localhost -p 1883 -t "swissairdry/test" -v
```

#### 4. Netzwerkfehler

- Überprüfen Sie die Docker-Netzwerke
- Stellen Sie sicher, dass die Container im richtigen Netzwerk sind
- Prüfen Sie die Hostnamen-Auflösung

```bash
# Netzwerke anzeigen
docker network ls

# Container in einem Netzwerk anzeigen
docker network inspect frontend
```

### Log-Dateien

#### 1. Container-Logs

```bash
# Logs eines bestimmten Containers anzeigen
docker logs swissairdry-api
docker logs swissairdry-mqtt
```

#### 2. Anwendungs-Logs

- API-Logs: `/app/logs/api.log` im API-Container
- MQTT-Logs: `/mosquitto/log` im MQTT-Container
- ExApp-Daemon-Logs: `/app/logs/exapp_daemon.log` im ExApp-Daemon-Container

#### 3. Fehlersuche mit erweiterten Logs

```bash
# Aktivieren erweiterter Logs
docker-compose stop swissairdry-api
docker-compose run -e DEBUG=1 swissairdry-api
```

### Systemd-Integration (optional)

Für automatischen Start bei Systemstart:

```ini
# /etc/systemd/system/swissairdry.service
[Unit]
Description=SwissAirDry Docker Compose Services
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/pfad/zu/swissairdry
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down

[Install]
WantedBy=multi-user.target
```

Aktivieren des Dienstes:

```bash
sudo systemctl enable swissairdry.service
sudo systemctl start swissairdry.service
```

## Kontakt

Bei technischen Problemen wenden Sie sich an:
- E-Mail: tech@vgnc.org