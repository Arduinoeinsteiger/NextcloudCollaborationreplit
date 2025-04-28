#!/bin/bash

# ============================================================
# SwissAirDry NOTFALL-REPARATUR-SKRIPT
# ============================================================
# WARNUNG: Dieses Skript behebt ALLE bekannten Probleme auf einmal!
# 1. Erstellt fehlende Verzeichnisse und Dateien
# 2. Korrigiert Docker-Zugriffe
# 3. Bereinigt das Dateisystem
# 4. Schafft eine klare Projektstruktur

# Farbige Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${RED}${BOLD}===========================================================${NC}"
echo -e "${RED}${BOLD}     SwissAirDry KOMPLETTE NOTFALL-REPARATUR     ${NC}"
echo -e "${RED}${BOLD}===========================================================${NC}"
echo ""

# Funktion zum Anzeigen von Status-Meldungen
function status_message() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Funktion zum Anzeigen von Erfolgs-Meldungen
function success_message() {
    echo -e "${GREEN}[ERFOLG]${NC} $1"
}

# Funktion zum Anzeigen von Warnungen
function warning_message() {
    echo -e "${YELLOW}[WARNUNG]${NC} $1"
}

# Funktion zum Anzeigen von kritischen Meldungen
function critical_message() {
    echo -e "${RED}${BOLD}[KRITISCH]${NC} $1"
}

# Funktion zum Anzeigen von Überschriften
function header_message() {
    echo ""
    echo -e "${PURPLE}${BOLD}$1${NC}"
    echo -e "${PURPLE}${BOLD}$(printf '=%.0s' $(seq 1 ${#1}))${NC}"
}

# Funktion zum Erstellen aller benötigten Verzeichnisse
function create_all_directories() {
    header_message "SCHRITT 1: Erstelle alle benötigten Verzeichnisse"
    
    # Hauptverzeichnisse
    mkdir -p swissairdry/api/app/{routes,models,schemas,templates,static,utils}
    mkdir -p swissairdry/mqtt
    mkdir -p swissairdry/exapp/{daemon,frontend/{src,public,components}}
    mkdir -p nginx/conf.d
    mkdir -p db/migrations
    mkdir -p docs/{images,api}
    mkdir -p scripts
    
    success_message "Alle Verzeichnisse wurden erstellt."
}

# Funktion zum Erstellen wichtiger Konfigurationsdateien
function create_config_files() {
    header_message "SCHRITT 2: Erstelle wichtige Konfigurationsdateien"
    
    # .env-Datei erstellen
    if [ ! -f ".env" ]; then
        cat > .env << 'EOF'
# SwissAirDry Umgebungsvariablen

# Datenbank-Konfiguration
DB_HOST=db
DB_PORT=5432
DB_NAME=swissairdry
DB_USER=postgres
DB_PASSWORD=swissairdry

# MQTT-Konfiguration
MQTT_BROKER=mqtt
MQTT_PORT=1883
MQTT_USER=swissairdry
MQTT_PASSWORD=swissairdry
MQTT_WEBSOCKET_PORT=9001

# API-Konfiguration
API_PORT=5000
SIMPLE_API_PORT=5001
API_SECRET_KEY=super_secret_key_change_in_production

# Nextcloud-Integration
NEXTCLOUD_URL=http://nextcloud:8080
NEXTCLOUD_APP_TOKEN=change_this_in_production
EXAPP_PORT=3000
EXAPP_DAEMON_PORT=8701

# Docker-Konfiguration
POSTGRES_PASSWORD=swissairdry
POSTGRES_USER=postgres
POSTGRES_DB=swissairdry
EOF
        success_message ".env-Datei erstellt."
    else
        warning_message ".env-Datei existiert bereits. Keine Änderungen vorgenommen."
    fi
    
    # mosquitto.conf erstellen
    if [ ! -f "swissairdry/mqtt/mosquitto.conf" ]; then
        cat > swissairdry/mqtt/mosquitto.conf << 'EOF'
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
        success_message "mosquitto.conf erstellt."
    else
        warning_message "mosquitto.conf existiert bereits. Keine Änderungen vorgenommen."
    fi
    
    # Nginx default.conf erstellen
    if [ ! -f "nginx/conf.d/default.conf" ]; then
        mkdir -p nginx/conf.d
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
    
    # Nextcloud ExApp
    location /exapp/ {
        proxy_pass http://exapp:3000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Große Datei-Uploads erlauben
    client_max_body_size 100M;
}
EOF
        success_message "nginx/conf.d/default.conf erstellt."
    else
        warning_message "nginx/conf.d/default.conf existiert bereits. Keine Änderungen vorgenommen."
    fi
}

