# SwissAirDry Docker-Installation

Diese Anleitung beschreibt, wie du SwissAirDry mit Docker Desktop installieren und ausführen kannst.

## Voraussetzungen

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installiert
- Git (optional, für den Download des Repositories)

## Installation

1. Stelle sicher, dass Docker Desktop läuft.

2. Öffne ein Terminal/Kommandozeile und navigiere in das SwissAirDry/containers Verzeichnis:

```bash
cd pfad/zu/SwissAirDry/containers
```

3. Starte alle Container mit:

```bash
docker-compose up -d
```

Das `-d` Flag startet die Container im Hintergrund (detached mode).

4. Um den Status der Container zu prüfen:

```bash
docker-compose ps
```

## Zugriff auf die Dienste

Nach erfolgreicher Installation kannst du auf die folgenden Dienste zugreifen:

- Nextcloud: http://localhost:8080
  - Benutzername: admin (oder wie in .env definiert)
  - Passwort: admin123 (oder wie in .env definiert)

- SwissAirDry API: http://localhost:5000
  - API Dokumentation: http://localhost:5000/docs

- SwissAirDry Simple API: http://localhost:5001
  - API Dokumentation: http://localhost:5001/docs

- MQTT-Broker: 
  - Port: 1883 (MQTT)
  - Port: 9001 (WebSocket)

## Häufige Befehle

### Container starten
```bash
docker-compose up -d
```

### Container stoppen
```bash
docker-compose down
```

### Logs anzeigen
```bash
docker-compose logs -f
```

Um nur die Logs eines bestimmten Dienstes anzuzeigen:
```bash
docker-compose logs -f swissairdry-api
```

### Container neu erstellen und starten
```bash
docker-compose up -d --build
```

### Container und Volumes löschen (alle Daten werden gelöscht!)
```bash
docker-compose down -v
```