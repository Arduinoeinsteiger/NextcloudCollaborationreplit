# SwissAirDry Installations- und Konfigurationsanleitung

Diese Anleitung beschreibt die Installation und Konfiguration des SwissAirDry Stacks, bestehend aus API-Server, MQTT-Broker, Datenbank und Nextcloud-Integration (ExApp).

## Systemvoraussetzungen

- Ubuntu 22.04 LTS oder höher (oder eine andere kompatible Linux-Distribution)
- Mindestens 2 GB RAM
- Mindestens 20 GB freier Festplattenspeicher
- Internetverbindung für die Installation von Paketen und Docker-Images

## Schnelle Installation (Automatisch)

Für eine schnelle und automatische Installation können Sie den folgenden Befehl verwenden:

```bash
git clone https://github.com/swissairdry/swissairdry.git
cd swissairdry
sudo bash install.sh --auto
```

Diese Methode installiert alle notwendigen Komponenten mit Standardeinstellungen und generiert automatisch sichere Passwörter.

## Manuelle Installation

Wenn Sie die Installation anpassen möchten, folgen Sie diesen Schritten:

### 1. Repository klonen

```bash
git clone https://github.com/swissairdry/swissairdry.git
cd swissairdry
```

### 2. Installationsskript ausführen

```bash
sudo bash install.sh
```

Folgen Sie den Anweisungen auf dem Bildschirm, um die Domain und andere Einstellungen zu konfigurieren.

### 3. Service-Überprüfung

Nach Abschluss der Installation können Sie die Dienste überprüfen:

- API-Server: http://localhost:5000
- Simple API: http://localhost:5001
- MQTT-Broker: localhost:1883
- Nextcloud ExApp: http://localhost:8000

## Konfiguration der Ports

Die folgenden Ports werden vom SwissAirDry Stack verwendet:

| Port | Dienst                     | Protokoll | Beschreibung                                          |
|------|----------------------------|-----------|-------------------------------------------------------|
| 80   | HTTP                       | TCP       | HTTP-Weiterleitungen zu HTTPS                         |
| 443  | HTTPS                      | TCP       | Verschlüsselte Webzugriffe                            |
| 1883 | MQTT                       | TCP       | Verbindung für ESP-Geräte und API                     |
| 5000 | API-Server                 | TCP       | Hauptschnittstelle für Webanwendungen und Mobile Apps |
| 5001 | Simple API-Server          | TCP       | Vereinfachte API für ESP-Geräte                       |
| 5432 | PostgreSQL                 | TCP       | Datenbankzugriff                                      |
| 8000 | Nextcloud ExApp            | TCP       | Nextcloud External App (für Entwicklung)              |
| 8080 | Nextcloud                  | TCP       | Nextcloud-Webinterface (falls aktiviert)              |
| 9001 | MQTT Websockets            | TCP       | MQTT über Websockets für Webanwendungen               |

## Konfiguration der DNS-Einträge

Für eine vollständige Installation sollten Sie die folgenden DNS-Einträge konfigurieren:

- `vgnc.org` → Ihre Server-IP
- `api.vgnc.org` → Ihre Server-IP
- `mqtt.vgnc.org` → Ihre Server-IP

## SSL-Zertifikate für die Produktion

Für eine Produktionsumgebung empfehlen wir die Verwendung von Let's Encrypt-Zertifikaten:

```bash
sudo apt-get install certbot
sudo certbot certonly --standalone -d vgnc.org -d www.vgnc.org -d api.vgnc.org -d mqtt.vgnc.org
```

Kopieren Sie dann die Zertifikate in die entsprechenden Verzeichnisse:

```bash
sudo cp /etc/letsencrypt/live/vgnc.org/fullchain.pem ./ssl/certs/vgnc.org.cert.pem
sudo cp /etc/letsencrypt/live/vgnc.org/privkey.pem ./ssl/private/vgnc.org.key.pem
sudo chmod 644 ./ssl/certs/vgnc.org.cert.pem
sudo chmod 600 ./ssl/private/vgnc.org.key.pem
```

## Docker-Container-Management

### Container neu starten

```bash
docker compose restart
```

### Logs anzeigen

```bash
# Alle Logs anzeigen
docker compose logs

# Logs eines bestimmten Dienstes anzeigen
docker compose logs api
docker compose logs mqtt
docker compose logs db
```

### Updates installieren

```bash
sudo bash install.sh --update
```

## ESP-Geräte Konfiguration

Die ESP-Firmware ist so konzipiert, dass sie sich automatisch mit dem MQTT-Broker verbindet. Konfigurieren Sie die ESP-Geräte mit dem QR-Code oder über die Webschnittstelle:

1. Verbinden Sie sich mit dem WLAN des ESP-Geräts (normalerweise "SwissAirDry-XXXXX")
2. Öffnen Sie die Adresse 192.168.4.1 in Ihrem Browser
3. Konfigurieren Sie die WLAN-Zugangsdaten und den MQTT-Server
4. Das ESP-Gerät verbindet sich automatisch und sendet Sensordaten an den MQTT-Broker

## Fehlerbehebung

### MQTT-Verbindungsprobleme

Prüfen Sie, ob der MQTT-Broker korrekt läuft:

```bash
docker logs swissairdry-mqtt
```

Überprüfen Sie, ob die Firewall die erforderlichen Ports erlaubt:

```bash
sudo ufw status
```

### API-Server-Probleme

Überprüfen Sie die API-Server-Logs:

```bash
docker logs swissairdry-api
```

### Datenbank-Probleme

Überprüfen Sie, ob die Datenbank läuft und erreichbar ist:

```bash
docker exec -it swissairdry-db psql -U swissairdry -d swissairdry -c "SELECT version();"
```

## Weitere Informationen

Für weitere Informationen, Updates und Hilfe besuchen Sie:
- [GitHub Repository](https://github.com/SwissAirDry/swissairdry)
- [SwissAirDry Dokumentation](https://docs.swissairdry.ch)
- [Fehlerbehebung](FEHLERBEHEBUNG.md)