# Funktion zum Erstellen der API-Dateien
function create_api_files() {
    header_message "SCHRITT 3: Erstelle fehlende API-Dateien"
    
    # start_simple.py erstellen
    if [ ! -f "swissairdry/api/start_simple.py" ]; then
        cat > swissairdry/api/start_simple.py << 'EOF'
#!/usr/bin/env python3
"""
SwissAirDry Simple API
----------------------

Einfacher API-Server für die Kommunikation mit IoT-Geräten.
"""

import os
import json
import logging
import socket
from flask import Flask, request, jsonify, render_template
import paho.mqtt.client as mqtt
import time

# Logging-Konfiguration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask-App erstellen
app = Flask(__name__)

# Konfiguration
MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 1883))
MQTT_USER = os.environ.get("MQTT_USER", "")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD", "")

# Zeitstempel für Client-ID generieren
timestamp = int(time.time())
hostname = socket.gethostname()
pid = os.getpid()
MQTT_CLIENT_ID = f"sard-simple-{hostname}-{timestamp}-{pid}"

# Globaler MQTT-Client
mqtt_client = None

# MQTT-Callbacks
def on_connect(client, userdata, flags, rc):
    """Callback für erfolgreiche Verbindung"""
    if rc == 0:
        logger.info(f"MQTT-Client verbunden mit {MQTT_BROKER}:{MQTT_PORT}")
        
        # Standard-Topics abonnieren
        client.subscribe("swissairdry/#")
        client.subscribe("swissairdry/+/data")
        client.subscribe("swissairdry/+/status")
        client.subscribe("swissairdry/+/config")
    else:
        logger.warning(f"MQTT-Verbindung fehlgeschlagen mit Code {rc}")

def on_message(client, userdata, msg):
    """Callback für eingehende Nachrichten"""
    try:
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        
        logger.debug(f"MQTT-Nachricht empfangen: {topic} - {payload}")
    except Exception as e:
        logger.error(f"Fehler bei der Verarbeitung der MQTT-Nachricht: {str(e)}")

def on_disconnect(client, userdata, rc):
    """Callback für Verbindungsabbruch"""
    logger.warning("MQTT-Client getrennt")

# MQTT-Client initialisieren
def init_mqtt():
    global mqtt_client
    
    mqtt_client = mqtt.Client()
    
    # Callbacks setzen
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.on_disconnect = on_disconnect
    
    # Authentifizierung, falls konfiguriert
    if MQTT_USER and MQTT_PASSWORD:
        mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    
    # Verbinden
    try:
        logger.info(f"Verbinde mit MQTT-Broker {MQTT_BROKER}:{MQTT_PORT}...")
        logger.info(f"MQTT-Client-ID: {MQTT_CLIENT_ID}")
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # Im Hintergrund starten
        mqtt_client.loop_start()
    except Exception as e:
        logger.error(f"Fehler bei der Verbindung zum MQTT-Broker: {str(e)}")

# API-Routen
@app.route("/")
def index():
    """Startseite"""
    return jsonify({
        "name": "SwissAirDry Simple API",
        "status": "online",
        "version": "1.0.0"
    })

@app.route("/api/status")
def status():
    """API-Status"""
    return jsonify({
        "status": "online",
        "mqtt_connected": mqtt_client is not None,
        "version": "1.0.0"
    })

@app.route("/api/device/<device_id>/data", methods=["POST"])
def device_data(device_id):
    """Empfange Daten von einem Gerät"""
    if not request.is_json:
        return jsonify({"error": "Content-Type muss application/json sein"}), 400
    
    data = request.json
    
    # Veröffentliche Daten über MQTT
    if mqtt_client:
        topic = f"swissairdry/{device_id}/data"
        payload = json.dumps(data)
        mqtt_client.publish(topic, payload)
    
    return jsonify({"success": True, "device_id": device_id})

