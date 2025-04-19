# SwissAirDry "Schlüsselfertige" Installationsanleitung

Diese Anleitung beschreibt die Installation des SwissAirDry-Systems auf einem neuen Server. Sie bietet eine vollständige "schlüsselfertige" Lösung, die alle Komponenten installiert und konfiguriert.

## Systemvoraussetzungen

- Unterstützte Linux-Distribution: Ubuntu 22.04 LTS oder Debian 11+
- Minimaler Server:
  - 2 CPU-Kerne
  - 4 GB RAM
  - 40 GB Festplattenspeicher
- Empfohlener Server:
  - 4 CPU-Kerne
  - 8 GB RAM
  - 80 GB SSD-Speicher
- Öffentliche IP-Adresse mit Ports 80, 443, 1883 und 9001 freigegeben
- Registrierte Domain mit DNS-Konfiguration

## Vorbereitung

### Systemupdate

Führen Sie ein Systemupdate durch:

```bash
sudo apt update
sudo apt upgrade -y
```

### Firewall konfigurieren

Stellen Sie sicher, dass die erforderlichen Ports freigegeben sind:

```bash
sudo apt install -y ufw
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw allow 1883/tcp  # MQTT
sudo ufw allow 9001/tcp  # MQTT Websockets
sudo ufw enable
```

## One-Line-Installation

Für eine vollautomatische Installation:

```bash
wget -qO- https://raw.githubusercontent.com/swissairdry/swissairdry/main/install.sh | sudo bash -s -- --auto
```

## Schritt-für-Schritt-Installation

### 1. Repository klonen

```bash
sudo apt install -y git
git clone https://github.com/swissairdry/swissairdry.git
cd swissairdry
```

### 2. Installation starten

Interaktive Installation:

```bash
sudo bash install.sh
```

Folgen Sie den Anweisungen auf dem Bildschirm, um die Domain und andere Einstellungen zu konfigurieren.

### 3. SSL-Zertifikate einrichten

Für eine Produktionsumgebung empfehlen wir die Verwendung von Let's Encrypt:

```bash
sudo apt install -y certbot
sudo certbot certonly --standalone -d vgnc.org -d www.vgnc.org -d api.vgnc.org -d mqtt.vgnc.org
```

Kopieren Sie die Zertifikate:

```bash
sudo cp /etc/letsencrypt/live/vgnc.org/fullchain.pem ./ssl/certs/vgnc.org.cert.pem
sudo cp /etc/letsencrypt/live/vgnc.org/privkey.pem ./ssl/private/vgnc.org.key.pem
sudo chmod 644 ./ssl/certs/vgnc.org.cert.pem
sudo chmod 600 ./ssl/private/vgnc.org.key.pem
```

Starten Sie die Docker-Container neu:

```bash
docker compose restart
```

## Nextcloud-Integration

### Option 1: Bestehende Nextcloud verwenden

Wenn Sie bereits eine Nextcloud-Installation haben:

1. Installieren Sie die SwissAirDry-ExApp über den Nextcloud App Store
2. Konfigurieren Sie die ExApp für die Verbindung mit Ihrem SwissAirDry-API-Server:
   - Öffnen Sie die Nextcloud-Einstellungen
   - Navigieren Sie zu "SwissAirDry"
   - Geben Sie die API-URL ein: `https://api.vgnc.org`

### Option 2: Integrierte Nextcloud verwenden

Die SwissAirDry-Installation enthält eine eigene Nextcloud-Instanz:

1. Öffnen Sie `https://vgnc.org` in Ihrem Browser
2. Melden Sie sich mit dem Admin-Konto an (Standard: admin/admin)
3. Ändern Sie sofort das Standard-Passwort
4. Die SwissAirDry-ExApp ist bereits vorinstalliert und konfiguriert

## Automatischer Start bei Systemstart

Damit die Docker-Container automatisch beim Systemstart gestartet werden:

```bash
cd ~/swissairdry
cat << EOF | sudo tee /etc/systemd/system/swissairdry.service
[Unit]
Description=SwissAirDry Docker Stack
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/$(whoami)/swissairdry
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable swissairdry.service
sudo systemctl start swissairdry.service
```

