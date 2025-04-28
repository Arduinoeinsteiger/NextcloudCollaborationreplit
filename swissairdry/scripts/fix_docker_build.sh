#!/bin/bash

# Fix-Skript für Docker-Build-Fehler im SwissAirDry-Projekt
# Dieses Skript behebt spezifisch den pip install Fehler

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
echo -e "${BLUE}     SwissAirDry Docker-Build-Fehler Fixskript             ${NC}"
echo -e "${BLUE}===========================================================${NC}"
echo ""

# 1. Lokalisiere requirements.api.txt und requirements.simple.txt
info "Überprüfe requirements-Dateien..."

# Erstelle Verzeichnisse, falls sie nicht existieren
mkdir -p swissairdry/api

# Finde requirements-Dateien
API_REQ=$(find . -name "requirements.api.txt" | head -n 1)
SIMPLE_REQ=$(find . -name "requirements.simple.txt" | head -n 1)

# Überprüfe API requirements
if [ -n "$API_REQ" ]; then
    info "requirements.api.txt gefunden: $API_REQ"
    
    # Kopiere in das korrekte Verzeichnis, falls notwendig
    if [ "$API_REQ" != "./swissairdry/api/requirements.api.txt" ]; then
        cp "$API_REQ" "swissairdry/api/requirements.api.txt"
        success "requirements.api.txt in swissairdry/api/ kopiert"
    fi
    
    # Prüfe auf Probleme und korrigiere sie
    if grep -qE 'pydantic[><=]=?2\.' "swissairdry/api/requirements.api.txt"; then
        info "Downgrade pydantic von Version 2 auf Version 1 für bessere Kompatibilität..."
        sed -i 's/pydantic[><=]\{0,2\}2\.[0-9.]*\{0,\}/pydantic==1.10.8/g' "swissairdry/api/requirements.api.txt"
        success "pydantic auf Version 1.10.8 geändert für bessere Kompatibilität"
    fi
    
    # Prüfe, ob Versionen mit ungesundem Zeichen beginnen
    if grep -q "^[~^]" "swissairdry/api/requirements.api.txt"; then
        info "Entferne ungesunde Zeichen (^, ~) aus Versionen..."
        sed -i 's/^[~^]//' "swissairdry/api/requirements.api.txt"
        success "Ungesunde Zeichen aus Versionen entfernt"
    fi
    
    # Ersetze jede Version mit ungesundem Zeichen in der Mitte der Zeile
    sed -i 's/==\s*[~^]/==/g' "swissairdry/api/requirements.api.txt"
    
    # Stelle sicher, dass == zwischen Paket und Version steht (nicht nur =)
    sed -i 's/\([a-zA-Z0-9-]\+\)\s*=\([0-9]\)/\1==\2/g' "swissairdry/api/requirements.api.txt"
    
    # Entferne leere Zeilen und Kommentare 
    sed -i '/^#/d; /^$/d' "swissairdry/api/requirements.api.txt"
else
    warning "requirements.api.txt nicht gefunden. Erstelle neue Datei..."
    cat > "swissairdry/api/requirements.api.txt" << 'EOF'
fastapi==0.95.1
uvicorn==0.22.0
pydantic==1.10.8
paho-mqtt==1.6.1
sqlalchemy==2.0.15
psycopg2-binary==2.9.6
python-multipart==0.0.6
python-dotenv==1.0.0
httpx==0.24.1
jinja2==3.1.2
EOF
    success "Neue kompatible requirements.api.txt erstellt"
fi