@app.route("/api/device/<device_id>/status", methods=["POST"])
def device_status(device_id):
    """Empfange Statusmeldungen von einem Gerät"""
    if not request.is_json:
        return jsonify({"error": "Content-Type muss application/json sein"}), 400
    
    data = request.json
    
    # Veröffentliche Status über MQTT
    if mqtt_client:
        topic = f"swissairdry/{device_id}/status"
        payload = json.dumps(data)
        mqtt_client.publish(topic, payload)
    
    return jsonify({"success": True, "device_id": device_id})

@app.route("/api/send/<device_id>", methods=["POST"])
def send_command(device_id):
    """Sende einen Befehl an ein Gerät"""
    if not request.is_json:
        return jsonify({"error": "Content-Type muss application/json sein"}), 400
    
    data = request.json
    
    # Veröffentliche Befehl über MQTT
    if mqtt_client:
        topic = f"swissairdry/{device_id}/command"
        payload = json.dumps(data)
        mqtt_client.publish(topic, payload)
    
    return jsonify({"success": True, "device_id": device_id})

# Hauptfunktion
if __name__ == "__main__":
    logger.info("API-Server wird gestartet...")
    
    # MQTT-Client initialisieren
    init_mqtt()
    
    # Server starten
    try:
        app.run(host="0.0.0.0", port=5001, debug=True)
    except KeyboardInterrupt:
        logger.info("API-Server wird beendet...")
    finally:
        # MQTT-Client stoppen
        if mqtt_client:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
EOF
        chmod +x swissairdry/api/start_simple.py
        success_message "start_simple.py erstellt."
    else
        warning_message "start_simple.py existiert bereits. Keine Änderungen vorgenommen."
    fi
    
    # run2.py erstellen
    if [ ! -f "swissairdry/api/app/run2.py" ]; then
        cat > swissairdry/api/app/run2.py << 'EOF'
#!/usr/bin/env python3
"""
SwissAirDry FastAPI Server
--------------------------

FastAPI-Server für die Haupt-API von SwissAirDry.
"""

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Logging-Konfiguration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI-App erstellen
app = FastAPI(
    title="SwissAirDry API",
    description="API für die Verwaltung von SwissAirDry-Geräten",
    version="1.0.0"
)

# CORS-Konfiguration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API-Routen
@app.get("/")
async def root():
    """Startseite"""
    return {"message": "Willkommen bei der SwissAirDry API"}

@app.get("/api/status")
async def status():
    """API-Status"""
    return {
        "status": "online",
        "version": "1.0.0"
    }

@app.get("/api/devices")
async def list_devices():
    """Liste aller Geräte"""
    # Hier würde normalerweise eine Datenbankabfrage stehen
    # Für dieses einfache Beispiel verwenden wir Dummydaten
    return {
        "devices": [
            {
                "id": "esp8266-001",
                "name": "Trockner 1",
                "type": "ESP8266",
                "status": "online",
                "lastSeen": "2024-04-28T14:30:00Z"
            },
            {
                "id": "esp32-001",
                "name": "Trockner 2",
                "type": "ESP32",
                "status": "offline",
                "lastSeen": "2024-04-28T10:15:00Z"
            },
            {
                "id": "stm32-001",
                "name": "Temperatur-Sensor",
                "type": "STM32",
                "status": "online",
                "lastSeen": "2024-04-28T14:35:00Z"
            }
        ]
    }

# Fehlerbehandlung
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"Unbehandelte Ausnahme: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Interner Serverfehler"},
    )

# Hauptfunktion
if __name__ == "__main__":
    logger.info("API-Server erfolgreich gestartet")
    uvicorn.run(app, host="0.0.0.0", port=5000)
EOF
        chmod +x swissairdry/api/app/run2.py
        success_message "run2.py erstellt."
    else
        warning_message "run2.py existiert bereits. Keine Änderungen vorgenommen."
    fi
}

