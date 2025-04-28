#!/bin/bash

# SwissAirDry - Komplettes Installationsskript
# Dieses Skript richtet die komplette SwissAirDry Umgebung ein
# mit den vordefinierten Ports für Swisscom Router

set -e

echo "====================================================="
echo "SwissAirDry - Komplette Docker-Installation"
echo "====================================================="
echo ""

# Verzeichnisse erstellen
echo "1. Erstelle benötigte Verzeichnisse..."
mkdir -p nginx/conf.d nginx/ssl \
         mosquitto/config mosquitto/data mosquitto/log \
         nextcloud/config nextcloud/custom_apps \
         portainer/data

# Erstelle Docker-Compose-Datei
echo "2. Erstelle docker-compose.yml mit den korrekten Ports..."
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  # PostgreSQL Datenbank
  db:
    image: postgres:14-alpine
    container_name: swissairdry-db
    restart: unless-stopped
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: swissairdry
      POSTGRES_DB: swissairdry
    volumes:
      - db-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"  # PostgreSQL Port
    networks:
      - swissairdry-network
    
  # MQTT Broker
  mqtt:
    image: eclipse-mosquitto:2.0.18
    container_name: swissairdry-mqtt
    restart: unless-stopped
    ports:
      - "1883:1883"  # MQTT Port (Vorwärtsregel vorhanden)
      - "9001:9001"  # MQTT WebSocket Port
    volumes:
      - ./mosquitto/config:/mosquitto/config
      - ./mosquitto/data:/mosquitto/data
      - ./mosquitto/log:/mosquitto/log
    networks:
      - swissairdry-network
  
  # SwissAirDry Hauptanwendung (API)
  api:
    image: python:3.11-slim
    container_name: swissairdry-api
    restart: unless-stopped
    working_dir: /app
    command: >
      bash -c "apt-get update && apt-get install -y --no-install-recommends curl gcc libpq-dev python3-dev &&
               pip install fastapi uvicorn sqlalchemy pydantic psycopg2-binary paho-mqtt python-dotenv httpx jinja2 &&
               cd api/app && python -m uvicorn run2:app --host 0.0.0.0 --port 5000"
    ports:
      - "5000:5000"  # API Port (Vorwärtsregel vorhanden)
    environment:
      - DB_HOST=db
      - DB_USER=postgres
      - DB_PASSWORD=swissairdry
      - DB_NAME=swissairdry
      - MQTT_BROKER=mqtt
      - MQTT_PORT=1883
    volumes:
      - .:/app
    networks:
      - swissairdry-network
    depends_on:
      - db
      - mqtt
  
  # Simple API
  simple-api:
    image: python:3.11-slim
    container_name: swissairdry-simple-api
    restart: unless-stopped
    working_dir: /app
    command: >
      bash -c "pip install flask paho-mqtt python-dotenv requests &&
               cd swissairdry/api && python start_simple.py"
    environment:
      - MQTT_BROKER=mqtt
      - MQTT_PORT=1883
    volumes:
      - .:/app
    networks:
      - swissairdry-network
    depends_on:
      - mqtt

  # ExApp Server
  exapp:
    image: node:20-alpine
    container_name: swissairdry-exapp
    restart: unless-stopped
    working_dir: /app
    command: >
      sh -c "cd nextcloud/swissairdry-exapp && npm install && npm run serve"
    ports:
      - "3000:3000"  # ExApp Server Port (Vorwärtsregel vorhanden)
    volumes:
      - .:/app
    networks:
      - swissairdry-network
    depends_on:
      - api
  
  # ExApp Daemon
  exapp-daemon:
    image: node:20-alpine
    container_name: swissairdry-exapp-daemon
    restart: unless-stopped
    working_dir: /app
    command: >
      sh -c "cd nextcloud/swissairdry-exapp/daemon && npm install && node server.js"
    ports:
      - "8701:8701"  # ExApp Daemon Port
    environment:
      - API_URL=http://api:5000
      - MQTT_BROKER=mqtt
      - MQTT_PORT=1883
    volumes:
      - .:/app
    networks:
      - swissairdry-network
    depends_on:
      - api
      - mqtt
  
  # Portainer (Container-Management)
  portainer:
    image: portainer/portainer-ce:latest
    container_name: swissairdry-portainer
    restart: unless-stopped
    ports:
      - "9000:9000"  # Portainer Web Port (Vorwärtsregel vorhanden)
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./portainer/data:/data
    networks:
      - swissairdry-network
  
  # Nginx für Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: swissairdry-nginx
    restart: unless-stopped
    ports:
      - "80:80"     # HTTP Port (Vorwärtsregel vorhanden)
      - "443:443"   # HTTPS Port (Vorwärtsregel vorhanden)
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./nginx/ssl:/etc/nginx/ssl
    networks:
      - swissairdry-network
    depends_on:
      - api
      - simple-api
      - exapp

