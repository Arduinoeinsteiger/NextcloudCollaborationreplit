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

### 1. Docker Compose verwenden

```bash
cd docker
docker-compose up -d
```

## Hinweise zu MQTT

**Wichtig:** Das SwissAirDry-System verwendet ausschließlich Python (paho-mqtt) für die MQTT-Kommunikation. Die PHP-MQTT-Extension (Mosquitto-0.4.0) wird nicht mehr verwendet, da sie mit aktuellen PHP-Versionen nicht kompatibel ist.

- Die Python-MQTT-Implementierung finden Sie in `swissairdry/api/mqtt_client.py`
- MQTT-Broker-Konfiguration: `swissairdry/mqtt/mosquitto.conf`
- Ports: 1883 (MQTT), 9001 (MQTT WebSocket)

## ExApp-Daemon

Der ExApp-Daemon ist verantwortlich für die Synchronisation zwischen der SwissAirDry API und der Nextcloud ExApp.

- Daemon-Code: `swissairdry/api/app/exapp_daemon.py`
- Logs: `/app/logs/exapp_daemon.log` (im Container)

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

### Docker-Build-Fehler

Wenn beim Docker-Build Fehler im Zusammenhang mit der PHP-MQTT-Extension auftreten, stellen Sie sicher, dass in allen Dockerfiles die entsprechenden Zeilen entfernt wurden:

- ~~`libmosquitto-dev` aus der Paketinstallation~~
- ~~`pecl install Mosquitto-0.4.0`~~
- ~~`docker-php-ext-enable mosquitto`~~

## Kontakt

Bei technischen Problemen wenden Sie sich an:
- E-Mail: tech@vgnc.org