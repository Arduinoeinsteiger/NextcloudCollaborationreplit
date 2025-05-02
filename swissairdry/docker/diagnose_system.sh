#!/bin/bash

# Diagnose-Skript für SwissAirDry
# Dieses Skript untersucht den aktuellen Zustand des Systems und behebt häufige Probleme

# Farbige Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===========================================================${NC}"
echo -e "${BLUE}     SwissAirDry System-Diagnose und Reparatur-Tool     ${NC}"
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

# Funktion zur Überprüfung des Dateisystems
function check_filesystem() {
    status_message "Überprüfe wichtige Dateien..."
    
    missing_files=()
    
    # Liste von wichtigen Dateien und Verzeichnissen
    important_files=(
        "docker-compose.yml"
        "swissairdry/api/app/run2.py"
        "swissairdry/api/start_simple.py"
        "swissairdry/mqtt/mosquitto.conf"
    )
    
    for file in "${important_files[@]}"; do
        if [ ! -f "$file" ]; then
            missing_files+=("$file")
            error_message "Datei nicht gefunden: $file"
        else
            success_message "Datei gefunden: $file"
        fi
    done
    
    if [ ${#missing_files[@]} -eq 0 ]; then
        success_message "Alle wichtigen Dateien sind vorhanden."
    else
        error_message "Es fehlen ${#missing_files[@]} wichtige Dateien."
        return 1
    fi
    
    # Überprüfe die als gelöscht markierten Dateien
    if [ -f "requirements.api.txt" ]; then
        warning_message "Die Datei requirements.api.txt ist physisch vorhanden, aber als gelöscht markiert."
    fi
    
    if [ -f "Dockerfile.api" ]; then
        warning_message "Die Datei Dockerfile.api ist physisch vorhanden, aber als gelöscht markiert."
    fi
    
    if [ -f "app/main.py" ]; then
        warning_message "Die Datei app/main.py ist physisch vorhanden, aber als gelöscht markiert."
    fi
    
    return 0
}

# Funktion zur Überprüfung der Docker-Installation
function check_docker() {
    status_message "Überprüfe Docker-Installation..."
    
    if ! command -v docker &> /dev/null; then
        error_message "Docker ist nicht installiert."
        return 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error_message "Docker Compose ist nicht installiert."
        return 1
    fi
    
    success_message "Docker und Docker Compose sind installiert."
    
    # Prüfe, ob Docker-Daemon läuft
    if ! docker info &> /dev/null; then
        error_message "Docker-Daemon ist nicht gestartet oder Sie haben keine Berechtigungen."
        return 1
    fi
    
    success_message "Docker-Daemon läuft."
    
    return 0
}

# Funktion zur Überprüfung der Docker-Container
function check_containers() {
    status_message "Überprüfe Docker-Container..."
    
    # Anzeigen aller Container (auch gestoppte)
    echo "Liste aller Container (auch gestoppte):"
    docker ps -a
    
    # Prüfen, ob SwissAirDry-Container laufen
    running_containers=$(docker ps --format "{{.Names}}" | grep -E 'swissairdry|mqtt|api|db' | wc -l)
    
    if [ "$running_containers" -eq 0 ]; then
        warning_message "Keine SwissAirDry-Container sind aktiv."
    else
        success_message "$running_containers SwissAirDry-Container sind aktiv."
    fi
    
    return 0
}

# Funktion zur Überprüfung der Netzwerk-Ports
function check_ports() {
    status_message "Überprüfe Netzwerk-Ports..."
    
    # Liste der wichtigen Ports
    declare -A ports
    ports[5000]="API"
    ports[5001]="Simple API"
    ports[1883]="MQTT Broker"
    ports[9001]="MQTT WebSocket"
    ports[3000]="ExApp Server"
    ports[8701]="ExApp Daemon"
    ports[80]="HTTP"
    ports[443]="HTTPS"
    
    # Prüfe jeden Port
    for port in "${!ports[@]}"; do
        if command -v ss &> /dev/null; then
            # Verwende ss, wenn verfügbar
            if ss -tuln | grep -q ":$port "; then
                success_message "Port $port (${ports[$port]}) ist aktiv."
            else
                warning_message "Port $port (${ports[$port]}) ist nicht aktiv."
            fi
        elif command -v netstat &> /dev/null; then
            # Verwende netstat als Alternative
            if netstat -tuln | grep -q ":$port "; then
                success_message "Port $port (${ports[$port]}) ist aktiv."
            else
                warning_message "Port $port (${ports[$port]}) ist nicht aktiv."
            fi
        else
            error_message "Weder ss noch netstat sind verfügbar. Port-Überprüfung nicht möglich."
            break
        fi
    done
    
    return 0
}

# Funktion zur automatischen Reparatur von erkannten Problemen
function repair_system() {
    status_message "Starte automatische Reparatur..."
    
    # Überprüfe, ob docker-compose.yml existiert
    if [ ! -f "docker-compose.yml" ]; then
        error_message "Keine docker-compose.yml gefunden. Kann keine Reparatur durchführen."
        return 1
    fi
    
    # Stoppe alle Container
    status_message "Stoppe alle laufenden Container..."
    docker-compose down 2>/dev/null
    
    # Prüfe, ob wichtige Verzeichnisse existieren und erstelle sie bei Bedarf
    mkdir -p swissairdry/api/app
    mkdir -p swissairdry/mqtt
    mkdir -p nginx/conf.d
    
    # Prüfe, ob mosquitto.conf existiert
    if [ ! -f "swissairdry/mqtt/mosquitto.conf" ]; then
        status_message "Erstelle fehlende mosquitto.conf..."
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
        success_message "mosquitto.conf wurde erstellt."
    fi
    
    # Starte die Container neu
    status_message "Starte Container neu..."
    docker-compose up -d
    
    success_message "Reparatur abgeschlossen. Bitte überprüfen Sie, ob das System jetzt funktioniert."
    
    return 0
}

# Hauptfunktion
function main() {
    # Führe alle Überprüfungen durch
    check_filesystem
    fs_status=$?
    
    check_docker
    docker_status=$?
    
    check_containers
    container_status=$?
    
    check_ports
    port_status=$?
    
    echo ""
    echo -e "${BLUE}===========================================================${NC}"
    echo -e "${BLUE}                   Diagnose Ergebnisse                    ${NC}"
    echo -e "${BLUE}===========================================================${NC}"
    
    if [ $fs_status -eq 0 ] && [ $docker_status -eq 0 ] && [ $container_status -eq 0 ] && [ $port_status -eq 0 ]; then
        success_message "System-Diagnose abgeschlossen. Einige Warnungen wurden gefunden."
    else
        error_message "System-Diagnose abgeschlossen. Es wurden Probleme gefunden."
    fi
    
    # Frage nach Reparatur
    echo ""
    read -p "Möchten Sie eine automatische Reparatur durchführen? (j/n): " repair_choice
    
    if [[ $repair_choice == "j" || $repair_choice == "J" ]]; then
        repair_system
    else
        status_message "Keine Reparatur durchgeführt."
    fi
    
    echo ""
    status_message "Diagnose abgeschlossen."
}

# Starte die Hauptfunktion
main