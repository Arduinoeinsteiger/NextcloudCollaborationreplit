#!/bin/bash

# System-Reparatur-Skript für SwissAirDry
# Dieses Skript behebt bekannte Probleme mit dem SwissAirDry-System

# Farbige Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===========================================================${NC}"
echo -e "${BLUE}     SwissAirDry System-Reparatur-Tool     ${NC}"
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

# Funktion zum Bereinigen des Docker-Systems
function clean_docker() {
    status_message "Bereinige Docker-System..."
    
    # Stoppe alle laufenden Container
    status_message "Stoppe alle laufenden Container..."
    docker-compose down 2>/dev/null || true
    
    # Entferne alle SwissAirDry-bezogenen Container
    status_message "Entferne SwissAirDry-Container..."
    docker rm -f $(docker ps -a --filter name=swissairdry -q) 2>/dev/null || true
    docker rm -f $(docker ps -a --filter name=mqtt -q) 2>/dev/null || true
    docker rm -f $(docker ps -a --filter name=api -q) 2>/dev/null || true
    
    # Entferne SwissAirDry-bezogene Netzwerke
    status_message "Entferne SwissAirDry-Netzwerke..."
    docker network rm $(docker network ls --filter name=swissairdry -q) 2>/dev/null || true
    
    success_message "Docker-System bereinigt."
    
    return 0
}

# Funktion zum Erstellen wichtiger Verzeichnisse
function create_directories() {
    status_message "Erstelle wichtige Verzeichnisse..."
    
    # Erstelle Verzeichnisse
    mkdir -p swissairdry/api/app
    mkdir -p swissairdry/mqtt
    mkdir -p swissairdry/api/app/templates
    mkdir -p swissairdry/api/app/static
    mkdir -p swissairdry/api/app/models
    mkdir -p swissairdry/api/app/routes
    mkdir -p swissairdry/api/app/schemas
    mkdir -p nginx/conf.d
    mkdir -p mysql/data
    mkdir -p mosquitto/config
    mkdir -p mosquitto/data
    mkdir -p mosquitto/log
    
    success_message "Verzeichnisse erstellt."
    
    return 0
}

# Funktion zum Erstellen wichtiger Konfigurationsdateien
function create_config_files() {
    status_message "Erstelle wichtige Konfigurationsdateien..."
    
    # Erstelle mosquitto.conf
    if [ ! -f "swissairdry/mqtt/mosquitto.conf" ]; then
        status_message "Erstelle mosquitto.conf..."
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
    
    # Erstelle nginx Konfiguration
    if [ ! -f "nginx/conf.d/default.conf" ]; then
        status_message "Erstelle nginx Konfiguration..."
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
    
    # Große Datei-Uploads erlauben
    client_max_body_size 100M;
}
EOF
        success_message "nginx Konfiguration erstellt."
    else
        success_message "nginx Konfiguration existiert bereits."
    fi
    
    # Erstelle docker-compose.yml, falls nicht vorhanden
    if [ ! -f "docker-compose.yml" ]; then
        status_message "Erstelle docker-compose.yml..."
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
      - "1883:1883"  # MQTT Port
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
               cd swissairdry/api/app && python -m uvicorn run2:app --host 0.0.0.0 --port 5000"
    ports:
      - "5000:5000"  # API Port
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
    ports:
      - "5001:5001"  # Simple API Port
    environment:
      - MQTT_BROKER=mqtt
      - MQTT_PORT=1883
    volumes:
      - .:/app
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
EOF
        success_message "docker-compose.yml erstellt."
    else
        success_message "docker-compose.yml existiert bereits."
    fi
    
    return 0
}

# Funktion zum Neu-Starten der Docker-Container
function restart_containers() {
    status_message "Starte Docker-Container neu..."
    
    # Docker-Compose ausführen
    if docker-compose up -d; then
        success_message "Docker-Container erfolgreich gestartet."
    else
        error_message "Fehler beim Starten der Docker-Container."
        return 1
    fi
    
    return 0
}

# Funktion zum Überprüfen der Container-Status
function check_container_status() {
    status_message "Überprüfe Container-Status..."
    
    # Warten, bis Container hochgefahren sind
    sleep 5
    
    # Zeige laufende Container an
    docker ps
    
    # Prüfe, ob alle erwarteten Container laufen
    expected_containers=("swissairdry-db" "swissairdry-mqtt" "swissairdry-api" "swissairdry-simple-api" "swissairdry-nginx")
    missing_containers=()
    
    for container in "${expected_containers[@]}"; do
        if ! docker ps --format '{{.Names}}' | grep -q "$container"; then
            missing_containers+=("$container")
        fi
    done
    
    if [ ${#missing_containers[@]} -eq 0 ]; then
        success_message "Alle erwarteten Container laufen."
    else
        error_message "Folgende Container laufen nicht: ${missing_containers[*]}"
        
        # Zeige Logs der fehlenden Container an
        for container in "${missing_containers[@]}"; do
            echo -e "${YELLOW}Logs für $container:${NC}"
            docker logs "$container" 2>&1 | tail -n 20
            echo ""
        done
        
        return 1
    fi
    
    return 0
}

# Hauptfunktion
function main() {
    echo -e "${YELLOW}Diese Skript wird das SwissAirDry-System reparieren.${NC}"
    echo -e "${YELLOW}Es werden bestehende Container gestoppt und wichtige Konfigurationsdateien erstellt.${NC}"
    read -p "Möchten Sie fortfahren? (j/n): " choice
    
    if [[ "$choice" != "j" && "$choice" != "J" ]]; then
        status_message "Abbruch durch Benutzer."
        exit 0
    fi
    
    # Führe Reparaturschritte aus
    clean_docker
    create_directories
    create_config_files
    restart_containers
    check_container_status
    
    echo ""
    echo -e "${BLUE}===========================================================${NC}"
    echo -e "${BLUE}                   Reparatur abgeschlossen                 ${NC}"
    echo -e "${BLUE}===========================================================${NC}"
    
    success_message "Die System-Reparatur wurde abgeschlossen."
    success_message "Falls weiterhin Probleme bestehen, führen Sie das diagnose_system.sh Skript aus."
    
    echo ""
    status_message "Sie können nun auf die folgenden Dienste zugreifen:"
    echo "  - Hauptanwendung (API): http://localhost:5000"
    echo "  - Simple API: http://localhost:5001"
    echo "  - MQTT Broker: localhost:1883"
    echo "  - MQTT WebSocket: ws://localhost:9001"
    
    return 0
}

# Starte die Hauptfunktion
main