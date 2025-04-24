# SwissAirDry Nextcloud ExApp - Installationsanleitung

Diese Anleitung beschreibt die Installation der SwissAirDry-App als moderne ExApp (External App) in Nextcloud ab Version 25.

## Voraussetzungen

* Nextcloud Server (Version 25 oder höher)
* Docker auf dem Nextcloud-Server
* Administrator-Zugriff auf Nextcloud

## 1. Installation über den Nextcloud App Store (empfohlen)

Die einfachste Methode zur Installation ist über den Nextcloud App Store:

1. Melden Sie sich als Administrator bei Ihrer Nextcloud-Instanz an
2. Navigieren Sie zu "Apps" > "App-Verwaltung"
3. Wählen Sie die Kategorie "Integration" oder suchen Sie nach "SwissAirDry"
4. Klicken Sie auf "Installieren"

Die App wird automatisch heruntergeladen und eingerichtet, einschließlich des Docker-Containers.

## 2. Manuelle Installation

Wenn Sie die App manuell installieren möchten:

1. Laden Sie das App-Paket von GitHub herunter:
   ```bash
   git clone https://github.com/Arduinoeinsteiger/NextcloudCollaborationreplit
   ```

2. Kopieren Sie den `swissairdry`-Ordner in das Nextcloud `apps`-Verzeichnis:
   ```bash
   cp -r swissairdry /path/to/nextcloud/apps/
   ```

3. Aktivieren Sie die App über die Kommandozeile:
   ```bash
   cd /path/to/nextcloud
   sudo -u www-data php occ app:enable swissairdry
   ```

4. Da SwissAirDry eine ExApp ist, wird Nextcloud automatisch versuchen, den entsprechenden Docker-Container herunterzuladen und zu starten.

## 3. Docker-Container manuell konfigurieren

Wenn der automatische Docker-Setup nicht funktioniert, können Sie den Container manuell einrichten:

1. Ziehen Sie das Docker-Image:
   ```bash
   docker pull ghcr.io/arduinoeinsteiger/swissairdry:latest
   ```

2. Registrieren Sie die App als ExApp:
   ```bash
   sudo -u www-data php occ app_api:app:register swissairdry \
     --json-info /path/to/nextcloud/apps/swissairdry/appinfo/info.xml \
     --docker-image ghcr.io/arduinoeinsteiger/swissairdry:latest
   ```

## 4. Konfiguration

Nach der Installation:

1. Navigieren Sie zu "Einstellungen" > "SwissAirDry"
2. Konfigurieren Sie die folgenden Einstellungen:
   - API-Server-URL
   - MQTT-Broker-Einstellungen
   - Benutzer-Zugriffsrechte

## Fehlerbehebung

### Nextcloud stürzt beim Zugriff auf die App ab

Dies deutet auf ein Problem mit der ExApp-Integration hin. Prüfen Sie:

1. Die Docker-Installation auf Ihrem Server:
   ```bash
   docker ps | grep swissairdry
   ```

2. Die ExApp-Registrierung in Nextcloud:
   ```bash
   sudo -u www-data php occ app_api:app:list
   ```

3. Kontrollieren Sie die Nextcloud-Logs:
   ```bash
   tail -f /path/to/nextcloud/data/nextcloud.log
   ```

### Container startet nicht

Wenn der Docker-Container nicht startet:

1. Prüfen Sie den Container-Status:
   ```bash
   docker logs swissairdry
   ```

2. Stellen Sie sicher, dass die Ports nicht blockiert sind
3. Überprüfen Sie, ob Docker genügend Ressourcen hat

## Aktualisierung

Updates werden automatisch über den Nextcloud App Store bereitgestellt. Bei manueller Installation:

1. Stoppen Sie den alten Container:
   ```bash
   docker stop swissairdry
   ```

2. Laden Sie das neue App-Paket herunter und installieren Sie es wie oben beschrieben
3. Aktualisieren Sie die App in Nextcloud:
   ```bash
   sudo -u www-data php occ app:update swissairdry
   ```