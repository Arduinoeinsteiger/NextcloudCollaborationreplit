#!/bin/bash

# SwissAirDry Projekt-Organisationsskript
# Dieses Skript organisiert die Projektstruktur und erstellt eine klare Übersicht

# Farbige Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}===========================================================${NC}"
echo -e "${BLUE}     SwissAirDry Projekt-Organisations-Tool     ${NC}"
echo -e "${BLUE}===========================================================${NC}"
echo ""

# Konfigurationsvariablen
LOG_FILE="project_overview.md"
MAIN_DIR=$(pwd)

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

# Funktion zum Schreiben in die Log-Datei
function log() {
    echo "$1" >> "$LOG_FILE"
}

# Funktion zur Erstellung einer Dateiübersicht für einen Ordner
function create_file_overview() {
    local dir=$1
    local prefix=$2
    local max_depth=$3
    local current_depth=$4
    
    if [ -z "$current_depth" ]; then
        current_depth=0
    fi
    
    if [ "$current_depth" -ge "$max_depth" ] && [ "$max_depth" -ne -1 ]; then
        return
    fi
    
    # Files in aktuellem Verzeichnis auflisten
    for file in "$dir"/*; do
        if [ -f "$file" ]; then
            local filename=$(basename "$file")
            local extension="${filename##*.}"
            local file_size=$(du -h "$file" | cut -f1)
            
            # Dateistruktur im Markdown-Format
            log "${prefix}- 📄 **${filename}** (${file_size})"
            
            # Je nach Dateityp, Detailinformationen anzeigen
            case "$extension" in
                py)
                    # Für Python-Dateien, ersten Docstring oder Modulname extrahieren
                    local docstring=$(grep -m 1 '"""' "$file" | sed 's/"""//')
                    local classname=$(grep -m 1 "class " "$file" | sed 's/class \([^(:]*\).*/\1/')
                    
                    if [ -n "$docstring" ]; then
                        log "${prefix}  - *${docstring}*"
                    elif [ -n "$classname" ]; then
                        log "${prefix}  - *Definiert Klasse: ${classname}*"
                    fi
                    ;;
                sh)
                    # Für Shell-Skripte, Beschreibung oder Hauptfunktion extrahieren
                    local description=$(grep -m 1 "# " "$file" | sed 's/# //')
                    
                    if [ -n "$description" ]; then
                        log "${prefix}  - *${description}*"
                    fi
                    ;;
                md|markdown)
                    # Für Markdown-Dateien, Überschriften extrahieren
                    local title=$(grep -m 1 "^# " "$file" | sed 's/# //')
                    
                    if [ -n "$title" ]; then
                        log "${prefix}  - *${title}*"
                    fi
                    ;;
                yml|yaml)
                    # Für YAML-Dateien, Services extrahieren (für Docker Compose)
                    local services=$(grep -o "services:" "$file")
                    
                    if [ -n "$services" ]; then
                        log "${prefix}  - *Docker Compose Konfiguration*"
                        local service_count=$(grep -c "  [a-zA-Z-]\+:" "$file")
                        log "${prefix}  - *Enthält ${service_count} Services*"
                    fi
                    ;;
                conf)
                    # Für Konfigurationsdateien
                    log "${prefix}  - *Konfigurationsdatei*"
                    ;;
            esac
        fi
    done
    
    # Verzeichnisse in aktuellem Verzeichnis auflisten
    for file in "$dir"/*; do
        if [ -d "$file" ] && [[ ! $(basename "$file") == .* ]]; then
            local dirname=$(basename "$file")
            local file_count=$(find "$file" -type f | wc -l)
            
            # Verzeichnisstruktur im Markdown-Format
            log "${prefix}- 📁 **${dirname}** (${file_count} Dateien)"
            
            # Rekursiv Unterverzeichnisse auflisten
            create_file_overview "$file" "${prefix}  " "$max_depth" $((current_depth+1))
        fi
    done
}

# Funktion zum Erstellen einer Projektübersicht
function create_project_overview() {
    status_message "Erstelle Projektübersicht..."
    
    # Übersichtsdatei löschen, falls vorhanden
    rm -f "$LOG_FILE"
    
    # Überschrift
    log "# SwissAirDry Projektübersicht"
    log ""
    log "## Generiert am $(date '+%Y-%m-%d %H:%M:%S')"
    log ""
    
    # Projektstruktur
    log "## Projektstruktur"
    log ""
    create_file_overview "$MAIN_DIR" "" 3
    
    # Docker-Compose-Übersicht
    if [ -f "docker-compose.yml" ] || [ -f "docker-compose-all-in-one.yml" ]; then
        log ""
        log "## Docker-Konfiguration"
        log ""
        
        # Standarddatei
        if [ -f "docker-compose.yml" ]; then
            log "### docker-compose.yml"
            log ""
            log "Services:"
            log ""
            grep -o "  [a-zA-Z0-9_-]\+:" docker-compose.yml | sed 's/://' | sed 's/^/- /' >> "$LOG_FILE"
            log ""
        fi
        
        # All-in-One-Datei
        if [ -f "docker-compose-all-in-one.yml" ]; then
            log "### docker-compose-all-in-one.yml"
            log ""
            log "Services:"
            log ""
            grep -o "  [a-zA-Z0-9_-]\+:" docker-compose-all-in-one.yml | sed 's/://' | sed 's/^/- /' >> "$LOG_FILE"
            log ""
        fi
    fi
    
    # Python-Umgebung
    if [ -f "pyproject.toml" ] || [ -f "requirements.txt" ]; then
        log ""
        log "## Python-Umgebung"
        log ""
        
        # pyproject.toml
        if [ -f "pyproject.toml" ]; then
            log "### pyproject.toml"
            log ""
            
            # Name und Version
            local project_name=$(grep "name = " pyproject.toml | head -1 | sed 's/name = "\(.*\)"/\1/')
            local project_version=$(grep "version = " pyproject.toml | head -1 | sed 's/version = "\(.*\)"/\1/')
            
            log "- **Projektname:** ${project_name}"
            log "- **Version:** ${project_version}"
            log ""
            
            # Abhängigkeiten
            log "**Abhängigkeiten:**"
            log ""
            grep "^\[tool.poetry.dependencies\]" -A 50 pyproject.toml | grep "^[a-zA-Z0-9_-]\+ = " | sed 's/ = .*/ /' | sed 's/^/- /' >> "$LOG_FILE"
            log ""
        fi
        
        # requirements.txt
        if [ -f "requirements.txt" ]; then
            log "### requirements.txt"
            log ""
            log "**Abhängigkeiten:**"
            log ""
            cat requirements.txt | grep -v "^#" | grep -v "^[[:space:]]*$" | sed 's/^/- /' >> "$LOG_FILE"
            log ""
        fi
    fi
    
    # API-Endpunkte
    log ""
    log "## API-Endpunkte"
    log ""
    
    # Suche nach FastAPI/Flask-Routen
    api_endpoints=$(grep -r "@app\.\(get\|post\|put\|delete\)" --include="*.py" . | grep -o '".*"' | sort | uniq)
    
    if [ -n "$api_endpoints" ]; then
        log "### Verfügbare Endpunkte"
        log ""
        echo "$api_endpoints" | sed 's/^/- /' >> "$LOG_FILE"
    else
        log "Keine API-Endpunkte gefunden."
    fi
    
    success_message "Projektübersicht wurde erstellt: $LOG_FILE"
}

