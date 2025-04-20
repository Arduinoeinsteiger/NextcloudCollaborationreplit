# SwissAirDry Fehlerbehebungsanleitung

Diese Anleitung hilft Ihnen bei der Behebung häufiger Probleme mit dem SwissAirDry-System.

## Inhaltsverzeichnis

1. [Docker-bezogene Probleme](#docker-bezogene-probleme)
2. [Netzwerkprobleme](#netzwerkprobleme)
3. [SSL-/TLS-Probleme](#ssl-tls-probleme)
4. [Nextcloud-Probleme](#nextcloud-probleme)
5. [API-Probleme](#api-probleme)
6. [MQTT-Probleme](#mqtt-probleme)
7. [Datenbank-Probleme](#datenbank-probleme)
8. [Häufige Fehlercodes](#häufige-fehlercodes)

---

## Docker-bezogene Probleme

### Container startet nicht

**Symptom**: Ein oder mehrere Container starten nicht.

**Lösungsansätze**:

1. Logs des betroffenen Containers prüfen:
   ```bash
   docker-compose logs [service-name]
   ```

2. Container neustarten:
   ```bash
   docker-compose restart [service-name]
   ```

3. Container mit neuen Images neu erstellen:
   ```bash
   docker-compose pull [service-name]
   docker-compose up -d --force-recreate [service-name]
   ```

### Unzureichender Speicherplatz

**Symptom**: Docker Container können nicht erstellt werden oder stürzen ab.

**Lösungsansätze**:

1. Speicherplatz überprüfen:
   ```bash
   df -h
   ```

2. Ungenutzten Docker-Ressourcen bereinigen:
   ```bash
   docker system prune -a
   ```

3. Laufende Container und deren Größe anzeigen:
   ```bash
   docker ps -s
   ```

---

## Netzwerkprobleme

### Dienste sind nicht erreichbar

**Symptom**: Weboberfläche oder API ist nicht erreichbar.

**Lösungsansätze**:

1. Prüfen, ob die Dienste laufen:
   ```bash
   docker-compose ps
   ```

2. Netzwerkkonfiguration überprüfen:
   ```bash
   docker network inspect swissairdry_network
   ```

3. Ports auf dem Host prüfen:
   ```bash
   netstat -tulpn | grep -E '80|443|1883|8883|5432'
   ```

4. Firewall-Einstellungen überprüfen und ggf. Ports freigeben:
   ```bash
   sudo ufw status
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```

---

## SSL-/TLS-Probleme

### Zertifikatsfehler

**Symptom**: Browser zeigt SSL-Fehler oder Dienste können nicht verschlüsselt kommunizieren.

**Lösungsansätze**:

1. Zertifikatsdateien überprüfen:
   ```bash
   ls -la /opt/swissairdry/nginx/ssl/
   ```

2. Überprüfen, ob die Zertifikate gültig sind:
   ```bash
   openssl x509 -in /opt/swissairdry/nginx/ssl/fullchain.pem -text -noout
   ```

3. Zertifikate erneuern (bei Let's Encrypt):
   ```bash
   certbot renew
   ```

4. Bei selbstsignierten Zertifikaten: Neue Zertifikate generieren und Container neustarten:
   ```bash
   docker-compose restart nginx mqtt
   ```

---

## Nextcloud-Probleme

### Nextcloud zeigt Wartungsmodus oder Fehler

**Symptom**: Nextcloud ist im Wartungsmodus oder zeigt Fehler an.

**Lösungsansätze**:

1. Nextcloud-Logs überprüfen:
   ```bash
   docker-compose logs nextcloud_app
   ```

2. Datenbank-Verbindung prüfen:
   ```bash
   docker-compose exec -T nextcloud_app php occ status
   ```

3. Wartungsmodus deaktivieren:
   ```bash
   docker-compose exec -T nextcloud_app php occ maintenance:mode --off
   ```

4. Nextcloud-Berechtigungen reparieren:
   ```bash
   docker-compose exec -T nextcloud_app chown -R www-data:www-data /var/www/html
   ```

5. Nextcloud aktualisieren:
   ```bash
   docker-compose exec -T nextcloud_app php occ upgrade
   ```

### Externe App funktioniert nicht

**Symptom**: Die SwissAirDry-App erscheint nicht in Nextcloud oder funktioniert nicht korrekt.

**Lösungsansätze**:

1. Prüfen, ob die App installiert ist:
   ```bash
   docker-compose exec -T nextcloud_app php occ app:list | grep external
   ```

2. App neu installieren:
   ```bash
   docker-compose exec -T nextcloud_app php occ app:install external
   docker-compose exec -T nextcloud_app php occ app:enable external
   ```

3. Berechtigungen überprüfen:
   ```bash
   docker-compose exec -T nextcloud_app php occ app:update external
   ```

---

## API-Probleme

### API gibt Fehler zurück

**Symptom**: API-Anfragen schlagen fehl oder liefern unerwartete Ergebnisse.

**Lösungsansätze**:

1. API-Logs überprüfen:
   ```bash
   docker-compose logs api
   ```

2. API-Container neustarten:
   ```bash
   docker-compose restart api
   ```

3. API-Verbindung zur Datenbank prüfen:
   ```bash
   docker-compose exec api python -c "import psycopg2; conn = psycopg2.connect('host=postgres dbname=swissairdry user=swissairdry password=PASSWORD_AUS_ENV_DATEI'); print('Verbindung OK')"
   ```
   (Ersetzen Sie PASSWORD_AUS_ENV_DATEI durch das tatsächliche Passwort)

4. Prüfen, ob die API erreichbar ist:
   ```bash
   curl -k https://api.ihre-domain.de/health
   ```

---

## MQTT-Probleme

### MQTT-Verbindungsprobleme

**Symptom**: Geräte können keine Verbindung zum MQTT-Broker herstellen oder MQTT-Container startet ständig neu.

**Lösungsansätze**:

1. MQTT-Logs prüfen:
   ```bash
   docker-compose logs mqtt
   ```

2. MQTT-Konfiguration überprüfen:
   ```bash
   cat /opt/swissairdry/mqtt/config/mosquitto.conf
   ```

3. Prüfen, ob der MQTT-Broker läuft und Ports geöffnet sind:
   ```bash
   docker-compose ps mqtt
   netstat -tulpn | grep -E '1883|8883'
   ```

4. **Problem mit SSL-Zertifikaten für MQTT beheben**:
   
   Wenn in den Logs Fehler zu "Permission denied" oder Problemen mit den SSL-Zertifikaten erscheinen:
   ```bash
   # Zertifikats-Berechtigungsproblem beheben
   sudo chmod -R 755 /opt/swissairdry/nginx/ssl
   sudo chown -R 1883:1883 /opt/swissairdry/nginx/ssl
   sudo chmod 600 /opt/swissairdry/nginx/ssl/privkey.pem
   
   # Oder alternativ in docker-compose.yml das :ro Flag entfernen
   # - /opt/swissairdry/nginx/ssl:/mosquitto/certs:ro → - /opt/swissairdry/nginx/ssl:/mosquitto/certs
   ```

5. Bei anhaltenden SSL-Problemen die SSL-Konfiguration temporär deaktivieren:
   ```bash
   # In /opt/swissairdry/mqtt/config/mosquitto.conf die SSL-Listener-Zeilen auskommentieren:
   # listener 8883
   # certfile /mosquitto/certs/fullchain.pem
   # keyfile /mosquitto/certs/privkey.pem
   # require_certificate false
   ```

6. MQTT-Broker neustarten mit korrektem User:
   ```bash
   # In docker-compose.yml den user-Parameter ergänzen (falls fehlend)
   # user: "1883"  # Unter dem volumes-Bereich
   
   # Dann neu starten
   docker-compose restart mqtt
   ```

7. MQTT-Verbindung mit einem Test-Client prüfen:
   ```bash
   docker run --rm -it eclipse-mosquitto mosquitto_pub -h ihre-domain.de -p 1883 -t test -m "hello"
   ```

---

## Datenbank-Probleme

### PostgreSQL-Datenbankprobleme

**Symptom**: API kann nicht auf die Datenbank zugreifen oder Datenbankfehler werden angezeigt.

**Lösungsansätze**:

1. Datenbank-Logs prüfen:
   ```bash
   docker-compose logs postgres
   ```

2. Datenbank-Status prüfen:
   ```bash
   docker-compose exec postgres pg_isready
   ```

3. Verbindung zur Datenbank testen:
   ```bash
   docker-compose exec postgres psql -U swissairdry -d swissairdry -c "SELECT 1"
   ```

4. Datenbank-Container neustarten:
   ```bash
   docker-compose restart postgres
   ```

### MariaDB/MySQL-Datenbankprobleme (Nextcloud)

**Symptom**: Nextcloud kann nicht auf die Datenbank zugreifen.

**Lösungsansätze**:

1. Datenbank-Logs prüfen:
   ```bash
   docker-compose logs db
   ```

2. Verbindung zur Datenbank testen:
   ```bash
   docker-compose exec db mysql -u nextcloud -p -e "SHOW DATABASES"
   ```
   (Geben Sie das Passwort ein, wenn Sie dazu aufgefordert werden)

3. Datenbank-Container neustarten:
   ```bash
   docker-compose restart db
   ```

---

## Häufige Fehlercodes

### HTTP-Statuscodes

- **404 Not Found**: Ressource konnte nicht gefunden werden
  - Prüfen Sie die URL und die Konfiguration des Reverse Proxy

- **502 Bad Gateway**: Nginx kann nicht mit dem Backend kommunizieren
  - Prüfen Sie, ob der API-Container läuft
  - Prüfen Sie die Netzwerkkonfiguration

- **503 Service Unavailable**: Dienst ist temporär nicht verfügbar
  - Prüfen Sie den Status des entsprechenden Containers

### Nextcloud-Fehlermeldungen

- **CSRF check failed**: Sitzungsproblem
  - Browser-Cache leeren und erneut anmelden

- **No database drivers (PDO) installed**: Datenbanktreiber fehlt
  - Prüfen Sie die Nextcloud-Installation

### SwissAirDry API-Fehlercodes

- **401 Unauthorized**: Authentifizierungsproblem
  - Prüfen Sie den API-Token oder die Anmeldedaten

- **403 Forbidden**: Keine Berechtigung
  - Prüfen Sie die Benutzerrechte

- **500 Internal Server Error**: Serverfehler
  - Prüfen Sie die API-Logs für detaillierte Fehlermeldungen

---

## Wiederherstellung nach Datenverlust

### Backup-Wiederherstellung

**Schritt-für-Schritt-Anleitung**:

1. Nextcloud-Datenbank wiederherstellen:
   ```bash
   docker-compose exec -T db mysql -u root -p nextcloud < nextcloud_backup.sql
   ```

2. Nextcloud-Dateien wiederherstellen (falls Sie ein Backup haben):
   ```bash
   # Beispiel mit rsync
   rsync -av /path/to/backup/nextcloud/ /opt/swissairdry/nextcloud/nextcloud_data/
   ```

3. SwissAirDry-Datenbank wiederherstellen:
   ```bash
   docker-compose exec -T postgres psql -U swissairdry -d swissairdry < swissairdry_backup.sql
   ```

4. Container neustarten:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

Bei weiteren Fragen oder Problemen wenden Sie sich bitte an den Support:
- E-Mail: support@swissairdry.com
- Webseite: https://swissairdry.com/support