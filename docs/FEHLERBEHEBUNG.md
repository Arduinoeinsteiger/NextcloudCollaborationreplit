# SwissAirDry Fehlerbehebung

Dieses Dokument enthält Lösungen für häufige Probleme, die bei der Installation und Verwendung des SwissAirDry-Systems auftreten können.

## Allgemeine Probleme

### Docker-Container starten nicht

**Problem**: Die Docker-Container starten nicht oder beenden sich sofort wieder.

**Lösungen**:
1. Überprüfen Sie die Docker-Logs:
   ```bash
   docker-compose logs
   ```

2. Stellen Sie sicher, dass alle benötigten Ports verfügbar sind:
   ```bash
   sudo lsof -i :5000
   sudo lsof -i :1883
   sudo lsof -i :9001
   sudo lsof -i :5432
   ```

3. Überprüfen Sie, ob die benötigten Verzeichnisse existieren und die richtigen Berechtigungen haben:
   ```bash
   mkdir -p swissairdry/mqtt/auth
   chmod -R 777 swissairdry/mqtt
   ```

4. Prüfen Sie die `.env`-Datei auf fehlende oder falsche Werte.

### Datenbank-Verbindungsprobleme

**Problem**: Der API-Server kann keine Verbindung zur Datenbank herstellen.

**Lösungen**:
1. Überprüfen Sie, ob der PostgreSQL-Container läuft:
   ```bash
   docker-compose ps postgres
   ```

2. Prüfen Sie die Datenbank-Anmeldedaten in der `.env`-Datei.

3. Versuchen Sie, sich manuell mit der Datenbank zu verbinden:
   ```bash
   docker-compose exec postgres psql -U swissairdry -d swissairdry
   ```

4. Überprüfen Sie die Logs des PostgreSQL-Containers:
   ```bash
   docker-compose logs postgres
   ```

5. Stellen Sie sicher, dass die `DATABASE_URL` korrekt ist und dem Format entspricht:
   ```
   postgresql://swissairdry:password@postgres:5432/swissairdry
   ```

### MQTT-Broker-Probleme

**Problem**: Der MQTT-Broker ist nicht erreichbar oder funktioniert nicht korrekt.

**Lösungen**:
1. Überprüfen Sie, ob der MQTT-Container läuft:
   ```bash
   docker-compose ps mqtt
   ```

2. Prüfen Sie die MQTT-Logs:
   ```bash
   docker-compose logs mqtt
   ```

3. Testen Sie die MQTT-Verbindung mit einem Tool wie mosquitto_pub/sub:
   ```bash
   docker-compose exec mqtt mosquitto_pub -h localhost -t test -m "Hallo"
   docker-compose exec mqtt mosquitto_sub -h localhost -t test
   ```

4. Stellen Sie sicher, dass die Konfigurationsdatei `mosquitto.conf` korrekt ist und die richtigen Berechtigungen hat.

5. Überprüfen Sie, ob die Ports 1883 und 9001 erreichbar sind:
   ```bash
   telnet localhost 1883
   telnet localhost 9001
   ```

## API-Server-Probleme

### API-Server startet nicht

**Problem**: Der API-Server startet nicht oder stürzt sofort ab.

**Lösungen**:
1. Überprüfen Sie die API-Server-Logs:
   ```bash
   docker-compose logs api
   ```

2. Stellen Sie sicher, dass alle benötigten Python-Pakete installiert sind:
   ```bash
   docker-compose exec api pip list
   ```

3. Überprüfen Sie, ob die Umgebungsvariablen korrekt gesetzt sind:
   ```bash
   docker-compose exec api env | grep API
   ```

4. Prüfen Sie, ob der Port 5000 bereits von einem anderen Dienst verwendet wird:
   ```bash
   sudo lsof -i :5000
   ```

5. Überprüfen Sie die Datenbankverbindung wie oben beschrieben.

### API-Endpunkte geben 404 oder 500 zurück

**Problem**: API-Endpunkte sind nicht erreichbar oder geben Fehler zurück.

**Lösungen**:
1. Überprüfen Sie, ob der API-Server läuft:
   ```bash
   docker-compose ps api
   ```

2. Testen Sie einen einfachen Endpunkt wie den Health-Check:
   ```bash
   curl http://localhost:5000/health
   ```

3. Überprüfen Sie die API-Logs auf spezifische Fehlermeldungen:
   ```bash
   docker-compose logs api
   ```

4. Stellen Sie sicher, dass die Routen korrekt definiert sind und die URL-Pfade stimmen.

5. Bei 500-Fehlern prüfen Sie die Ausnahmebehandlung im API-Code.

## Nextcloud-Integrationsprobleme

### Nextcloud-App stürzt ab oder verursacht Instabilität

**Problem**: Die Nextcloud-App stürzt ab oder verursacht Instabilität in der Nextcloud-Instanz.

**Lösungen**:
1. Stellen Sie sicher, dass die Nextcloud-App richtig als External App konfiguriert ist:
   ```xml
   <external-app>
       <load-parallel/>
       <iframe id="frame" src="..."/>
   </external-app>
   ```

2. Überprüfen Sie die Nextcloud-Logs:
   ```bash
   tail -f /path/to/nextcloud/data/nextcloud.log
   ```

3. Stellen Sie sicher, dass CORS korrekt konfiguriert ist und Anfragen von Ihrer Nextcloud-Domäne zugelassen werden.

4. Prüfen Sie, ob die URL in der iframe-src gültig ist und auf einen erreichbaren API-Server verweist.

5. Überprüfen Sie, ob die Nextcloud-App die Mindestanforderungen an die Nextcloud-Version erfüllt.