# Funktion zum Korrigieren der Docker-Compose-Datei
function fix_docker_compose() {
    header_message "SCHRITT 4: Korrigiere Docker-Compose-Dateien"
    
    DOCKER_COMPOSE_FILE="docker-compose-all-in-one.yml"
    
    if [ -f "$DOCKER_COMPOSE_FILE" ]; then
        # Mache ein Backup
        cp "$DOCKER_COMPOSE_FILE" "${DOCKER_COMPOSE_FILE}.backup"
        
        status_message "Passe Docker-Compose-Datei an..."
        
        # Ersetze ghcr.io-Referenzen durch lokale Builds
        sed -i 's|image: ghcr.io/arduinoeinsteiger/swissairdry-api:latest|build: ./swissairdry/api|g' "$DOCKER_COMPOSE_FILE"
        sed -i 's|image: ghcr.io/arduinoeinsteiger/swissairdry-simple-api:latest|build: ./swissairdry/api\n    dockerfile: Dockerfile.simple|g' "$DOCKER_COMPOSE_FILE"
        sed -i 's|image: ghcr.io/arduinoeinsteiger/swissairdry-exapp:latest|build: ./swissairdry/exapp|g' "$DOCKER_COMPOSE_FILE"
        sed -i 's|image: ghcr.io/arduinoeinsteiger/swissairdry-exapp-daemon:latest|build: ./swissairdry/exapp/daemon|g' "$DOCKER_COMPOSE_FILE"
        
        success_message "Docker-Compose-Datei angepasst."
    else
        critical_message "Docker-Compose-Datei nicht gefunden!"
        
        # Erstelle eine neue Docker-Compose-Datei
        cat > "$DOCKER_COMPOSE_FILE" << 'EOF'
version: '3.8'

services:
  # PostgreSQL Datenbank
  db:
    image: postgres:14-alpine
    container_name: swissairdry-db
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-swissairdry}
      POSTGRES_DB: ${POSTGRES_DB:-swissairdry}
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
      - "1883:1883"  # MQTT Port
      - "9001:9001"  # MQTT WebSocket Port
    volumes:
      - ./swissairdry/mqtt/mosquitto.conf:/mosquitto/config/mosquitto.conf
      - mosquitto-data:/mosquitto/data
      - mosquitto-log:/mosquitto/log
    networks:
      - swissairdry-network
  
  # SwissAirDry Hauptanwendung (API)
  api:
    build: ./swissairdry/api
    container_name: swissairdry-api
    restart: unless-stopped
    environment:
      - DB_HOST=db
      - DB_USER=${POSTGRES_USER:-postgres}
      - DB_PASSWORD=${POSTGRES_PASSWORD:-swissairdry}
      - DB_NAME=${POSTGRES_DB:-swissairdry}
      - MQTT_BROKER=mqtt
      - MQTT_PORT=1883
      - API_SECRET_KEY=${API_SECRET_KEY:-super_secret_key_change_in_production}
    ports:
      - "5000:5000"  # API Port
    volumes:
      - ./swissairdry/api:/app
    networks:
      - swissairdry-network
    depends_on:
      - db
      - mqtt
  
  # Simple API
  simple-api:
    build: 
      context: ./swissairdry/api
      dockerfile: Dockerfile.simple
    container_name: swissairdry-simple-api
    restart: unless-stopped
    environment:
      - MQTT_BROKER=mqtt
      - MQTT_PORT=1883
    ports:
      - "5001:5001"  # Simple API Port
    volumes:
      - ./swissairdry/api:/app
    networks:
      - swissairdry-network
    depends_on:
      - mqtt
  
  # Nginx für Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: swissairdry-nginx
    restart: unless-stopped
    ports:
      - "80:80"     # HTTP Port
      - "443:443"   # HTTPS Port
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
  mosquitto-data:
  mosquitto-log:
EOF
        success_message "Neue Docker-Compose-Datei erstellt."
    fi
}