# Funktion zur Erstellung einer optimierten Projektstruktur
function organize_project_structure() {
    status_message "Organisiere Projektstruktur..."
    
    # Hauptverzeichnisse erstellen
    mkdir -p swissairdry/api/app/routes
    mkdir -p swissairdry/api/app/models
    mkdir -p swissairdry/api/app/schemas
    mkdir -p swissairdry/api/app/templates
    mkdir -p swissairdry/api/app/static
    mkdir -p swissairdry/mqtt
    mkdir -p swissairdry/exapp/daemon
    mkdir -p swissairdry/exapp/frontend/src
    mkdir -p nginx/conf.d
    mkdir -p docs/images
    mkdir -p scripts
    
    # Python- und Docker-Dateien an die richtige Stelle kopieren
    status_message "Verschiebe Dateien an die richtige Stelle..."
    
    # Python-Dateien
    find . -maxdepth 1 -name "*.py" -exec cp {} scripts/ \;
    
    # Docker-Compose-Dateien bleiben im Hauptverzeichnis
    
    # Shell-Skripte
    find . -maxdepth 1 -name "*.sh" -not -name "organize_project.sh" -exec cp {} scripts/ \;
    
    # Dokumentationsdateien
    find . -maxdepth 1 -name "*.md" -exec cp {} docs/ \;
    
    # MQTT-Konfigurationsdateien
    if [ -f "swissairdry/mqtt/mosquitto.conf" ]; then
        success_message "MQTT-Konfiguration bereits vorhanden."
    else
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
        success_message "MQTT-Konfiguration erstellt."
    fi
    
    # Projektstruktur-Übersicht erstellen
    create_project_overview
    
    # Readme aktualisieren
    cat > README.md << 'EOF'
# SwissAirDry

## Projektbeschreibung

SwissAirDry ist eine umfassende IoT-Plattform zur Verwaltung von Trocknungsgeräten.
Die Plattform ermöglicht die Überwachung und Steuerung von Geräten in Echtzeit,
Datenerfassung und -analyse sowie eine benutzerfreundliche Oberfläche für Techniker im Feld.

## Komponenten

- **API-Server**: FastAPI-basierter Hauptserver für die Geschäftslogik
- **Simple API**: Vereinfachte API für IoT-Geräte
- **MQTT-Broker**: Zur Kommunikation mit IoT-Geräten
- **Nextcloud Integration**: ExApp zur Integration in Nextcloud
- **PostgreSQL-Datenbank**: Zur Datenspeicherung

## Gerätetypen

- ESP8266
- ESP32
- STM32

## Installation

Siehe `INSTALLATIONSANLEITUNG.md` für detaillierte Installationsanweisungen.

## Fehlerbehebung

Siehe `FEHLERBEHEBUNG.md` für Hilfe bei häufigen Problemen.

## Projektübersicht

Eine detaillierte Übersicht der Projektstruktur finden Sie in der Datei `project_overview.md`.
EOF
    
    success_message "Projekt wurde organisiert."
    success_message "Bitte prüfen Sie die README.md und project_overview.md für eine Übersicht."
}

# Hauptfunktion
function main() {
    echo -e "${YELLOW}Dieses Skript organisiert die Projektstruktur und erstellt eine Übersicht.${NC}"
    echo -e "${YELLOW}Es werden keine Dateien gelöscht, nur kopiert und neue Strukturen erstellt.${NC}"
    echo ""
    read -p "Möchten Sie fortfahren? (j/n): " choice
    
    if [[ "$choice" != "j" && "$choice" != "J" ]]; then
        status_message "Abbruch durch Benutzer."
        exit 0
    fi
    
    # Funktion zur Projektorganisation aufrufen
    organize_project_structure
    
    echo ""
    echo -e "${BLUE}===========================================================${NC}"
    echo -e "${BLUE}                   Organisation abgeschlossen              ${NC}"
    echo -e "${BLUE}===========================================================${NC}"
    
    echo ""
    status_message "Die Projektstruktur wurde organisiert."
    status_message "Eine Übersicht wurde in der Datei ${PURPLE}project_overview.md${NC} erstellt."
    
    return 0
}

# Starte die Hauptfunktion
main