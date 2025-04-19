# SwissAirDry Fehlerbehebungsanleitung

Diese Anleitung enthält Lösungsansätze für häufige Probleme bei der Installation und Nutzung des SwissAirDry Stacks.

## Inhaltsverzeichnis

1. [Allgemeine Docker-Probleme](#allgemeine-docker-probleme)
2. [MQTT-Probleme](#mqtt-probleme)
3. [API-Server-Probleme](#api-server-probleme)
4. [Datenbank-Probleme](#datenbank-probleme)
5. [Nextcloud-Integration](#nextcloud-integration)
6. [ESP-Geräte-Verbindungsprobleme](#esp-geräte-verbindungsprobleme)
7. [SSL-Zertifikat-Probleme](#ssl-zertifikat-probleme)
8. [Netzwerkprobleme](#netzwerkprobleme)

## Allgemeine Docker-Probleme

### Container starten nicht

**Problem:** Die Docker-Container starten nicht oder stürzen sofort nach dem Start ab.

**Lösung:**
1. Überprüfen Sie die Docker-Logs:
   ```bash
   docker compose logs
   ```

2. Stellen Sie sicher, dass die erforderlichen Ports nicht bereits belegt sind:
   ```bash
   sudo lsof -i :5000
   sudo lsof -i :1883
   ```

3. Docker-Dienst neu starten:
   ```bash
   sudo systemctl restart docker
   ```

4. Vergewissern Sie sich, dass Sie über ausreichend Festplattenplatz verfügen:
   ```bash
   df -h
   ```

### Berechtigungsprobleme

**Problem:** Fehler wie "permission denied" in den Docker-Logs.

**Lösung:**
1. Überprüfen Sie die Eigentümerschaft der Volume-Verzeichnisse:
   ```bash
   sudo chown -R 1000:1000 ./swissairdry/mqtt
   sudo chown -R 999:999 ./swissairdry/db
   ```

2. Stellen Sie sicher, dass die SSL-Zertifikatdateien die richtigen Berechtigungen haben:
   ```bash
   sudo chmod 644 ./ssl/certs/vgnc.org.cert.pem
   sudo chmod 600 ./ssl/private/vgnc.org.key.pem
   ```

## MQTT-Probleme

### MQTT-Verbindung fehlgeschlagen

**Problem:** ESP-Geräte oder API-Server können keine Verbindung zum MQTT-Broker herstellen.

**Lösung:**
1. Überprüfen Sie, ob der MQTT-Broker läuft:
   ```bash
   docker ps | grep mqtt
   ```

2. Überprüfen Sie die MQTT-Logs:
   ```bash
   docker logs swissairdry-mqtt
   ```

3. Überprüfen Sie die mosquitto.conf auf Fehler:
   ```bash
   docker exec -it swissairdry-mqtt cat /mosquitto/config/mosquitto.conf
   ```

4. Stellen Sie sicher, dass der MQTT-Port (1883) erreichbar ist:
   ```bash
   netstat -tuln | grep 1883
   ```

5. Für anonyme Verbindungen in der Entwicklungsumgebung sollte die mosquitto.conf folgende Zeile enthalten:
   ```
   allow_anonymous true
   ```

### MQTT-Authentifizierung

**Problem:** MQTT meldet Authentifizierungsfehler.

**Lösung:**
1. Überprüfen Sie die MQTT-Benutzeranmeldedaten in der .env-Datei.
   
2. Falls Sie die Authentifizierung aktiviert haben, stellen Sie sicher, dass Sie die Passwortdatei erstellt haben:
   ```bash
   docker exec -it swissairdry-mqtt mosquitto_passwd -c /mosquitto/config/mosquitto.passwd <username>
   ```

3. Achten Sie darauf, dass die Verbindungen der Client-Geräte die richtigen Anmeldeinformationen verwenden.

## API-Server-Probleme

### API-Server startet nicht

**Problem:** Der API-Server startet nicht oder bricht mit Fehlern ab.

**Lösung:**
1. Überprüfen Sie die API-Server-Logs:
   ```bash
   docker logs swissairdry-api
   ```

2. Testen Sie, ob die Datenbank erreichbar ist:
   ```bash
   docker exec -it swissairdry-api ping db
   ```

3. Überprüfen Sie die Umgebungsvariablen:
   ```bash
   docker exec -it swissairdry-api env | grep DATABASE_URL
   ```

4. Starten Sie den Container mit aktiviertem Debug-Modus:
   ```bash
   # .env-Datei bearbeiten
   DEBUG=True
   # Container neu starten
   docker compose restart api
   ```

## Datenbank-Probleme

### Datenbank-Verbindungsfehler

**Problem:** Die Anwendung zeigt Datenbank-Verbindungsfehler an.

**Lösung:**
1. Überprüfen Sie, ob der Datenbankcontainer läuft:
   ```bash
   docker ps | grep db
   ```

2. Überprüfen Sie die Datenbankverbindungszeichenfolge in der .env-Datei.

3. Stellen Sie sicher, dass die Datenbank initialisiert wurde:
   ```bash
   docker logs swissairdry-db
   ```

4. Testen Sie die Datenbankverbindung direkt:
   ```bash
   docker exec -it swissairdry-db psql -U swissairdry -d swissairdry -c "SELECT 1;"
   ```

### Datenbank-Migrationen

**Problem:** Schemasynchronisation oder Migrationsfehler.

**Lösung:**
1. Führen Sie die Migrations-Skripte im API-Container aus:
   ```bash
   docker exec -it swissairdry-api python -m swissairdry.db.migrate
   ```

2. Bei schwerwiegenden Problemen können Sie die Datenbank zurücksetzen (ACHTUNG: Datenverlust!):
   ```bash
   docker compose down
   sudo rm -rf ./postgres-data
   docker compose up -d
   ```

## Nextcloud-Integration

### Nextcloud ExApp-Verbindungsfehler

**Problem:** Die Nextcloud ExApp kann nicht mit der API kommunizieren.

**Lösung:**
1. Überprüfen Sie die ExApp-Logs:
   ```bash
   docker logs swissairdry-exapp
   ```

2. Stellen Sie sicher, dass die API-URL in der .env-Datei korrekt ist:
   ```
   API_URL=http://api:5000
   ```

3. Überprüfen Sie die Netzwerkverbindung zwischen den Containern:
   ```bash
   docker exec -it swissairdry-exapp ping api
   ```

## ESP-Geräte-Verbindungsprobleme

### ESP-Gerät verbindet sich nicht mit dem MQTT-Broker

**Problem:** ESP-Geräte können keine Verbindung zum MQTT-Broker herstellen.

**Lösung:**
1. Prüfen Sie, ob die richtige MQTT-Server-Adresse in der ESP-Konfiguration angegeben ist.

2. Stellen Sie sicher, dass das ESP-Gerät WLAN-Verbindung hat.

3. Überprüfen Sie, ob Sie eine statische IP im lokalen Netzwerk mit korrektem Gateway-Zugang verwenden.

4. Aktivieren Sie Debug-Ausgaben in der ESP-Firmware, falls möglich.

5. Überprüfen Sie, ob der MQTT-Broker anonyme Verbindungen zulässt (für einfache Setups).

### ESP-Gerät aktualisiert keine Sensordaten

**Problem:** ESP-Geräte verbinden sich, senden aber keine Daten.

**Lösung:**
1. Überprüfen Sie, ob die Topic-Konfiguration korrekt ist.

2. Stellen Sie sicher, dass die Sensoren korrekt angeschlossen sind.

3. Überwachen Sie die MQTT-Themen mit einem MQTT-Client:
   ```bash
   docker exec -it swissairdry-mqtt mosquitto_sub -t 'swissairdry/#' -v
   ```

## SSL-Zertifikat-Probleme

### Nginx meldet Zertifikatsfehler

**Problem:** Nginx startet nicht oder meldet Fehler bezüglich SSL-Zertifikaten.

**Lösung:**
1. Überprüfen Sie, ob die Zertifikatsdateien vorhanden sind:
   ```bash
   ls -la ./ssl/certs/
   ls -la ./ssl/private/
   ```

2. Stellen Sie sicher, dass die Zertifikatsdateien die richtigen Berechtigungen haben:
   ```bash
   sudo chmod 644 ./ssl/certs/vgnc.org.cert.pem
   sudo chmod 600 ./ssl/private/vgnc.org.key.pem
   ```

3. Überprüfen Sie die Gültigkeit des Zertifikats:
   ```bash
   openssl x509 -in ./ssl/certs/vgnc.org.cert.pem -text -noout
   ```

## Netzwerkprobleme

### Ports sind nicht erreichbar

**Problem:** Dienste sind innerhalb des Docker-Netzwerks erreichbar, aber nicht von außen.

**Lösung:**
1. Überprüfen Sie, ob die Ports in der docker-compose.yml korrekt abgebildet werden.

2. Überprüfen Sie die Firewall-Einstellungen:
   ```bash
   sudo ufw status
   ```

3. Stellen Sie sicher, dass der Server die Ports nach außen freigibt:
   ```bash
   # Ports öffnen
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw allow 1883/tcp
   sudo ufw allow 5000/tcp
   sudo ufw allow 5001/tcp
   ```

### Interne Container-Netzwerkprobleme

**Problem:** Container können nicht miteinander kommunizieren.

**Lösung:**
1. Überprüfen Sie, ob alle Container im selben Netzwerk sind:
   ```bash
   docker network inspect swissairdry-net
   ```

2. Testen Sie die Kommunikation zwischen den Containern:
   ```bash
   docker exec -it swissairdry-api ping mqtt
   docker exec -it swissairdry-api ping db
   ```

3. Stellen Sie sicher, dass die Container-Namen in den Verbindungszeichenfolgen verwendet werden und nicht "localhost".

---

Wenn Sie weiterhin Probleme haben, überprüfen Sie bitte die [GitHub Issues](https://github.com/SwissAirDry/swissairdry/issues) für bekannte Probleme oder erstellen Sie ein neues Issue mit einer detaillierten Beschreibung Ihres Problems.