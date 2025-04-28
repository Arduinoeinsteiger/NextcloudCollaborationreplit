# Fehlerbehebung CI-Probleme

Dieses Dokument enthält Informationen zur Behebung von CI-Problemen bei GitHub Actions für das SwissAirDry-Projekt.

## Bekannte Probleme mit GitHub Actions

1. **Zugriffsprobleme auf Container-Registry**
   - **Problem**: `denied: failed to fetch anonymous token: unexpected status: 403 Forbidden`
   - **Lösung**: Ersetzen Sie ghcr.io-Image-Referenzen in docker-compose.yml durch lokale Builds.

2. **Python-Syntaxfehler in CI**
   - **Problem**: Die CI-Pipeline meldet Syntaxfehler in Python-Dateien.
   - **Lösung**: Verwenden Sie das `fix_all_ci_issues.py`-Skript, um Python-Syntax zu korrigieren.

3. **Veraltete GitHub Actions Versionen**
   - **Problem**: Fehler mit neuesten Actions-Versionen (v4)
   - **Lösung**: Aktualisierung auf stabile Versionen (v3) mit dem Skript `update_github_actions.py`.

## Fehlerhafte Docker-Image-Referenzen

Die häufigsten Fehler treten beim Zugriff auf Docker-Images von der GitHub Container Registry auf:

```
! simple-api Warning: Head "https://ghcr.io/v2/arduinoeinsteiger/swissairdry-simple-api/manifests/latest": denied
! exapp Warning: Head "https://ghcr.io/v2/arduinoeinsteiger/swissairdry-exapp/manifests/latest": denied
! api Warning: Head "https://ghcr.io/v2/arduinoeinsteiger/swissairdry-api/manifests/latest": denied
! exapp-daemon Warning: Head "https://ghcr.io/v2/arduinoeinsteiger/swissairdry-exapp-daemon/manifests/latest": denied
```

### Lösung: Lokale Builds verwenden

Ändern Sie die `docker-compose.yml` wie folgt:

Statt:
```yaml
services:
  api:
    image: ghcr.io/arduinoeinsteiger/swissairdry-api:latest
```

Verwenden Sie:
```yaml
services:
  api:
    build: ./swissairdry/api
```

## Fehlende Dateien und Verzeichnisse

Bei Fehlern wie:
```
ERROR [simple-api 6/7] COPY start_simple.py .:
ERROR [api 6/7] COPY app/ app/:
```

Führen Sie das `FINAL_FIX.sh`-Skript aus, das alle fehlenden Verzeichnisse und Dateien erstellt.

## Python-Abhängigkeitsprobleme

Wenn LSP-Fehler (Language Server Protocol) gemeldet werden wie:
```
Error on line 11:
Import "sqlalchemy" could not be resolved
```

### Lösung:

1. Führen Sie `pip install -r swissairdry/api/requirements.api.txt` aus.
2. Stellen Sie sicher, dass alle erforderlichen Python-Pakete installiert sind.

## STM32-Support verbessern

Für verbesserte STM32-Unterstützung:

1. Stellen Sie sicher, dass die entsprechenden Routen in der API verfügbar sind.
2. Prüfen Sie, ob die Hardware-Treiber und Kommunikationsprotokolle korrekt eingerichtet sind.

## Portainer-Integration

Portainer kann nach der Installation über http://localhost:9000 aufgerufen werden.

1. Erstellen Sie bei der ersten Anmeldung einen Admin-Benutzer.
2. Wählen Sie 'Local' als Umgebung für den Zugriff auf lokale Docker-Container.
3. Verwalten Sie alle Container über die Portainer-Oberfläche.

## Nextcloud-Integration

Falls die Nextcloud-Integration erforderlich ist, stellen Sie sicher, dass:

1. Die Nextcloud-Docker-Container konfiguriert und gestartet sind.
2. Die ExApp-Komponenten korrekt installiert und mit der API verbunden sind.
3. Die erforderlichen Umgebungsvariablen in der `.env`-Datei definiert sind.

## Automatisierte Skripte zur Fehlerbehebung

Das Projekt enthält mehrere automatisierte Skripte zur Fehlerbehebung:

1. `FINAL_FIX.sh` - Komplettes Reparatur-Skript für alle bekannten Probleme
2. `fix_all_ci_issues.py` - Behebt CI-Probleme in Python-Dateien
3. `update_github_actions.py` - Aktualisiert GitHub Actions auf stabile Versionen
4. `fix_docker_installation.sh` - Repariert Docker-Installationsprobleme

Führen Sie die Skripte in der angegebenen Reihenfolge aus, um die meisten Probleme zu beheben.