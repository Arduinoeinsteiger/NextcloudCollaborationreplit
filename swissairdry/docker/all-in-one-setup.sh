#!/bin/bash

# SwissAirDry - All-in-One Installationsscript
# Dieses Skript richtet alle Docker-Container für SwissAirDry ein

set -e

echo "====================================================="
echo "SwissAirDry - All-in-One Docker Installationsscript"
echo "====================================================="
echo ""

# Verzeichnisse erstellen
echo "1. Erstelle benötigte Verzeichnisse..."
mkdir -p nginx/conf.d nginx/ssl mosquitto/config mosquitto/data mosquitto/log

# Docker-Netzwerk erstellen
echo "2. Erstelle Docker-Netzwerk..."
docker network create swissairdry-network 2>/dev/null || echo "Netzwerk existiert bereits"

# Konfigurationsdateien erstellen
echo "3. Erstelle Konfigurationsdateien..."

# Nginx-Konfiguration
cat > nginx/conf.d/default.conf << 'EOF'
server {
    listen 80;
    server_name _;
    
    # Weiterleitungen für die Hauptanwendung
    location / {
        proxy_pass http://api:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API Routen
    location /api/ {
        proxy_pass http://api:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket Unterstützung
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Simple API Routen
    location /simple-api/ {
        rewrite ^/simple-api(/.*)$ $1 break;
        proxy_pass http://simple-api:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket für MQTT
    location /mqtt/ {
        proxy_pass http://mqtt:9001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # WebSocket Unterstützung
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
    
    # Konfiguration für große Dateiuploads
    client_max_body_size 20M;
    
    # Zugriff auf bestimmte Dateien verhindern
    location ~ /\.ht {
        deny all;
    }
}
EOF

# MQTT-Konfiguration
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

# .env-Datei
cat > .env << 'EOF'
# Datenbank
DB_USER=postgres
DB_PASSWORD=swissairdry
DB_NAME=swissairdry

# Ports
API_PORT=5000
SIMPLE_API_PORT=5001
MQTT_PORT=1883
MQTT_WS_PORT=9001
PORTAINER_PORT=9000

# MQTT
MQTT_ALLOW_ANONYMOUS=true
MQTT_CLIENT_ID=swissairdry-server

# Docker-Registry
REGISTRY_URL=ghcr.io/arduinoeinsteiger
IMAGE_TAG=latest
EOF

# Docker-Compose-Datei erstellen
echo "4. Erstelle docker-compose.yml..."
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  # PostgreSQL Datenbank
  db:
    image: postgres:14-alpine
    container_name: swissairdry-db
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-swissairdry}
      POSTGRES_DB: ${DB_NAME:-swissairdry}
    volumes:
      - db-data:/var/lib/postgresql/data
    networks:
      - swissairdry-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-postgres}"]
      interval: 10s
      timeout: 5s
      retries: 5
    
  # MQTT Broker
  mqtt:
    image: eclipse-mosquitto:2.0
    container_name: swissairdry-mqtt
    restart: unless-stopped
    ports:
      - "${MQTT_PORT:-1883}:1883"
      - "${MQTT_WS_PORT:-9001}:9001"
    volumes:
      - ./mosquitto/config:/mosquitto/config
      - ./mosquitto/data:/mosquitto/data
      - ./mosquitto/log:/mosquitto/log
    networks:
      - swissairdry-network
  
  # Main API (FastAPI)
  api:
    image: python:3.11-slim
    container_name: swissairdry-api
    restart: unless-stopped
    working_dir: /app
    command: >
      bash -c "pip install --no-cache-dir -r requirements.api.txt &&
               uvicorn app.run2:app --host 0.0.0.0 --port 5000 --reload"
    ports:
      - "${API_PORT:-5000}:5000"
    environment:
      - API_HOST=0.0.0.0
      - API_PORT=5000
      - DB_HOST=db
      - DB_USER=${DB_USER:-postgres}
      - DB_PASSWORD=${DB_PASSWORD:-swissairdry}
      - DB_NAME=${DB_NAME:-swissairdry}
      - MQTT_BROKER=mqtt
      - MQTT_PORT=${MQTT_PORT:-1883}
    volumes:
      - ./api:/app
    networks:
      - swissairdry-network
    depends_on:
      - db
      - mqtt
  
  # Simple API (Flask)
  simple-api:
    image: python:3.11-slim
    container_name: swissairdry-simple-api
    restart: unless-stopped
    working_dir: /app
    command: >
      bash -c "pip install --no-cache-dir -r requirements.simple.txt &&
               cd app && python start_simple.py"
    ports:
      - "${SIMPLE_API_PORT:-5001}:5001"
    environment:
      - API_HOST=0.0.0.0
      - API_PORT=5001
      - MQTT_BROKER=mqtt
      - MQTT_PORT=${MQTT_PORT:-1883}
      - MQTT_CLIENT_ID=${MQTT_CLIENT_ID:-swissairdry-simple-api}
    volumes:
      - ./api:/app
    networks:
      - swissairdry-network
    depends_on:
      - mqtt

  # Nginx Web Server
  nginx:
    image: nginx:alpine
    container_name: swissairdry-nginx
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./nginx/ssl:/etc/nginx/ssl
    networks:
      - swissairdry-network
    depends_on:
      - api
      - simple-api

networks:
  swissairdry-network:
    driver: bridge

volumes:
  db-data:
EOF

# Prüfe API Verzeichnis
echo "5. Prüfe API Verzeichnis und erstelle requirements.txt wenn nötig..."

if [ ! -d "api" ]; then
  echo "API Verzeichnis nicht gefunden. Erstelle es..."
  mkdir -p api/app
fi

if [ ! -f "api/requirements.api.txt" ]; then
  echo "requirements.api.txt nicht gefunden. Erstelle Standardversion..."
  cat > api/requirements.api.txt << 'EOF'
fastapi>=0.100.0
uvicorn>=0.23.0
sqlalchemy>=2.0.0
pydantic>=2.0.0
psycopg2-binary>=2.9.0
paho-mqtt>=2.2.0
python-dotenv>=1.0.0
httpx>=0.24.0
jinja2>=3.1.0
starlette>=0.30.0
pytest>=7.3.0
pytest-asyncio>=0.21.0
EOF
fi

if [ ! -f "api/requirements.simple.txt" ]; then
  echo "requirements.simple.txt nicht gefunden. Erstelle Standardversion..."
  cat > api/requirements.simple.txt << 'EOF'
flask>=2.3.0
paho-mqtt>=2.2.0
python-dotenv>=1.0.0
requests>=2.31.0
EOF
fi

# Start-Skript
cat > start.sh << 'EOF'
#!/bin/bash
echo "Starte SwissAirDry Docker Container..."
docker-compose up -d
echo "Container gestartet!"
EOF
chmod +x start.sh

# Stop-Skript
cat > stop.sh << 'EOF'
#!/bin/bash
echo "Stoppe SwissAirDry Docker Container..."
docker-compose down
echo "Container gestoppt!"
EOF
chmod +x stop.sh

echo "6. Installation abgeschlossen!"
echo ""
echo "Verwendung:"
echo " - Start der Container: ./start.sh"
echo " - Stopp der Container: ./stop.sh"
echo ""
echo "Zugriff auf die Anwendung:"
echo " - API: http://localhost:5000"
echo " - Simple API: http://localhost:5001"
echo " - Web-Interface über Nginx: http://localhost"
echo ""
echo "====================================================="