networks:
  swissairdry-network:
    driver: bridge

volumes:
  db-data:
EOF

# MQTT Konfiguration
echo "3. Erstelle MQTT Konfiguration..."
cat > mosquitto/config/mosquitto.conf << 'EOF'
# Grundlegende Konfiguration
listener 1883
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log

# WebSocket-Konfiguration
listener 9001
protocol websockets

# Logging
log_type error
log_type warning
log_type notice
log_type information
connection_messages true

# Sicherheit
allow_zero_length_clientid true
per_listener_settings false
EOF

# Nginx Konfiguration
echo "4. Erstelle Nginx Konfiguration..."
cat > nginx/conf.d/default.conf << 'EOF'
# Standard-Server für alle allgemeinen Anfragen
server {
    listen 80 default_server;
    server_name _;
    
    # Hauptanwendung API
    location / {
        proxy_pass http://api:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API Routen
    location /api/ {
        proxy_pass http://api:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # ExApp
    location /exapp/ {
        proxy_pass http://exapp:3000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # MQTT WebSocket
    location /mqtt/ {
        proxy_pass http://mqtt:9001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
    
    # Portainer
    location /portainer/ {
        proxy_pass http://portainer:9000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Große Datei-Uploads erlauben
    client_max_body_size 100M;
}

# Server-Konfiguration für vgnc.org
server {
    listen 80;
    server_name vgnc.org www.vgnc.org;
    
    # Hauptanwendung API
    location / {
        proxy_pass http://api:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Die restlichen Einstellungen sind die gleichen wie für den default_server
    location /api/ {
        proxy_pass http://api:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /exapp/ {
        proxy_pass http://exapp:3000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    location /mqtt/ {
        proxy_pass http://mqtt:9001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
    
    location /portainer/ {
        proxy_pass http://portainer:9000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    client_max_body_size 100M;
}

# Server-Konfiguration für api.vgnc.org
server {
    listen 80;
    server_name api.vgnc.org;
    
    # Alle Anfragen an die API weiterleiten
    location / {
        proxy_pass http://api:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    client_max_body_size 100M;
}

# Server-Konfiguration für talk.vgnc.org
server {
    listen 80;
    server_name talk.vgnc.org;
    
    # Alle Anfragen an die ExApp weiterleiten
    location / {
        proxy_pass http://exapp:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    client_max_body_size 100M;
}
EOF

# Erstelle Start-Skript
echo "5. Erstelle Start/Stop-Skripte..."
cat > start-swissairdry.sh << 'EOF'
#!/bin/bash
echo "Starte SwissAirDry Docker Container..."
docker-compose up -d
echo "Docker Container wurden gestartet!"
echo "SwissAirDry ist nun verfügbar unter:"
echo " - Hauptanwendung: http://localhost oder http://[Server-IP]"
echo " - API: http://localhost:5000 oder http://[Server-IP]:5000"
echo " - Portainer: http://localhost:9000 oder http://[Server-IP]:9000/portainer/"
EOF
chmod +x start-swissairdry.sh

cat > stop-swissairdry.sh << 'EOF'
#!/bin/bash
echo "Stoppe SwissAirDry Docker Container..."
docker-compose down
echo "Docker Container wurden gestoppt!"
EOF
chmod +x stop-swissairdry.sh

# Erstelle README mit Installationsanleitung
cat > README-INSTALLATION.md << 'EOF'
# SwissAirDry - Installationsanleitung

## Übersicht

Diese Anleitung erklärt die Installation und Konfiguration der SwissAirDry-Plattform mit Docker. Die Einrichtung ist für einfache Bedienung optimiert und berücksichtigt die konfigurierten Portweiterleitungen für den Zugriff von außen.

## Voraussetzungen

- Docker und Docker Compose installiert
- Port-Weiterleitungen im Router (siehe unten)
- Optional: Domain mit DNS-Einträgen

## Installierte Komponenten

1. **SwissAirDry API**: Hauptanwendung (Port 5000)
2. **Simple API**: Vereinfachte API für IoT-Geräte (Port 5001)
3. **MQTT Broker**: Mosquitto für Gerätekommunikation (Port 1883, WebSocket 9001)
4. **ExApp Server**: Node.js Anwendung (Port 3000)
5. **ExApp Daemon**: Hintergrundprozess für ExApp
6. **PostgreSQL**: Datenbank (Port 5432)
7. **Nginx**: Reverse Proxy für HTTP(S) (Port 80/443)
8. **Portainer**: Container-Management (Port 9000)

## Portkonfiguration

Die folgenden Ports werden verwendet und müssen in Ihrer Router-Konfiguration weitergeleitet werden:

| Port | Protokoll | Dienst | Beschreibung |
|------|-----------|--------|--------------|
| 22 | TCP | SSH | Sicherer Zugriff auf den Server |
| 80 | TCP | HTTP | Web-Zugriff |
| 443 | TCP | HTTPS | Sicherer Web-Zugriff |
| 1883 | TCP/UDP | MQTT | MQTT Broker |
| 3000 | TCP | ExApp | ExApp Server |
| 5000 | TCP | API | SwissAirDry API |
| 5432 | TCP/UDP | PostgreSQL | Datenbank |
| 8080 | TCP | Nextcloud | Nextcloud-Zugriff |
| 9000 | TCP | Portainer | Container-Management |

## Domain-Konfiguration

Das System unterstützt die Domain vgnc.org mit folgenden Subdomains:

- **vgnc.org / www.vgnc.org**: Hauptanwendung
- **api.vgnc.org**: API-Zugriff
- **talk.vgnc.org**: ExApp-Kommunikation

## Installationsschritte

1. Führen Sie das Installationsskript aus:
   ```bash
   chmod +x swissairdry-installer.sh
   ./swissairdry-installer.sh
   ```

2. Starten Sie die Container:
   ```bash
   ./start-swissairdry.sh
   ```

3. Zugriff auf die verschiedenen Dienste:
   - Hauptanwendung: http://localhost oder http://Ihre-IP
   - API: http://localhost:5000 oder http://Ihre-IP:5000
   - Portainer: http://localhost:9000 oder http://Ihre-IP:9000

4. Bei Verwendung einer Domain:
   - Hauptanwendung: http://vgnc.org oder http://www.vgnc.org
   - API: http://api.vgnc.org
   - ExApp: http://talk.vgnc.org

## Stoppen des Systems

Um das System zu stoppen, führen Sie aus:
```bash
./stop-swissairdry.sh
```

## Fehlerbehebung

Bei Problemen prüfen Sie:
1. Docker-Container-Status: `docker ps`
2. Container-Logs: `docker logs [container-name]`
3. Netzwerk-Konfiguration: `docker network inspect swissairdry-network`
4. Port-Freigaben: `netstat -tulpn | grep LISTEN`

## Kontakt und Support

Bei Fragen oder Problemen wenden Sie sich an das SwissAirDry-Team.
EOF

# Informationen anzeigen
echo "====================================================="
echo "Installation abgeschlossen!"
echo ""
echo "Um SwissAirDry zu starten, führen Sie aus:"
echo "./start-swissairdry.sh"
echo ""
echo "Um SwissAirDry zu stoppen, führen Sie aus:"
echo "./stop-swissairdry.sh"
echo ""
echo "Hinweis: Es werden folgende Ports verwendet (wie in den Portweiterleitungsregeln konfiguriert):"
echo " - 80/443: Web-Zugriff"
echo " - 1883: MQTT Broker"
echo " - 3000: ExApp Server"
echo " - 5000: SwissAirDry API"
echo " - 5432: PostgreSQL Datenbank"
echo " - 9000: Portainer"
echo ""
echo "Eine ausführliche Dokumentation finden Sie in der Datei README-INSTALLATION.md"
echo "====================================================="