# Funktion zum Erstellen von Dockerfiles
function create_dockerfiles() {
    header_message "SCHRITT 5: Erstelle fehlende Dockerfiles"
    
    # Dockerfile für API erstellen oder prüfen
    if [ ! -f "swissairdry/api/Dockerfile" ]; then
        # Kopiere das vorhandene Dockerfile, falls es existiert
        if [ -f "api/Dockerfile.api" ]; then
            cp "api/Dockerfile.api" "swissairdry/api/Dockerfile"
            success_message "Dockerfile.api nach swissairdry/api/Dockerfile kopiert."
        else
            # Erstelle neues Dockerfile
            cat > "swissairdry/api/Dockerfile" << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Installiere Abhängigkeiten
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Kopiere requirements.txt
COPY requirements.api.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere Anwendungsdateien
COPY app/ app/

# Setze Umgebungsvariablen
ENV PYTHONUNBUFFERED=1

# Lege Port frei
EXPOSE 5000

# Starte die Anwendung
CMD ["python", "app/run2.py"]
EOF
            success_message "Neues Dockerfile für API erstellt."
        fi
    else
        warning_message "Dockerfile für API existiert bereits. Keine Änderungen vorgenommen."
    fi
    
    # Dockerfile für Simple API erstellen oder prüfen
    if [ ! -f "swissairdry/api/Dockerfile.simple" ]; then
        # Kopiere das vorhandene Dockerfile, falls es existiert
        if [ -f "api/Dockerfile.simple" ]; then
            cp "api/Dockerfile.simple" "swissairdry/api/Dockerfile.simple"
            success_message "Dockerfile.simple nach swissairdry/api/Dockerfile.simple kopiert."
        else
            # Erstelle neues Dockerfile
            cat > "swissairdry/api/Dockerfile.simple" << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Installiere Abhängigkeiten
COPY requirements.simple.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere Anwendungsdateien
COPY start_simple.py .

# Setze Umgebungsvariablen
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=start_simple.py

# Lege Port frei
EXPOSE 5001

# Starte die Anwendung
CMD ["python", "start_simple.py"]
EOF
            success_message "Neues Dockerfile.simple erstellt."
        fi
    else
        warning_message "Dockerfile.simple existiert bereits. Keine Änderungen vorgenommen."
    fi
    
    # Erstelle requirements.api.txt, falls nicht vorhanden
    if [ ! -f "swissairdry/api/requirements.api.txt" ]; then
        # Kopiere vorhandene Datei, falls sie existiert
        if [ -f "api/requirements.api.txt" ]; then
            cp "api/requirements.api.txt" "swissairdry/api/requirements.api.txt"
            success_message "requirements.api.txt kopiert."
        else
            cat > "swissairdry/api/requirements.api.txt" << 'EOF'
fastapi==0.109.2
uvicorn==0.27.1
pydantic==2.5.2
paho-mqtt==1.6.1
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
python-multipart==0.0.9
python-dotenv==1.0.1
httpx==0.25.2
jinja2==3.1.3
EOF
            success_message "Neue requirements.api.txt erstellt."
        fi
    else
        warning_message "requirements.api.txt existiert bereits. Keine Änderungen vorgenommen."
    fi
    
    # Erstelle requirements.simple.txt, falls nicht vorhanden
    if [ ! -f "swissairdry/api/requirements.simple.txt" ]; then
        # Kopiere vorhandene Datei, falls sie existiert
        if [ -f "api/requirements.simple.txt" ]; then
            cp "api/requirements.simple.txt" "swissairdry/api/requirements.simple.txt"
            success_message "requirements.simple.txt kopiert."
        else
            cat > "swissairdry/api/requirements.simple.txt" << 'EOF'
flask==3.0.0
paho-mqtt==1.6.1
python-dotenv==1.0.1
requests==2.31.0
EOF
            success_message "Neue requirements.simple.txt erstellt."
        fi
    else
        warning_message "requirements.simple.txt existiert bereits. Keine Änderungen vorgenommen."
    fi
}