### Authentifizierungsprobleme in der Nextcloud-App

**Problem**: Authentifizierungsfehler in der Nextcloud-Integration.

**Lösungen**:
1. Überprüfen Sie, ob der API-Schlüssel korrekt ist und in den Nextcloud-App-Einstellungen richtig konfiguriert ist.

2. Prüfen Sie, ob die Nextcloud-Instanz als vertrauenswürdiger Client im API-Server konfiguriert ist.

3. Stellen Sie sicher, dass die Anfragen über HTTPS erfolgen, wenn der API-Server HTTPS erfordert.

4. Überprüfen Sie die API-Logs auf Authentifizierungsfehler:
   ```bash
   docker-compose logs api | grep "auth\|authentication\|unauthorized"
   ```

## ESP32-Geräteprobleme

### ESP32-Gerät verbindet nicht mit WLAN

**Problem**: Das ESP32-Gerät kann keine Verbindung zum WLAN herstellen.

**Lösungen**:
1. Überprüfen Sie SSID und Passwort in der Firmware.

2. Stellen Sie sicher, dass das WLAN-Signal stark genug ist und der Router 2,4-GHz-Netzwerke unterstützt.

3. Überprüfen Sie, ob die maximale Anzahl an Clients im WLAN erreicht ist.

4. Versuchen Sie, das Gerät zurückzusetzen und die Firmware neu zu flashen.

### ESP32-Gerät verbindet nicht mit der API oder dem MQTT-Broker

**Problem**: Das ESP32-Gerät kann keine Verbindung zur API oder zum MQTT-Broker herstellen.

**Lösungen**:
1. Überprüfen Sie, ob die IP-Adresse oder der Hostname des Servers korrekt ist.

2. Stellen Sie sicher, dass die entsprechenden Ports (5000 für API, 1883 für MQTT) erreichbar sind.

3. Prüfen Sie, ob Authentifizierungsdaten (für MQTT) korrekt konfiguriert sind.

4. Überprüfen Sie die Logs des API-Servers oder MQTT-Brokers auf Verbindungsversuche:
   ```bash
   docker-compose logs mqtt | grep "connect"
   docker-compose logs api | grep "device_id"
   ```

5. Testen Sie die Erreichbarkeit des Servers vom WLAN des ESP32 aus mit einem anderen Gerät.

### Sensordaten werden nicht angezeigt oder aktualisiert

**Problem**: Sensordaten werden nicht korrekt angezeigt oder aktualisiert.

**Lösungen**:
1. Überprüfen Sie, ob die Sensordaten korrekt gesendet werden:
   ```bash
   docker-compose logs mqtt | grep "swissairdry/device_id/data"
   ```

2. Stellen Sie sicher, dass das JSON-Format der Sensordaten korrekt ist.

3. Überprüfen Sie in der Datenbank, ob die Daten gespeichert werden:
   ```bash
   docker-compose exec postgres psql -U swissairdry -d swissairdry -c "SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 5;"
   ```

4. Prüfen Sie, ob die API-Endpunkte zum Abrufen von Sensordaten funktionieren:
   ```bash
   curl http://localhost:5000/api/device/device_id/data
   ```

## Datenbank-Probleme

### Datenbank enthält keine Tabellen

**Problem**: Die Datenbank scheint leer zu sein oder enthält nicht die erwarteten Tabellen.

**Lösungen**:
1. Überprüfen Sie, ob die Datenbankmigration beim Start des API-Servers ausgeführt wurde:
   ```bash
   docker-compose logs api | grep "migration\|database\|table"
   ```

2. Listen Sie die vorhandenen Tabellen in der Datenbank auf:
   ```bash
   docker-compose exec postgres psql -U swissairdry -d swissairdry -c "\dt"
   ```

3. Führen Sie die Datenbankmigration manuell aus:
   ```bash
   docker-compose exec api python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"
   ```

### Datenbank ist voll oder langsam

**Problem**: Die Datenbank wird zu groß oder Abfragen werden langsam.

**Lösungen**:
1. Überprüfen Sie die Größe der Datenbank:
   ```bash
   docker-compose exec postgres psql -U swissairdry -d swissairdry -c "SELECT pg_size_pretty(pg_database_size('swissairdry'));"
   ```

2. Identifizieren Sie große Tabellen:
   ```bash
   docker-compose exec postgres psql -U swissairdry -d swissairdry -c "SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) FROM pg_catalog.pg_statio_user_tables ORDER BY pg_total_relation_size(relid) DESC;"
   ```

3. Löschen Sie alte Sensordaten:
   ```bash
   docker-compose exec postgres psql -U swissairdry -d swissairdry -c "DELETE FROM sensor_data WHERE timestamp < NOW() - INTERVAL '30 days';"
   ```

4. Führen Sie eine Datenbank-Vakuumierung durch:
   ```bash
   docker-compose exec postgres psql -U swissairdry -d swissairdry -c "VACUUM FULL;"
   ```

5. Implementieren Sie eine Datenhaltungsrichtlinie, um alte Daten regelmäßig zu bereinigen.

## Weitere Ressourcen

Wenn die oben genannten Lösungen nicht helfen, konsultieren Sie:

- Die offiziellen Docker-Dokumentation: https://docs.docker.com/
- Die FastAPI-Dokumentation: https://fastapi.tiangolo.com/
- Die PostgreSQL-Dokumentation: https://www.postgresql.org/docs/
- Die Mosquitto-MQTT-Broker-Dokumentation: https://mosquitto.org/documentation/
- Die ESP32-Arduino-Dokumentation: https://docs.espressif.com/projects/arduino-esp32/

Oder wenden Sie sich an den SwissAirDry-Support unter support@swissairdry.com.