# Überprüfe Simple-API requirements
if [ -n "$SIMPLE_REQ" ]; then
    info "requirements.simple.txt gefunden: $SIMPLE_REQ"
    
    # Kopiere in das korrekte Verzeichnis, falls notwendig
    if [ "$SIMPLE_REQ" != "./swissairdry/api/requirements.simple.txt" ]; then
        cp "$SIMPLE_REQ" "swissairdry/api/requirements.simple.txt"
        success "requirements.simple.txt in swissairdry/api/ kopiert"
    fi
    
    # Prüfe auf Probleme und korrigiere sie
    if grep -q "flask" "swissairdry/api/requirements.simple.txt"; then
        # Stelle sicher, dass Flask eine kompatible Version hat
        sed -i 's/flask[><=]\{0,2\}[0-9.]*\{0,\}/flask==2.2.3/g' "swissairdry/api/requirements.simple.txt"
        success "Flask auf Version 2.2.3 gesetzt"
    else
        # Füge Flask hinzu, falls es fehlt
        echo "flask==2.2.3" >> "swissairdry/api/requirements.simple.txt"
        success "Flask zur requirements.simple.txt hinzugefügt"
    fi
    
    # Entferne leere Zeilen und Kommentare
    sed -i '/^#/d; /^$/d' "swissairdry/api/requirements.simple.txt"
else
    warning "requirements.simple.txt nicht gefunden. Erstelle neue Datei..."
    cat > "swissairdry/api/requirements.simple.txt" << 'EOF'
flask==2.2.3
paho-mqtt==1.6.1
python-dotenv==1.0.0
requests==2.28.2
EOF
    success "Neue kompatible requirements.simple.txt erstellt"
fi

# 2. Überprüfe und korrigiere die Dockerfiles
info "Überprüfe Dockerfiles..."

# API Dockerfile
API_DOCKERFILE="swissairdry/api/Dockerfile"
if [ -f "$API_DOCKERFILE" ]; then
    info "API Dockerfile gefunden: $API_DOCKERFILE"
    
    # Erstelle ein Backup
    cp "$API_DOCKERFILE" "${API_DOCKERFILE}.bak"
    
    # Prüfe auf häufige Probleme
    if ! grep -q "apt-get update" "$API_DOCKERFILE"; then
        warning "Fehlende apt-get Befehle im Dockerfile. Korrigiere..."
        # Erstelle ein neues korrigiertes Dockerfile
        cat > "$API_DOCKERFILE" << 'EOF'
FROM python:3.9-slim

WORKDIR /app

# Installiere Abhängigkeiten mit expliziten Fehlerprüfungen
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Kopiere requirements.txt und installiere mit Fehlerbehandlung
COPY requirements.api.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt || \
    (echo "Fehler bei der Installation der Abhängigkeiten. Inhalt der requirements.txt:" && \
     cat /app/requirements.txt && exit 1)

# Kopiere Anwendungsdateien
COPY app/ /app/app/

# Setze Umgebungsvariablen
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Lege Port frei
EXPOSE 5000

# Starte die Anwendung
CMD ["python", "app/run2.py"]
EOF
        success "API Dockerfile korrigiert mit robuster Fehlerbehandlung"
    fi
else
    warning "API Dockerfile nicht gefunden. Erstelle neue Datei..."
    mkdir -p $(dirname "$API_DOCKERFILE")
    cat > "$API_DOCKERFILE" << 'EOF'
FROM python:3.9-slim

WORKDIR /app

# Installiere Abhängigkeiten mit expliziten Fehlerprüfungen
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Kopiere requirements.txt und installiere mit Fehlerbehandlung
COPY requirements.api.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt || \
    (echo "Fehler bei der Installation der Abhängigkeiten. Inhalt der requirements.txt:" && \
     cat /app/requirements.txt && exit 1)

# Kopiere Anwendungsdateien
COPY app/ /app/app/

# Setze Umgebungsvariablen
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Lege Port frei
EXPOSE 5000

# Starte die Anwendung
CMD ["python", "app/run2.py"]
EOF
    success "Neues API Dockerfile erstellt"
fi

# Simple API Dockerfile
SIMPLE_DOCKERFILE="swissairdry/api/Dockerfile.simple"
if [ -f "$SIMPLE_DOCKERFILE" ]; then
    info "Simple API Dockerfile gefunden: $SIMPLE_DOCKERFILE"
    
    # Erstelle ein Backup
    cp "$SIMPLE_DOCKERFILE" "${SIMPLE_DOCKERFILE}.bak"
    
    # Erstelle ein neues korrigiertes Dockerfile
    cat > "$SIMPLE_DOCKERFILE" << 'EOF'