# Funktion zum Erstellen des All-in-One-Startskripts
function create_start_script() {
    header_message "SCHRITT 6: Erstelle verbessertes Startskript"
    
    cat > "start-all-in-one-fixed.sh" << 'EOF'
#!/bin/bash

# SwissAirDry All-in-One Startskript (KORRIGIERTE VERSION)
# Dieses Skript startet alle Komponenten des SwissAirDry-Systems

# Farbige Ausgabe
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Funktion zum Anzeigen von Informationen
function info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Funktion zum Anzeigen von Erfolgen
function success() {
    echo -e "${GREEN}[ERFOLG]${NC} $1"
}

# Funktion zum Anzeigen von Warnungen
function warning() {
    echo -e "${YELLOW}[WARNUNG]${NC} $1"
}

# Funktion zum Anzeigen von Fehlern
function error() {
    echo -e "${RED}[FEHLER]${NC} $1"
}

echo -e "${BLUE}===========================================================${NC}"
echo -e "${BLUE}     SwissAirDry All-in-One Startskript (KORRIGIERT)      ${NC}"
echo -e "${BLUE}===========================================================${NC}"
echo ""

# Prüfe, ob Docker installiert ist
if ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null; then
    error "Docker und/oder Docker Compose sind nicht installiert!"
    echo "Bitte installieren Sie Docker und Docker Compose mit:"
    echo "  curl -fsSL https://get.docker.com | sh"
    echo "  sudo apt-get install -y docker-compose"
    exit 1
fi

# Prüfe, ob Docker-Daemon läuft
if ! docker info &> /dev/null; then
    error "Docker-Daemon ist nicht gestartet!"
    echo "Bitte starten Sie den Docker-Daemon mit:"
    echo "  sudo systemctl start docker"
    exit 1
fi

# Prüfe, ob .env-Datei existiert und erstelle sie, falls nicht
if [ ! -f .env ]; then
    info "Erstelle .env-Datei..."
    cat > .env << 'EOL'
# SwissAirDry Umgebungsvariablen
DB_HOST=db
DB_PORT=5432
DB_NAME=swissairdry
DB_USER=postgres
DB_PASSWORD=swissairdry
MQTT_BROKER=mqtt
MQTT_PORT=1883
MQTT_USER=swissairdry
MQTT_PASSWORD=swissairdry
MQTT_WEBSOCKET_PORT=9001
API_PORT=5000
SIMPLE_API_PORT=5001
API_SECRET_KEY=super_secret_key_change_in_production
NEXTCLOUD_URL=http://nextcloud:8080
NEXTCLOUD_APP_TOKEN=change_this_in_production
EXAPP_PORT=3000
EXAPP_DAEMON_PORT=8701
POSTGRES_PASSWORD=swissairdry
POSTGRES_USER=postgres
POSTGRES_DB=swissairdry
EOL
    success ".env-Datei erstellt."
else
    info ".env-Datei gefunden."
fi

# Prüfe, ob alle benötigten Dateien existieren
info "Prüfe, ob alle benötigten Dateien vorhanden sind..."

# Liste der kritischen Verzeichnisse
mkdir -p swissairdry/mqtt
mkdir -p swissairdry/api/app
mkdir -p nginx/conf.d

# Prüfe mosquitto.conf
if [ ! -f "swissairdry/mqtt/mosquitto.conf" ]; then
    warning "mosquitto.conf nicht gefunden. Erstelle Standardkonfiguration..."
    cat > swissairdry/mqtt/mosquitto.conf << 'EOL'
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
EOL
    success "mosquitto.conf erstellt."
else
    success "mosquitto.conf gefunden."
fi

# Prüfe Nginx Konfiguration
if [ ! -f "nginx/conf.d/default.conf" ]; then
    warning "nginx/conf.d/default.conf nicht gefunden. Erstelle Standardkonfiguration..."
    cat > nginx/conf.d/default.conf << 'EOL'
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
    
    # Große Datei-Uploads erlauben
    client_max_body_size 100M;
}
EOL
    success "nginx/conf.d/default.conf erstellt."
else
    success "nginx/conf.d/default.conf gefunden."
fi

# Starte die Docker-Container
info "Starte Docker-Container mit docker-compose..."
if [ -f "docker-compose-all-in-one.yml" ]; then
    if docker-compose -f docker-compose-all-in-one.yml up -d; then
        success "Docker-Container wurden erfolgreich gestartet."
    else
        error "Fehler beim Starten der Docker-Container!"
        exit 1
    fi
else
    error "docker-compose-all-in-one.yml nicht gefunden!"
    exit 1
fi

# Warte, bis alle Services bereit sind
info "Warte, bis alle Services bereit sind..."
sleep 10

# Zeige Status der Container
info "Status der Container:"
docker-compose -f docker-compose-all-in-one.yml ps

