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

## Kontakt

Bei technischen Problemen wenden Sie sich an:
- E-Mail: tech@vgnc.org