## Verifizierung der Installation

Überprüfen Sie, ob alle Dienste korrekt laufen:

```bash
docker compose ps
```

Testen Sie den Zugriff auf die wichtigsten Endpunkte:

- API: `https://api.vgnc.org`
- Nextcloud: `https://vgnc.org`
- MQTT (mit einem MQTT-Client wie MQTT Explorer): `mqtt://vgnc.org:1883`

## Backup-Konfiguration

### Automatisches Datenbank-Backup

Erstellen Sie ein Backup-Skript:

```bash
cat << 'EOF' | sudo tee /usr/local/bin/swissairdry-backup.sh
#!/bin/bash
BACKUP_DIR="/var/backups/swissairdry"
DATE=$(date +%Y%m%d)
mkdir -p "$BACKUP_DIR"

# Docker Compose stoppen
cd /home/$(whoami)/swissairdry
docker compose stop db

# Datenbank-Backup erstellen
docker compose exec -T db pg_dump -U swissairdry -d swissairdry > "$BACKUP_DIR/swissairdry-db-$DATE.sql"

# Docker Compose wieder starten
docker compose start db

# Umgebungsvariablen sichern
cp /home/$(whoami)/swissairdry/.env "$BACKUP_DIR/env-$DATE.txt"

# Alte Backups löschen (älter als 14 Tage)
find "$BACKUP_DIR" -name "swissairdry-db-*.sql" -mtime +14 -delete
find "$BACKUP_DIR" -name "env-*.txt" -mtime +14 -delete

# Backup komprimieren
cd "$BACKUP_DIR"
tar -czf "swissairdry-backup-$DATE.tar.gz" "swissairdry-db-$DATE.sql" "env-$DATE.txt"
rm "swissairdry-db-$DATE.sql" "env-$DATE.txt"
EOF

sudo chmod +x /usr/local/bin/swissairdry-backup.sh
```

Fügen Sie einen Cron-Job für nächtliche Backups hinzu:

```bash
echo "0 2 * * * root /usr/local/bin/swissairdry-backup.sh" | sudo tee /etc/cron.d/swissairdry-backup
```

## System-Monitoring

Für ein einfaches System-Monitoring können Sie Netdata installieren:

```bash
bash <(curl -Ss https://get.netdata.cloud/kickstart.sh)
```

Greifen Sie dann auf das Monitoring-Dashboard zu: `http://server-ip:19999`

## Wartung und Updates

### Updates installieren

Um SwissAirDry zu aktualisieren:

```bash
cd ~/swissairdry
git pull
sudo bash install.sh --update
```

### System-Logs überprüfen

```bash
# API-Logs
docker compose logs api

# MQTT-Logs
docker compose logs mqtt

# Datenbank-Logs
docker compose logs db

# Alle Logs
docker compose logs
```

## Fehlersuche

Siehe [FEHLERBEHEBUNG.md](FEHLERBEHEBUNG.md) für detaillierte Informationen zur Behebung häufiger Probleme.

## Wiederherstellung

Um das System wiederherzustellen:

```bash
# Neueste Backup-Datei finden
BACKUP_FILE=$(ls -t /var/backups/swissairdry/swissairdry-backup-*.tar.gz | head -1)

# Backup extrahieren
mkdir -p /tmp/swissairdry-restore
tar -xzf "$BACKUP_FILE" -C /tmp/swissairdry-restore

# Konfiguration und Datenbank wiederherstellen
cp /tmp/swissairdry-restore/env-*.txt ~/swissairdry/.env
docker compose exec -T db psql -U swissairdry -d swissairdry < /tmp/swissairdry-restore/swissairdry-db-*.sql

# Aufräumen
rm -rf /tmp/swissairdry-restore
```

## Nächste Schritte

Nach der Installation sollten Sie:

1. Die Standardpasswörter ändern
2. Die MQTT-Sicherheit konfigurieren (optional)
3. ESP-Geräte einrichten und mit dem System verbinden
4. Benutzer und Kundenkonten anlegen

Weitere Informationen finden Sie in der [vollständigen Dokumentation](https://github.com/SwissAirDry/swissairdry).