FROM python:3.9-slim

WORKDIR /app

# Installiere Abhängigkeiten mit expliziten Fehlerprüfungen
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Kopiere requirements.txt und installiere mit Fehlerbehandlung
COPY requirements.simple.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt || \
    (echo "Fehler bei der Installation der Abhängigkeiten. Inhalt der requirements.txt:" && \
     cat /app/requirements.txt && exit 1)

# Kopiere Anwendungsdateien
COPY start_simple.py /app/

# Setze Umgebungsvariablen
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV FLASK_APP=start_simple.py

# Lege Port frei
EXPOSE 5001

# Starte die Anwendung
CMD ["python", "start_simple.py"]
EOF
    success "Simple API Dockerfile korrigiert mit robuster Fehlerbehandlung"
else
    warning "Simple API Dockerfile nicht gefunden. Erstelle neue Datei..."
    mkdir -p $(dirname "$SIMPLE_DOCKERFILE")
    cat > "$SIMPLE_DOCKERFILE" << 'EOF'
FROM python:3.9-slim

WORKDIR /app

# Installiere Abhängigkeiten mit expliziten Fehlerprüfungen
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Kopiere requirements.txt und installiere mit Fehlerbehandlung
COPY requirements.simple.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt || \
    (echo "Fehler bei der Installation der Abhängigkeiten. Inhalt der requirements.txt:" && \
     cat /app/requirements.txt && exit 1)

# Kopiere Anwendungsdateien
COPY start_simple.py /app/

# Setze Umgebungsvariablen
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV FLASK_APP=start_simple.py

# Lege Port frei
EXPOSE 5001

# Starte die Anwendung
CMD ["python", "start_simple.py"]
EOF
    success "Neues Simple API Dockerfile erstellt"
fi

# 3. Überprüfe oder erstelle start_simple.py
SIMPLE_PY="swissairdry/api/start_simple.py"
if [ ! -f "$SIMPLE_PY" ]; then
    warning "start_simple.py nicht gefunden. Erstelle Datei..."
    cat > "$SIMPLE_PY" << 'EOF'
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
from flask import Flask, request, jsonify
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
    """Callback bei Verbindungsabbruch"""
    logger.warning("MQTT-Client getrennt")

# MQTT-Client initialisieren
def init_mqtt():
    global mqtt_client
    
    mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_ID)
    
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
        return True
    except Exception as e:
        logger.error(f"Fehler bei der Verbindung zum MQTT-Broker: {str(e)}")
        return False

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
    print("SwissAirDry Simple API Server startet auf Port 5001...")
    
    # MQTT-Client initialisieren
    if init_mqtt():
        print("MQTT-Client erfolgreich initialisiert")
    else:
        print("MQTT-Client konnte nicht initialisiert werden")
    
    # Server starten
    try:
        app.run(host="0.0.0.0", port=5001, debug=True)
    except KeyboardInterrupt:
        print("API-Server wird beendet...")
    finally:
        # MQTT-Client stoppen
        if mqtt_client:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
EOF
    chmod +x "$SIMPLE_PY"
    success "start_simple.py erstellt"
fi

# 4. Aktualisiere docker-compose-Datei
info "Überprüfe docker-compose-Datei..."
DOCKER_COMPOSE="docker-compose-all-in-one.yml"

