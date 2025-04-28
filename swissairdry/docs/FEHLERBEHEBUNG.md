# SwissAirDry Fehlerbehebung

Diese Anleitung hilft bei der Behebung häufiger Probleme mit dem SwissAirDry-System.

## Inhaltsverzeichnis

1. [Diagnose-Tools](#diagnose-tools)
2. [Häufige Probleme](#häufige-probleme)
   - [Docker-Container starten nicht](#docker-container-starten-nicht)
   - [API ist nicht erreichbar](#api-ist-nicht-erreichbar)
   - [MQTT-Verbindung fehlgeschlagen](#mqtt-verbindung-fehlgeschlagen)
   - [Dateisystem-Inkonsistenzen](#dateisystem-inkonsistenzen)
3. [Reparatur-Anleitung](#reparatur-anleitung)
4. [Manuelle Behebungsschritte](#manuelle-behebungsschritte)
5. [Kontakt und Support](#kontakt-und-support)

## Diagnose-Tools

Im SwissAirDry-Paket sind zwei Diagnose-Tools enthalten:

1. **diagnose_system.sh**: Dieses Skript führt eine umfassende Systemdiagnose durch und identifiziert potenzielle Probleme.

   ```bash
   ./diagnose_system.sh
   ```

2. **system_repair.sh**: Dieses Skript behebt bekannte Probleme automatisch und stellt das System wieder her.

   ```bash
   ./system_repair.sh
   ```

## Häufige Probleme

### Docker-Container starten nicht

**Symptome:**
- Docker-Compose zeigt Fehler an
- Container werden gestartet, beenden sich aber sofort
- Keine laufenden Container sichtbar mit `docker ps`

**Lösungen:**
1. Überprüfen Sie den Docker-Daemon-Status:
   ```bash
   sudo systemctl status docker
   ```

2. Überprüfen Sie die Container-Logs:
   ```bash
   docker logs swissairdry-api
   docker logs swissairdry-mqtt
   ```

3. Starten Sie die Docker-Services neu:
   ```bash
   sudo systemctl restart docker
   ./system_repair.sh
   ```

### API ist nicht erreichbar

**Symptome:**
- API-Endpunkte antworten nicht (Port 5000/5001)
- Browser zeigt "Verbindung abgelehnt" oder Timeout-Fehler

**Lösungen:**
1. Überprüfen Sie, ob die Container laufen:
   ```bash
   docker ps | grep api
   ```

2. Überprüfen Sie die Container-Logs:
   ```bash
   docker logs swissairdry-api
   ```

3. Überprüfen Sie die Port-Bindungen:
   ```bash
   ss -tuln | grep 5000
   ```

4. Neu starten des API-Containers:
   ```bash
   docker-compose restart api
   ```

### MQTT-Verbindung fehlgeschlagen

**Symptome:**
- IoT-Geräte können keine Verbindung zum MQTT-Broker herstellen
- Fehler "Connection refused" oder Timeouts
- MQTT-Client kann nicht auf Port 1883 verbinden

**Lösungen:**
1. Überprüfen Sie, ob der MQTT-Broker läuft:
   ```bash
   docker ps | grep mqtt
   ```

2. Überprüfen Sie die MQTT-Broker-Logs:
   ```bash
   docker logs swissairdry-mqtt
   ```

3. Überprüfen Sie die mosquitto.conf:
   ```bash
   cat swissairdry/mqtt/mosquitto.conf
   ```

4. Neu starten des MQTT-Containers:
   ```bash
   docker-compose restart mqtt
   ```

### Dateisystem-Inkonsistenzen

**Symptome:**
- Einige Dateien werden als gelöscht markiert, sind aber noch vorhanden
- Fehler beim Ausführen von Git-Befehlen
- Inkonsistente Versionskontrolle

**Lösungen:**
1. Bereinigen Sie den Git-Status:
   ```bash
   git status
   git clean -fd   # Vorsicht: Entfernt nicht-getrackte Dateien
   ```

2. Reset auf den letzten bekannten guten Zustand:
   ```bash
   git reset --hard origin/main
   ```

3. Führen Sie das Reparatur-Skript aus:
   ```bash
   ./system_repair.sh
   ```

## Reparatur-Anleitung

Falls das System nicht normal funktioniert, befolgen Sie diese Schritte:

1. **Diagnose durchführen**:
   ```bash
   ./diagnose_system.sh
   ```
   Überprüfen Sie die Ausgabe auf Fehler und Warnungen.

2. **System reparieren**:
   ```bash
   ./system_repair.sh
   ```
   Dieses Skript wird:
   - Bestehende Container stoppen und entfernen
   - Wichtige Verzeichnisse erstellen
   - Konfigurationsdateien wiederherstellen
   - Container neu starten

3. **Container-Status überprüfen**:
   ```bash
   docker ps
   ```
   Alle SwissAirDry-Container sollten im Status "Up" sein.

4. **Logs überprüfen**:
   ```bash
   docker-compose logs
   ```
   Suchen Sie nach Fehlermeldungen oder ungewöhnlichen Warnungen.

## Manuelle Behebungsschritte

Falls die automatischen Skripte das Problem nicht beheben, können diese manuellen Schritte helfen:

1. **Komplette Neuinstallation**:
   ```bash
   # Docker-Container und Volumes entfernen
   docker-compose down -v
   
   # Git-Repo zurücksetzen
   git reset --hard origin/main
   git clean -fd
   
   # System neu installieren
   ./system_repair.sh
   ```

2. **Docker-System bereinigen**:
   ```bash
   # Ungenutzte Container, Netzwerke und Images entfernen
   docker system prune -a
   
   # Volumes bereinigen (Vorsicht: Daten gehen verloren!)
   docker volume prune
   ```

3. **Dateisystem überprüfen**:
   ```bash
   # Wichtige Verzeichnisse erstellen
   mkdir -p swissairdry/api/app
   mkdir -p swissairdry/mqtt
   mkdir -p nginx/conf.d
   
   # Berechtigungen korrigieren
   chmod -R 755 .
   ```

## Kontakt und Support

Bei anhaltenden Problemen wenden Sie sich bitte an das SwissAirDry-Support-Team:

- E-Mail: support@swissairdry.com
- Support-Website: https://support.swissairdry.com
- GitHub Issues: https://github.com/swissairdry/swissairdry/issues