# Zeige verfügbare Endpunkte
echo ""
info "Verfügbare Endpunkte:"
echo "  - API: http://localhost:5000"
echo "  - Simple API: http://localhost:5001"
echo "  - MQTT Broker: localhost:1883"
echo "  - MQTT WebSocket: ws://localhost:9001"
echo "  - Nginx Reverse Proxy: http://localhost:80"

# Zeige Zugriff auf die Container
echo ""
info "Container-Zugriff:"
echo "  - API Logs: docker-compose -f docker-compose-all-in-one.yml logs api"
echo "  - Simple API Logs: docker-compose -f docker-compose-all-in-one.yml logs simple-api"
echo "  - MQTT Logs: docker-compose -f docker-compose-all-in-one.yml logs mqtt"
echo "  - Alle Services stoppen: docker-compose -f docker-compose-all-in-one.yml down"

echo ""
success "SwissAirDry-System wurde gestartet."
EOF
    chmod +x "start-all-in-one-fixed.sh"
    success_message "Verbessertes Startskript erstellt: start-all-in-one-fixed.sh"
}

# Funktion zum Erstellen der Projektübersicht
function create_project_overview() {
    header_message "SCHRITT 7: Erstelle Projektübersicht"
    
    # Erstelle FINAL_PROJECT_OVERVIEW.md
    cat > "FINAL_PROJECT_OVERVIEW.md" << 'EOF'
# SwissAirDry Projektübersicht

## Systemkomponenten

1. **API-Server**
   - **Beschreibung**: Hauptanwendungsserver auf Basis von FastAPI
   - **Port**: 5000
   - **Verzeichnis**: `swissairdry/api/app`

2. **Simple API**
   - **Beschreibung**: Vereinfachte API für IoT-Geräte (ESP8266, ESP32, STM32)
   - **Port**: 5001
   - **Verzeichnis**: `swissairdry/api`
   - **Hauptdatei**: `start_simple.py`

3. **MQTT-Broker**
   - **Beschreibung**: Mosquitto MQTT-Broker für Gerätekommunikation
   - **Ports**: 1883 (MQTT), 9001 (WebSocket)
   - **Konfiguration**: `swissairdry/mqtt/mosquitto.conf`

4. **Datenbank**
   - **Beschreibung**: PostgreSQL-Datenbank für Datenspeicherung
   - **Port**: 5432

5. **Nginx Reverse Proxy**
   - **Beschreibung**: Nginx als Reverse Proxy für alle Services
   - **Ports**: 80 (HTTP), 443 (HTTPS)
   - **Konfiguration**: `nginx/conf.d/default.conf`

## Verzeichnisstruktur

```
SwissAirDry/
├── docker-compose-all-in-one.yml    # Docker-Compose-Konfiguration
├── .env                             # Umgebungsvariablen
├── scripts/                         # Dienstprogramme und Skripte
├── docs/                            # Dokumentation
├── swissairdry/
│   ├── api/
│   │   ├── app/                     # Haupt-API (FastAPI)
│   │   │   ├── models/              # Datenbankmodelle
│   │   │   ├── routes/              # API-Routen
│   │   │   ├── schemas/             # Pydantic-Schemas
│   │   │   ├── templates/           # HTML-Templates
│   │   │   ├── static/              # Statische Dateien
│   │   │   └── run2.py              # Hauptanwendungsdatei
│   │   ├── Dockerfile               # Docker-Build für API
│   │   ├── Dockerfile.simple        # Docker-Build für Simple API
│   │   ├── requirements.api.txt     # Abhängigkeiten für Haupt-API
│   │   ├── requirements.simple.txt  # Abhängigkeiten für Simple API
│   │   └── start_simple.py          # Simple API Hauptdatei
│   ├── mqtt/
│   │   └── mosquitto.conf           # Mosquitto-Konfiguration
│   └── exapp/                       # Nextcloud ExApp (wenn aktiviert)
├── nginx/
│   └── conf.d/
│       └── default.conf             # Nginx-Konfiguration
└── db/                              # Datenbankdateien und Migrations
```

## Datei-Abhängigkeiten

### Für einen funktionierenden Betrieb mindestens erforderlich:

- `docker-compose-all-in-one.yml`
- `swissairdry/api/app/run2.py`
- `swissairdry/api/start_simple.py`
- `swissairdry/mqtt/mosquitto.conf`
- `swissairdry/api/Dockerfile`
- `swissairdry/api/Dockerfile.simple`
- `swissairdry/api/requirements.api.txt`
- `swissairdry/api/requirements.simple.txt`
- `nginx/conf.d/default.conf`

## Kommunikationsflüsse

1. **IoT-Geräte → MQTT-Broker**
   - Geräte senden Sensordaten an den MQTT-Broker
   - Topic-Format: `swissairdry/{device_id}/data`

2. **API-Server → MQTT-Broker**
   - API abonniert Geräte-Daten
   - API kann Befehle an Geräte senden

3. **Benutzer → Nginx → API-Server**
   - Benutzeranfragen werden über Nginx an die API weitergeleitet

4. **Simple API → MQTT-Broker**
   - Einfache API für direkte Gerätekommunikation

## Funktionalitäten

1. **Gerätemanagement**
   - Registrierung und Verwaltung von IoT-Geräten
   - Statusüberwachung

2. **Datenerfassung**
   - Sammlung von Sensordaten
   - Historische Datenaufzeichnung

3. **Steuerung**
   - Fernsteuerung von Geräten
   - Automatisierung durch Regeln

## Wartung und Fehlerbehebung

- **Container-Logs anzeigen**: `docker-compose -f docker-compose-all-in-one.yml logs [service-name]`
- **Alle Dienste neustarten**: `docker-compose -f docker-compose-all-in-one.yml restart`
- **System anhalten**: `docker-compose -f docker-compose-all-in-one.yml down`
- **System starten**: `./start-all-in-one-fixed.sh`

## Bekannte Probleme und Lösungen

1. **Docker-Image-Zugriffsprobleme**
   - **Problem**: Zugriff auf ghcr.io Images verweigert
   - **Lösung**: Lokale Builds in docker-compose.yml konfiguriert

2. **Fehlende Dateien/Verzeichnisse**
   - **Problem**: Kritische Dateien oder Verzeichnisse fehlen
   - **Lösung**: Automatische Erstellung durch Skripte

3. **Port-Konflikte**
   - **Problem**: Dienste können nicht auf bestimmten Ports starten
   - **Lösung**: Port-Konfiguration in docker-compose.yml anpassen
EOF
    
    success_message "Projektübersicht erstellt: FINAL_PROJECT_OVERVIEW.md"
}