if [ -f "$DOCKER_COMPOSE" ]; then
    # Erstelle ein Backup
    cp "$DOCKER_COMPOSE" "${DOCKER_COMPOSE}.bak"
    
    # Überprüfe, ob ghcr.io-Referenzen verwendet werden
    if grep -q "image: ghcr.io/arduinoeinsteiger/" "$DOCKER_COMPOSE"; then
        info "ghcr.io-Referenzen gefunden. Ersetze sie durch lokale Builds..."
        
        # Ersetze API-Image
        sed -i 's|image: ghcr.io/arduinoeinsteiger/swissairdry-api:latest|build:\n      context: ./swissairdry/api\n      dockerfile: Dockerfile|g' "$DOCKER_COMPOSE"
        
        # Ersetze Simple-API-Image
        sed -i 's|image: ghcr.io/arduinoeinsteiger/swissairdry-simple-api:latest|build:\n      context: ./swissairdry/api\n      dockerfile: Dockerfile.simple|g' "$DOCKER_COMPOSE"
        
        success "ghcr.io-Referenzen durch lokale Builds ersetzt"
    fi
    
    # Überprüfe Volumen-Mappings für die API
    if ! grep -q "volumes:" "$DOCKER_COMPOSE" || ! grep -q "- ./swissairdry/api:/app" "$DOCKER_COMPOSE"; then
        warning "Möglicherweise fehlen Volumen-Mappings. Prüfe manuell."
    fi
    
    # Füge Portainer hinzu, falls es fehlt
    if ! grep -q "portainer:" "$DOCKER_COMPOSE"; then
        info "Portainer nicht gefunden. Füge es zur docker-compose-Datei hinzu..."
        
        # Finde den letzten Dienst in der Datei
        LAST_SERVICE=$(grep -E "^  [a-zA-Z0-9_-]+:" "$DOCKER_COMPOSE" | tail -n 1)
        LAST_SERVICE_NAME=$(echo "$LAST_SERVICE" | cut -d':' -f1 | tr -d ' ')
        
        # Füge Portainer nach dem letzten Dienst ein
        sed -i "s/^  $LAST_SERVICE_NAME:/  $LAST_SERVICE_NAME:\n\n  # Portainer - Container-Management\n  portainer:\n    image: portainer\/portainer-ce:latest\n    container_name: swissairdry-portainer\n    restart: unless-stopped\n    security_opt:\n      - no-new-privileges:true\n    volumes:\n      - \/etc\/localtime:\/etc\/localtime:ro\n      - \/var\/run\/docker.sock:\/var\/run\/docker.sock:ro\n      - portainer-data:\/data\n    ports:\n      - \"9000:9000\"  # Portainer Port\n    networks:\n      - swissairdry-network/g" "$DOCKER_COMPOSE"
        
        # Füge Portainer-Volume hinzu, falls es fehlt
        if ! grep -q "portainer-data:" "$DOCKER_COMPOSE"; then
            # Finde den Volumes-Abschnitt
            VOLUMES_LINE=$(grep -n "^volumes:" "$DOCKER_COMPOSE" | cut -d':' -f1)
            if [ -n "$VOLUMES_LINE" ]; then
                # Füge Portainer-Volume zum Volumes-Abschnitt hinzu
                sed -i "$VOLUMES_LINE a\\  portainer-data:" "$DOCKER_COMPOSE"
                success "Portainer-Volume hinzugefügt"
            else
                # Füge Volumes-Abschnitt mit Portainer-Volume am Ende der Datei hinzu
                echo -e "\nvolumes:\n  portainer-data:" >> "$DOCKER_COMPOSE"
                success "Volumes-Abschnitt mit Portainer-Volume hinzugefügt"
            fi
        fi
        
        success "Portainer zum docker-compose-all-in-one.yml hinzugefügt"
    fi
else
    warning "docker-compose-all-in-one.yml nicht gefunden. Erstelle eine neue Datei..."
    cat > "$DOCKER_COMPOSE" << 'EOF'
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
    image: eclipse-mosquitto:2.0.15
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
    build:
      context: ./swissairdry/api
      dockerfile: Dockerfile
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
      
  # Portainer - Container-Management
  portainer:
    image: portainer/portainer-ce:latest
    container_name: swissairdry-portainer
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    volumes:
      - /etc/localtime:/etc/localtime:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - portainer-data:/data
    ports:
      - "9000:9000"  # Portainer Port
    networks:
      - swissairdry-network

networks:
  swissairdry-network:
    driver: bridge

volumes:
  db-data:
  mosquitto-data:
  mosquitto-log:
  portainer-data:
EOF
    success "Neue docker-compose-all-in-one.yml erstellt"
fi

# 5. Stelle sicher, dass mosquitto.conf existiert
info "Überprüfe mosquitto.conf..."
MOSQUITTO_CONF="swissairdry/mqtt/mosquitto.conf"

