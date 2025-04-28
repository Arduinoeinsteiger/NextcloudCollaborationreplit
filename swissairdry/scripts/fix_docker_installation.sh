#!/bin/bash

# Fix-Skript für SwissAirDry Docker-Installation
# Dieses Skript behebt die im Fehlerbericht vom 28.04.2024 erkannten Probleme

# Farbige Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===========================================================${NC}"
echo -e "${BLUE}     SwissAirDry Docker-Installations-Reparatur-Tool     ${NC}"
echo -e "${BLUE}===========================================================${NC}"
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

# Funktion zum Anzeigen von Fehlern
function error_message() {
    echo -e "${RED}[FEHLER]${NC} $1"
}

# Funktion zur Überprüfung der Repository-Struktur
function check_repository_structure() {
    status_message "Überprüfe Repository-Struktur..."
    
    local missing_dirs=()
    local missing_files=()
    
    # Überprüfe wichtige Verzeichnisse
    if [ ! -d "swissairdry" ]; then
        missing_dirs+=("swissairdry")
    fi
    
    if [ ! -d "swissairdry/api" ]; then
        missing_dirs+=("swissairdry/api")
    fi
    
    if [ ! -d "swissairdry/api/app" ]; then
        missing_dirs+=("swissairdry/api/app")
    fi
    
    # Überprüfe wichtige Dateien
    if [ ! -f "swissairdry/api/start_simple.py" ]; then
        missing_files+=("swissairdry/api/start_simple.py")
    fi
    
    if [ ! -f "swissairdry/api/app/run2.py" ]; then
        missing_files+=("swissairdry/api/app/run2.py")
    fi
    
    # Zeige Ergebnisse an
    if [ ${#missing_dirs[@]} -eq 0 ] && [ ${#missing_files[@]} -eq 0 ]; then
        success_message "Repository-Struktur ist vollständig."
        return 0
    else
        warning_message "Folgende Elemente fehlen im Repository:"
        
        if [ ${#missing_dirs[@]} -gt 0 ]; then
            echo "  Fehlende Verzeichnisse:"
            for dir in "${missing_dirs[@]}"; do
                echo "    - $dir"
            done
        fi
        
        if [ ${#missing_files[@]} -gt 0 ]; then
            echo "  Fehlende Dateien:"
            for file in "${missing_files[@]}"; do
                echo "    - $file"
            done
        fi
        
        return 1
    fi
}

# Funktion zur Überprüfung und Korrektur der Docker-Compose-Datei
function check_docker_compose() {
    status_message "Überprüfe Docker-Compose-Konfiguration..."
    
    local docker_compose_file="docker-compose-all-in-one.yml"
    
    if [ ! -f "$docker_compose_file" ]; then
        error_message "Docker-Compose-Datei '$docker_compose_file' nicht gefunden."
        return 1
    fi
    
    # Prüfe auf Referenzen zu GitHub Container Registry (ghcr.io)
    local ghcr_count=$(grep -c "ghcr.io" "$docker_compose_file")
    
    if [ "$ghcr_count" -gt 0 ]; then
        warning_message "Docker-Compose-Datei enthält $ghcr_count Referenzen zu ghcr.io"
        
        # Frage nach Bestätigung für Änderungen
        read -p "Möchten Sie die ghcr.io-Referenzen durch lokale Builds ersetzen? (j/n): " replace_choice
        
        if [[ "$replace_choice" == "j" || "$replace_choice" == "J" ]]; then
            # Erstelle Backup der originalen Datei
            cp "$docker_compose_file" "${docker_compose_file}.backup"
            
            # Ersetze ghcr.io-Referenzen durch lokale Builds
            sed -i 's|image: ghcr.io/arduinoeinsteiger/swissairdry-api:latest|build: ./swissairdry/api|g' "$docker_compose_file"
            sed -i 's|image: ghcr.io/arduinoeinsteiger/swissairdry-simple-api:latest|build: ./swissairdry/api|g' "$docker_compose_file"
            sed -i 's|image: ghcr.io/arduinoeinsteiger/swissairdry-exapp:latest|build: ./swissairdry/exapp|g' "$docker_compose_file"
            sed -i 's|image: ghcr.io/arduinoeinsteiger/swissairdry-exapp-daemon:latest|build: ./swissairdry/exapp/daemon|g' "$docker_compose_file"
            
            success_message "Docker-Compose-Datei wurde aktualisiert. Backup unter '${docker_compose_file}.backup'"
        else
            warning_message "Keine Änderungen an der Docker-Compose-Datei vorgenommen."
        fi
    else
        success_message "Docker-Compose-Datei verwendet keine ghcr.io-Referenzen."
    fi
    
    # Korrigiere Portprobleme, falls vorhanden
    status_message "Überprüfe Port-Konfigurationen..."
    
    # Überprüfe Portkonflikte zwischen Nextcloud und Nginx
    if grep -q "80:80" "$docker_compose_file" && grep -q "nextcloud" "$docker_compose_file"; then
        warning_message "Mögliche Portkonflikte zwischen Nextcloud und Nginx für Ports 80/443 gefunden"
        
        # Frage nach Bestätigung für Änderungen
        read -p "Möchten Sie die Nextcloud-Ports ändern, um Konflikte zu vermeiden? (j/n): " port_choice
        
        if [[ "$port_choice" == "j" || "$port_choice" == "J" ]]; then
            # Erstelle Backup, falls noch nicht getan
            if [ ! -f "${docker_compose_file}.backup" ]; then
                cp "$docker_compose_file" "${docker_compose_file}.backup"
            fi
            
            # Ändere Nextcloud-Ports auf 8080/8443
            nextcloud_service=$(grep -A 20 "nextcloud:" "$docker_compose_file" | grep -B 20 -m 1 "^\s*[a-zA-Z]")
            if [[ -n "$nextcloud_service" ]]; then
                status_message "Passe Nextcloud-Service für Ports 8080/8443 an..."
                
                # Sicherer Ansatz: Verwende eine temporäre Datei
                tmp_file="${docker_compose_file}.tmp"
                
                # Ersetze 80:80 mit 8080:80 im Nextcloud-Service-Block
                awk -v found=0 '
                    /nextcloud:/ {found=1}
                    found && /80:80/ {gsub("80:80", "8080:80"); found=0}
                    {print}
                ' "$docker_compose_file" > "$tmp_file"
                
                # Ersetze 443:443 mit 8443:443 im Nextcloud-Service-Block
                awk -v found=0 '
                    /nextcloud:/ {found=1}
                    found && /443:443/ {gsub("443:443", "8443:443"); found=0}
                    {print}
                ' "$tmp_file" > "$docker_compose_file"
                
                rm "$tmp_file"
                
                success_message "Port-Konfigurationen wurden aktualisiert. Nextcloud läuft jetzt auf Ports 8080/8443."
            else
                warning_message "Nextcloud-Service-Block konnte nicht gefunden werden. Manuelle Änderung erforderlich."
            fi
        else
            warning_message "Keine Änderungen an den Port-Konfigurationen vorgenommen."
        fi
    else
        success_message "Keine Portkonflikte zwischen Nextcloud und Nginx gefunden."
    fi
    
    return 0
}

# Funktion zum Erstellen fehlender Verzeichnisstrukturen
function create_missing_directories() {
    status_message "Erstelle fehlende Verzeichnisstrukturen..."
    
    # Hauptverzeichnisse
    mkdir -p swissairdry/api/app/routes
    mkdir -p swissairdry/api/app/models
    mkdir -p swissairdry/api/app/schemas
    mkdir -p swissairdry/api/app/templates
    mkdir -p swissairdry/api/app/static
    
    # MQTT Verzeichnis
    mkdir -p swissairdry/mqtt
    
    # ExApp Verzeichnisse
    mkdir -p swissairdry/exapp/daemon
    mkdir -p swissairdry/exapp/frontend/src
    
    # Nginx Verzeichnisse
    mkdir -p nginx/conf.d
    
    success_message "Verzeichnisstruktur erstellt."
    
    return 0
}

# Funktion zum Erstellen einer einfachen start_simple.py
function create_start_simple_py() {
    status_message "Erstelle einfache start_simple.py..."
    
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
    return render_template("index.html", title="SwissAirDry Simple API")

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

# Shutdown-Handler
@app.route("/shutdown", methods=["POST"])
def shutdown():
    """Herunterfahren des API-Servers"""
    logger.info("API-Server wird heruntergefahren...")
    
    # MQTT-Client stoppen
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
    
    # Flask-Shutdown-Funktion aufrufen
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Nicht im Werkzeug-Server')
    func()
    
    return jsonify({"success": True, "message": "Server wird heruntergefahren"})

# Erstelle Verzeichnisse für Templates und statische Dateien
def create_template_directories():
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    
    # Einfache Index-Template erstellen
    with open("templates/index.html", "w") as f:
        f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 40px;
            line-height: 1.6;
        }
        h1 {
            color: #333;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        .card {
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 20px;
            margin-bottom: 20px;
            background-color: #f9f9f9;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ title }}</h1>
        <div class="card">
            <h2>API-Status</h2>
            <p>Die API läuft und ist bereit für Anfragen.</p>
            <p>Rufen Sie <code>/api/status</code> auf, um den aktuellen Status zu sehen.</p>
        </div>
        <div class="card">
            <h2>API-Endpunkte</h2>
            <ul>
                <li><code>/api/status</code> - API-Status abfragen</li>
                <li><code>/api/device/{device_id}/data</code> - Gerätedaten senden</li>
                <li><code>/api/device/{device_id}/status</code> - Gerätestatus senden</li>
                <li><code>/api/send/{device_id}</code> - Befehl an Gerät senden</li>
            </ul>
        </div>
    </div>
</body>
</html>
        """)

# Hauptfunktion
if __name__ == "__main__":
    logger.info("API-Server wird gestartet...")
    
    # MQTT-Client initialisieren
    init_mqtt()
    
    # Template-Verzeichnisse erstellen
    create_template_directories()
    
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
        success_message "start_simple.py existiert bereits."
    fi
    
    return 0
}

# Funktion zum Erstellen einer einfachen run2.py
function create_run2_py() {
    status_message "Erstelle einfache run2.py..."
    
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

@app.get("/api/devices/{device_id}")
async def get_device(device_id: str):
    """Details zu einem bestimmten Gerät"""
    # Hier würde normalerweise eine Datenbankabfrage stehen
    # Für dieses einfache Beispiel verwenden wir eine Dummy-Logik
    
    if device_id.startswith("esp8266"):
        return {
            "id": device_id,
            "name": "Trockner 1",
            "type": "ESP8266",
            "status": "online",
            "lastSeen": "2024-04-28T14:30:00Z",
            "data": {
                "temperature": 22.5,
                "humidity": 45.2,
                "fanSpeed": 80
            }
        }
    elif device_id.startswith("esp32"):
        return {
            "id": device_id,
            "name": "Trockner 2",
            "type": "ESP32",
            "status": "offline",
            "lastSeen": "2024-04-28T10:15:00Z",
            "data": {
                "temperature": 0,
                "humidity": 0,
                "fanSpeed": 0
            }
        }
    elif device_id.startswith("stm32"):
        return {
            "id": device_id,
            "name": "Temperatur-Sensor",
            "type": "STM32",
            "status": "online",
            "lastSeen": "2024-04-28T14:35:00Z",
            "data": {
                "temperature": 24.8,
                "humidity": 38.5
            }
        }
    else:
        raise HTTPException(status_code=404, detail="Gerät nicht gefunden")

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
        success_message "run2.py existiert bereits."
    fi
    
    return 0
}

# Funktion zum Erstellen einer einfachen mosquitto.conf
function create_mosquitto_conf() {
    status_message "Erstelle mosquitto.conf..."
    
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
        success_message "mosquitto.conf existiert bereits."
    fi
    
    return 0
}

# Funktion zum Erstellen/Aktualisieren der Dockerfile für die API
function create_api_dockerfile() {
    status_message "Erstelle Dockerfile für API..."
    
    if [ ! -f "swissairdry/api/Dockerfile" ]; then
        cat > swissairdry/api/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Installiere Abhängigkeiten
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Kopiere Dateien
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere Anwendungsdateien
COPY app/ app/

# Setze Umgebungsvariablen
ENV PYTHONUNBUFFERED=1

# Starte die Anwendung
CMD ["python", "app/run2.py"]
EOF
        
        # Erstelle eine einfache requirements.txt
        cat > swissairdry/api/requirements.txt << 'EOF'
fastapi==0.109.2
uvicorn==0.27.1
pydantic==2.5.2
httpx==0.27.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
paho-mqtt==1.6.1
python-dotenv==1.0.1
jinja2==3.1.3
EOF
        
        success_message "Dockerfile und requirements.txt für API erstellt."
    else
        success_message "Dockerfile für API existiert bereits."
    fi
    
    return 0
}

# Funktion zum Erstellen/Aktualisieren eines Beispiel-Dockerfiles für Simple API
function create_simple_api_dockerfile() {
    status_message "Erstelle Dockerfile für Simple API..."
    
    if [ ! -f "swissairdry/api/Dockerfile.simple" ]; then
        cat > swissairdry/api/Dockerfile.simple << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Installiere Abhängigkeiten
RUN pip install --no-cache-dir flask paho-mqtt python-dotenv

# Kopiere Anwendungsdateien
COPY start_simple.py .

# Erstelle Verzeichnisse
RUN mkdir -p templates static

# Setze Umgebungsvariablen
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=start_simple.py

# Starte die Anwendung
CMD ["python", "start_simple.py"]
EOF
        
        success_message "Dockerfile für Simple API erstellt."
    else
        success_message "Dockerfile für Simple API existiert bereits."
    fi
    
    return 0
}

# Hauptfunktion
function main() {
    echo -e "${YELLOW}Dieser Skript behebt Probleme mit der SwissAirDry Docker-Installation.${NC}"
    echo -e "${YELLOW}Es werden fehlende Dateien und Verzeichnisse erstellt und die Docker-Konfiguration korrigiert.${NC}"
    echo ""
    read -p "Möchten Sie fortfahren? (j/n): " choice
    
    if [[ "$choice" != "j" && "$choice" != "J" ]]; then
        status_message "Abbruch durch Benutzer."
        exit 0
    fi
    
    echo ""
    
    # Überprüfungen und Korrekturen durchführen
    check_repository_structure
    check_docker_compose
    
    echo ""
    status_message "Beginne mit der Reparatur..."
    echo ""
    
    # Erstelle fehlende Verzeichnisse
    create_missing_directories
    
    # Erstelle fehlende Konfigurationsdateien
    create_start_simple_py
    create_run2_py
    create_mosquitto_conf
    create_api_dockerfile
    create_simple_api_dockerfile
    
    echo ""
    echo -e "${BLUE}===========================================================${NC}"
    echo -e "${BLUE}                   Reparatur abgeschlossen                 ${NC}"
    echo -e "${BLUE}===========================================================${NC}"
    
    success_message "Die Reparatur wurde abgeschlossen."
    success_message "Versuchen Sie jetzt, die Docker-Installation mit './start-all-in-one.sh' oder 'docker-compose -f docker-compose-all-in-one.yml up -d' erneut zu starten."
    
    return 0
}

# Starte die Hauptfunktion
main