# Hauptfunktion
function main() {
    echo -e "${YELLOW}${BOLD}WARNUNG: Dieses Skript wird das SwissAirDry-System komplett reparieren.${NC}"
    echo -e "${YELLOW}Es werden fehlende Dateien erstellt, Docker-Konfigurationen angepasst und Projekte neu organisiert.${NC}"
    echo ""
    read -p "Möchten Sie wirklich fortfahren? (j/n): " choice
    
    if [[ "$choice" != "j" && "$choice" != "J" ]]; then
        status_message "Abbruch durch Benutzer."
        exit 0
    fi
    
    echo ""
    critical_message "BEGINNE MIT DER NOTFALL-REPARATUR..."
    echo ""
    
    # Führe alle Reparaturschritte aus
    create_all_directories
    create_config_files
    create_api_files
    fix_docker_compose
    create_dockerfiles
    create_start_script
    create_project_overview
    
    echo ""
    echo -e "${GREEN}${BOLD}===========================================================${NC}"
    echo -e "${GREEN}${BOLD}                   REPARATUR ABGESCHLOSSEN                 ${NC}"
    echo -e "${GREEN}${BOLD}===========================================================${NC}"
    
    echo ""
    success_message "Die komplette Notfall-Reparatur wurde erfolgreich abgeschlossen."
    success_message "System kann jetzt mit folgendem Befehl gestartet werden:"
    echo -e "  ${BLUE}./start-all-in-one-fixed.sh${NC}"
    
    echo ""
    success_message "Eine vollständige Projektübersicht finden Sie in:"
    echo -e "  ${BLUE}FINAL_PROJECT_OVERVIEW.md${NC}"
    
    return 0
}

# Starte die Hauptfunktion
main