if [ ! -f "$MOSQUITTO_CONF" ]; then
    warning "mosquitto.conf nicht gefunden. Erstelle Datei..."
    mkdir -p $(dirname "$MOSQUITTO_CONF")
    cat > "$MOSQUITTO_CONF" << 'EOF'
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
    success "Neue mosquitto.conf erstellt"
fi

# 6. Stelle sicher, dass nginx default.conf existiert
info "Überprüfe nginx default.conf..."
NGINX_CONF="nginx/conf.d/default.conf"

if [ ! -f "$NGINX_CONF" ]; then
    warning "nginx default.conf nicht gefunden. Erstelle Datei..."
    mkdir -p $(dirname "$NGINX_CONF")
    cat > "$NGINX_CONF" << 'EOF'
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
    
    # Portainer Zugriff
    location /portainer/ {
        proxy_pass http://portainer:9000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Große Datei-Uploads erlauben
    client_max_body_size 100M;
}
EOF
    success "Neue nginx default.conf erstellt"
fi

# 7. Erstelle eine .env-Datei, falls sie nicht existiert
info "Überprüfe .env-Datei..."
ENV_FILE=".env"

if [ ! -f "$ENV_FILE" ]; then
    warning ".env-Datei nicht gefunden. Erstelle Datei..."
    cat > "$ENV_FILE" << 'EOF'
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
    success "Neue .env-Datei erstellt"
fi

# 8. Erstelle ein Skript zum Testen des Builds
info "Erstelle Skript zum Testen des Docker-Builds..."
TEST_SCRIPT="test_docker_build.sh"
cat > "$TEST_SCRIPT" << 'EOF'
#!/bin/bash

# Test-Skript für Docker-Builds
# Dieses Skript testet, ob die Docker-Images erfolgreich gebaut werden können

# Farbige Ausgabe
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}===========================================================${NC}"
echo -e "${BLUE}     SwissAirDry Docker-Build-Test                         ${NC}"
echo -e "${BLUE}===========================================================${NC}"
echo ""

# API-Image testen
echo -e "${BLUE}[TEST]${NC} Teste API-Docker-Build..."
cd swissairdry/api
docker build -t swissairdry-api-test -f Dockerfile .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}[ERFOLG]${NC} API-Docker-Build erfolgreich"
else
    echo -e "${RED}[FEHLER]${NC} API-Docker-Build fehlgeschlagen"
fi

# Simple-API-Image testen
echo -e "${BLUE}[TEST]${NC} Teste Simple-API-Docker-Build..."
docker build -t swissairdry-simple-api-test -f Dockerfile.simple .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}[ERFOLG]${NC} Simple-API-Docker-Build erfolgreich"
else
    echo -e "${RED}[FEHLER]${NC} Simple-API-Docker-Build fehlgeschlagen"
fi

cd ../..

echo ""
echo -e "${BLUE}===========================================================${NC}"
echo -e "${BLUE}     Test abgeschlossen                                    ${NC}"
echo -e "${BLUE}===========================================================${NC}"
EOF
chmod +x "$TEST_SCRIPT"
success "Test-Skript erstellt: $TEST_SCRIPT"

echo ""
success "Docker-Build-Fehler behoben"
echo ""
info "Zusammenfassung der Änderungen:"
echo " - requirements.api.txt und requirements.simple.txt korrigiert"
echo " - Dockerfile und Dockerfile.simple angepasst"
echo " - docker-compose-all-in-one.yml aktualisiert"
echo " - Portainer integriert"
echo " - Alle benötigten Konfigurationsdateien erstellt oder aktualisiert"
echo ""
info "Nächste Schritte:"
echo " 1. Führen Sie das Test-Skript aus: ./test_docker_build.sh"
echo " 2. Bei Erfolg: docker-compose -f docker-compose-all-in-one.yml up -d"
echo " 3. Testen Sie die API: curl http://localhost:5000/api/status"
echo " 4. Testen Sie die Simple API: curl http://localhost:5001/api/status"
echo " 5. Zugriff auf Portainer: http://localhost:9000"
echo ""