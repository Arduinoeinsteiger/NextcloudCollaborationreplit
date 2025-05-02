#!/bin/bash
# SwissAirDry Installationsskript
#
# Dieses Skript führt die automatisierte Installation des SwissAirDry-Systems durch.
# Es prüft Systemvoraussetzungen, richtet Netzwerke ein und startet die Docker-Container.
#
# Verwendung: ./install.sh [Optionen]
#   --no-ufw: Überspringt die UFW-Firewall-Konfiguration
#   --verbose: Gibt detaillierte Informationen während der Installation aus
#   --no-deps-check: Überspringt die Prüfung der Abhängigkeiten
#   --skip-perms: Überspringt das Setzen von Dateiberechtigungen
#   --no-web-check: Überspringt Health-Checks der Webdienste
#   --interactive: Fragt interaktiv nach Konfigurationswerten
#   --help: Zeigt diese Hilfe an

# Version
VERSION="1.0.0"

# Farben für Terminal-Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Optionen verarbeiten
NO_UFW=0
VERBOSE=0
NO_DEPS_CHECK=0
SKIP_PERMS=0
NO_WEB_CHECK=0
INTERACTIVE=0

function show_help() {
  echo -e "${BLUE}SwissAirDry Installationsskript v${VERSION}${NC}"
  echo
  echo "Dieses Skript führt die automatisierte Installation des SwissAirDry-Systems durch."
  echo
  echo "Verwendung: ./install.sh [Optionen]"
  echo
  echo "Optionen:"
  echo "  --no-ufw         Überspringt die UFW-Firewall-Konfiguration"
  echo "  --verbose        Gibt detaillierte Informationen während der Installation aus"
  echo "  --no-deps-check  Überspringt die Prüfung der Abhängigkeiten"
  echo "  --skip-perms     Überspringt das Setzen von Dateiberechtigungen"
  echo "  --no-web-check   Überspringt Health-Checks der Webdienste"
  echo "  --interactive    Fragt interaktiv nach Konfigurationswerten"
  echo "  --help           Zeigt diese Hilfe an"
  echo
  exit 0
}

for arg in "$@"; do
  case $arg in
    --no-ufw)
      NO_UFW=1
      shift
      ;;
    --verbose)
      VERBOSE=1
      shift
      ;;
    --no-deps-check)
      NO_DEPS_CHECK=1
      shift
      ;;
    --skip-perms)
      SKIP_PERMS=1
      shift
      ;;
    --no-web-check)
      NO_WEB_CHECK=1
      shift
      ;;
    --interactive)
      INTERACTIVE=1
      shift
      ;;
    --help)
      show_help
      ;;
    *)
      echo -e "${RED}Unbekannte Option: $arg${NC}"
      echo "Verwenden Sie --help für eine Liste aller Optionen."
      exit 1
      ;;
  esac
done

# Logging-Funktion
log() {
  if [ $VERBOSE -eq 1 ] || [ "$1" != "DEBUG" ]; then
    case "$1" in
      "INFO")
        echo -e "${GREEN}[$1]${NC} $2"
        ;;
      "WARNING")
        echo -e "${YELLOW}[$1]${NC} $2"
        ;;
      "ERROR")
        echo -e "${RED}[$1]${NC} $2"
        ;;
      "DEBUG")
        echo -e "${BLUE}[$1]${NC} $2"
        ;;
      *)
        echo -e "[$1] $2"
        ;;
    esac
  fi
}

# Abhängigkeiten prüfen
check_dependencies() {
  if [ "$NO_DEPS_CHECK" -eq 1 ]; then
    log "INFO" "Überspringe Prüfung der Abhängigkeiten."
    return 0
  fi

  log "INFO" "Prüfe zusätzliche Abhängigkeiten..."
  
  local missing_deps=()
  
  # Liste der zu prüfenden Abhängigkeiten
  local dependencies=("curl" "wget" "jq" "nc" "python3" "pip3" "node" "npm")
  
  for dep in "${dependencies[@]}"; do
    if ! command -v $dep >/dev/null 2>&1; then
      missing_deps+=("$dep")
      log "DEBUG" "$dep nicht gefunden."
    else
      log "DEBUG" "$dep gefunden: $(command -v $dep)"
    fi
  done
  
  if [ ${#missing_deps[@]} -gt 0 ]; then
    log "WARNING" "Folgende Abhängigkeiten fehlen: ${missing_deps[*]}"
    log "INFO" "Diese Programme könnten für einige Funktionen benötigt werden."
    
    if [ "$INTERACTIVE" -eq 1 ]; then
      log "INFO" "Möchten Sie versuchen, die fehlenden Abhängigkeiten zu installieren? (j/n)"
      read -r answer
      if [[ "$answer" == "j" || "$answer" == "J" ]]; then
        install_dependencies "${missing_deps[@]}"
      fi
    fi
  else
    log "INFO" "Alle zusätzlichen Abhängigkeiten sind verfügbar."
  fi
}

# Abhängigkeiten installieren
install_dependencies() {
  log "INFO" "Installiere fehlende Abhängigkeiten..."
  
  if command -v apt-get >/dev/null 2>&1; then
    log "DEBUG" "apt-get gefunden, verwende apt-get..."
    sudo apt-get update
    sudo apt-get install -y "$@"
  elif command -v yum >/dev/null 2>&1; then
    log "DEBUG" "yum gefunden, verwende yum..."
    sudo yum install -y "$@"
  elif command -v dnf >/dev/null 2>&1; then
    log "DEBUG" "dnf gefunden, verwende dnf..."
    sudo dnf install -y "$@"
  elif command -v pacman >/dev/null 2>&1; then
    log "DEBUG" "pacman gefunden, verwende pacman..."
    sudo pacman -Sy "$@"
  else
    log "ERROR" "Kein bekannter Paketmanager gefunden. Bitte installieren Sie die Abhängigkeiten manuell."
    return 1
  fi
  
  return 0
}

# Setze Dateiberechtigungen
set_permissions() {
  if [ "$SKIP_PERMS" -eq 1 ]; then
    log "INFO" "Überspringe Setzen von Dateiberechtigungen."
    return 0
  fi
  
  log "INFO" "Setze Dateiberechtigungen..."
  
  # Datenverzeichnisse
  if [ -d "data" ]; then
    chmod -R 755 data
    log "DEBUG" "Rechte für data/ gesetzt."
    
    # PostgreSQL-Datenverzeichnis
    if [ -d "data/db" ]; then
      chmod -R 700 data/db
      log "DEBUG" "Rechte für data/db/ gesetzt."
    fi
    
    # MQTT-Verzeichnis
    if [ -d "data/mqtt" ]; then
      chmod -R 755 data/mqtt
      chmod -R 777 data/mqtt/log
      log "DEBUG" "Rechte für data/mqtt/ gesetzt."
    fi
  fi
  
  # .env-Datei
  if [ -f ".env" ]; then
    chmod 600 .env
    log "DEBUG" "Rechte für .env gesetzt."
  fi
  
  # Docker Compose und Docker-Dateien
  if [ -d "docker" ]; then
    chmod -R 755 docker
    log "DEBUG" "Rechte für docker/ gesetzt."
  fi
  
  log "INFO" "Dateiberechtigungen erfolgreich gesetzt."
}

# Interaktive Konfiguration
configure_env() {
  if [ "$INTERACTIVE" -ne 1 ]; then
    log "DEBUG" "Überspringe interaktive Konfiguration."
    return 0
  fi
  
  log "INFO" "Starte interaktive Konfiguration..."
  
  if [ ! -f ".env" ]; then
    log "ERROR" "Keine .env-Datei gefunden. Die Konfiguration kann nicht aktualisiert werden."
    return 1
  fi
  
  log "INFO" "Aktuelle Konfiguration wird angezeigt..."
  log "INFO" "Drücken Sie Enter, um den Standardwert zu übernehmen."
  
  # Liste der zu konfigurierenden Variablen
  # Format: "VARIABLE_NAME|Beschreibung|Standardwert"
  local configs=(
    "DB_HOST|Datenbank-Host|localhost"
    "DB_PORT|Datenbank-Port|5432"
    "DB_USER|Datenbank-Benutzername|swissairdry"
    "DB_PASSWORD|Datenbank-Passwort|geheim123"
    "MQTT_HOST|MQTT-Broker-Host|localhost"
    "MQTT_PORT|MQTT-Broker-Port|1883"
    "API_HOST|API-Host|0.0.0.0"
    "API_PORT|API-Port|5000"
  )
  
  for config in "${configs[@]}"; do
    IFS='|' read -r var_name description default_value <<< "$config"
    
    # Aktuellen Wert aus .env lesen
    current_value=$(grep "^$var_name=" .env | cut -d '=' -f2-)
    if [ -z "$current_value" ]; then
      current_value="$default_value"
    fi
    
    # Benutzer nach neuem Wert fragen
    log "INFO" "$description [$current_value]:"
    read -r new_value
    
    # Wenn kein neuer Wert eingegeben wurde, behalte den aktuellen Wert
    if [ -z "$new_value" ]; then
      new_value="$current_value"
    fi
    
    # Wert in .env aktualisieren
    if grep -q "^$var_name=" .env; then
      sed -i "s|^$var_name=.*|$var_name=$new_value|" .env
    else
      echo "$var_name=$new_value" >> .env
    fi
    
    log "DEBUG" "$var_name auf $new_value gesetzt."
  done
  
  log "INFO" "Konfiguration abgeschlossen."
}

# Umfassender Gesundheitscheck
perform_health_check() {
  if [ "$NO_WEB_CHECK" -eq 1 ]; then
    log "INFO" "Überspringe Health-Checks."
    return 0
  fi
  
  log "INFO" "Führe umfassenden Gesundheitscheck durch..."
  local failed_checks=0
  
  # Warte etwas länger auf den Start der Dienste
  log "DEBUG" "Warte auf Start der Dienste (15s)..."
  sleep 15
  
  # Container-Status prüfen
  log "DEBUG" "Prüfe Container-Status..."
  local containers=("swissairdry-api" "swissairdry-mqtt" "swissairdry-db" "swissairdry-exapp")
  
  for container in "${containers[@]}"; do
    docker ps --format "{{.Names}}" | grep -q "$container"
    if [ $? -eq 0 ]; then
      local status=$(docker inspect --format "{{.State.Status}}" "$container")
      if [ "$status" == "running" ]; then
        log "INFO" "Container $container ist aktiv."
      else
        log "WARNING" "Container $container hat Status: $status"
        failed_checks=$((failed_checks+1))
      fi
    else
      log "DEBUG" "Container $container wurde nicht gefunden (optional)."
    fi
  done
  
  # API-Health-Check
  log "DEBUG" "Prüfe API-Gesundheit..."
  local api_response=$(curl -s -w "%{http_code}" "http://localhost:5000/health" -o /dev/null)
  if [ "$api_response" == "200" ]; then
    log "INFO" "API-Health-Check erfolgreich."
  else
    log "WARNING" "API-Health-Check fehlgeschlagen (Status: $api_response)."
    failed_checks=$((failed_checks+1))
  fi
  
  # MQTT-Verbindung prüfen
  log "DEBUG" "Prüfe MQTT-Verbindung..."
  nc -z localhost 1883 >/dev/null 2>&1
  if [ $? -eq 0 ]; then
    log "INFO" "MQTT-Broker-Verbindungscheck erfolgreich."
  else
    log "WARNING" "MQTT-Broker-Verbindungscheck fehlgeschlagen."
    failed_checks=$((failed_checks+1))
  fi
  
  # Datenbank-Verbindung prüfen
  log "DEBUG" "Prüfe Datenbankverbindung..."
  if docker ps --format "{{.Names}}" | grep -q "swissairdry-db"; then
    docker exec swissairdry-db pg_isready -U swissairdry >/dev/null 2>&1
    if [ $? -eq 0 ]; then
      log "INFO" "Datenbank-Verbindungscheck erfolgreich."
    else
      log "WARNING" "Datenbank-Verbindungscheck fehlgeschlagen."
      failed_checks=$((failed_checks+1))
    fi
  else
    log "DEBUG" "Datenbank-Container nicht gefunden, überspringe Check."
  fi
  
  if [ $failed_checks -gt 0 ]; then
    log "WARNING" "$failed_checks Gesundheitschecks sind fehlgeschlagen."
    log "INFO" "Prüfen Sie die Log-Dateien für weitere Informationen."
    return 1
  else
    log "INFO" "Alle Gesundheitschecks erfolgreich."
    return 0
  fi
}

# Installationsanzeige
show_header() {
  echo -e "${BLUE}"
  echo "   _____       _         ___  _      ____             "
  echo "  / ___/      (_)____   /   |(_)____/ __ \________  __"
  echo "  \__ \______/ / ___/  / /| |/ / ___/ / / / ___/ / / /"
  echo " ___/ /_____/ (__  )  / ___ / / /  / /_/ / /  / /_/ / "
  echo "/____/     /_/____/  /_/  |_/_/_/  /_____/_/   \__, /  "
  echo "                                              /____/   "
  echo -e "${NC}"
  echo -e "Installation ${GREEN}v${VERSION}${NC} ($(date +"%d.%m.%Y"))"
  echo -e "-----------------------------------------------"
}

# Hauptfunktion
main() {
  # Header anzeigen
  show_header
  
  log "INFO" "SwissAirDry Installation beginnt..."
  log "INFO" "Datum: $(date)"
  
  # Prüfe zusätzliche Abhängigkeiten
  check_dependencies
  
  # Interaktive Konfiguration (wenn aktiviert)
  if [ "$INTERACTIVE" -eq 1 ]; then
    configure_env
  fi
  
  # Setze Dateiberechtigungen
  set_permissions
  
  # Prüfe Systemvoraussetzungen und starte Installation
  install_swissairdry
  
  # Gesundheitscheck durchführen
  perform_health_check
  
  # Zusammenfassung anzeigen
  show_summary
}

# Zusammenfassung anzeigen
show_summary() {
  echo
  echo -e "${GREEN}==================== INSTALLATION ABGESCHLOSSEN ====================${NC}"
  echo
  echo -e "SwissAirDry wurde installiert und ist bereit zur Verwendung."
  echo
  echo -e "Weboberfläche: ${BLUE}http://localhost:8080${NC}"
  echo -e "API: ${BLUE}http://localhost:5000${NC}"
  echo -e "Simple API: ${BLUE}http://localhost:5001${NC}"
  echo -e "ExApp: ${BLUE}http://localhost:3000${NC}"
  echo
  echo -e "Für die Verwaltung der Docker-Container:"
  echo -e "  ${YELLOW}docker-compose ps${NC} - Zeigt laufende Container an"
  echo -e "  ${YELLOW}docker-compose logs${NC} - Zeigt Logs aller Container an"
  echo -e "  ${YELLOW}docker-compose restart${NC} - Startet alle Container neu"
  echo
  echo -e "Für weitere Informationen lesen Sie bitte die ${BLUE}INSTALLATION.md${NC}"
  echo
  echo -e "${GREEN}=====================================================================${NC}"
}

# Hauptinstallation
install_swissairdry() {
  log "INFO" "Prüfe Systemvoraussetzungen..."

if ! command -v docker >/dev/null 2>&1; then
  log "ERROR" "Docker ist nicht installiert. Bitte zuerst Docker installieren."
  exit 1
else
  log "DEBUG" "Docker gefunden: $(docker --version)"
fi

if ! command -v docker-compose >/dev/null 2>&1; then
  log "ERROR" "Docker Compose ist nicht installiert. Bitte zuerst Docker Compose installieren."
  exit 1
else
  log "DEBUG" "Docker Compose gefunden: $(docker-compose --version)"
fi

# Prüfe, ob wir als root laufen (für Firewall-Konfiguration benötigt)
if [ "$NO_UFW" -eq 0 ] && [ "$EUID" -ne 0 ]; then
  log "WARNING" "Dieses Skript benötigt Root-Rechte für Firewall-Konfigurationen."
  log "WARNING" "Bitte mit sudo ausführen oder verwenden Sie die Option --no-ufw."
  exit 1
fi

# Netzwerkkonfiguration prüfen
log "INFO" "Prüfe Netzwerkkonfiguration..."
ports=(80 443 8080 3000 5000 5001 8701 1883 9001 5432)
conflicts=0

for port in "${ports[@]}"; do
  nc -z localhost $port >/dev/null 2>&1
  if [ $? -eq 0 ]; then
    log "WARNING" "Port $port ist bereits belegt. Dies könnte zu Konflikten führen."
    conflicts=$((conflicts+1))
  else
    log "DEBUG" "Port $port ist verfügbar."
  fi
done

if [ $conflicts -gt 0 ]; then
  log "WARNING" "Es wurden $conflicts Portkonflikte gefunden. Fortfahren? (j/n)"
  read -r answer
  if [[ "$answer" != "j" && "$answer" != "J" ]]; then
    log "INFO" "Installation abgebrochen."
    exit 0
  fi
fi

# Firewall-Regeln (bei Bedarf)
if [ "$NO_UFW" -eq 0 ] && command -v ufw >/dev/null 2>&1; then
  log "INFO" "UFW-Firewall gefunden. Konfiguriere Ports..."
  ufw status | grep -q "Status: active"
  if [ $? -eq 0 ]; then
    for port in "${ports[@]}"; do
      log "DEBUG" "Öffne Port $port/tcp..."
      ufw allow $port/tcp >/dev/null 2>&1
    done
    log "INFO" "Firewall-Regeln hinzugefügt."
  else
    log "WARNING" "UFW ist installiert, aber nicht aktiv. Überspringe Firewall-Konfiguration."
  fi
else
  log "INFO" "Überspringe Firewall-Konfiguration."
fi

# Projekt-Setup
log "INFO" "Erstelle notwendige Ordner und Konfigurationsdateien..."
mkdir -p data/db data/mqtt/data data/mqtt/log
log "DEBUG" "Verzeichnisstruktur erstellt."

# Konfiguration kopieren
if [ -f .env.example ] && [ ! -f .env ]; then
  cp .env.example .env
  log "INFO" ".env-Datei aus Vorlage erstellt. Bitte passen Sie diese an Ihre Umgebung an."
else
  if [ -f .env ]; then
    log "DEBUG" ".env-Datei existiert bereits."
  else
    log "WARNING" ".env.example nicht gefunden. Bitte erstellen Sie eine .env-Datei manuell."
  fi
fi

# Docker-Netzwerke erstellen
log "INFO" "Erstelle Docker-Netzwerke..."
docker network create frontend 2>/dev/null || log "DEBUG" "Netzwerk 'frontend' existiert bereits."
docker network create backend 2>/dev/null || log "DEBUG" "Netzwerk 'backend' existiert bereits."
docker network create mqtt-net 2>/dev/null || log "DEBUG" "Netzwerk 'mqtt-net' existiert bereits."

# Starte die Services
if [ -d "docker" ]; then
  log "INFO" "Starte Docker-Container..."
  cd docker || exit 1
  docker-compose up -d
  
  if [ $? -eq 0 ]; then
    log "INFO" "Docker-Container erfolgreich gestartet."
  else
    log "ERROR" "Fehler beim Starten der Docker-Container."
    exit 1
  fi
else
  log "ERROR" "Docker-Verzeichnis nicht gefunden."
  log "ERROR" "Dieses Skript muss im Hauptverzeichnis des Projekts ausgeführt werden."
  exit 1
fi

# Überprüfe, ob die wichtigsten Dienste laufen
log "INFO" "Überprüfe laufende Dienste..."
sleep 5  # Kurz warten, damit die Container Zeit haben zu starten

# API-Erreichbarkeit prüfen
log "DEBUG" "Prüfe API-Erreichbarkeit..."
curl -s "http://localhost:5000/health" >/dev/null 2>&1
if [ $? -eq 0 ]; then
  log "INFO" "SwissAirDry API (Port 5000) ist erreichbar."
else
  log "WARNING" "SwissAirDry API (Port 5000) scheint nicht erreichbar zu sein."
fi

# MQTT-Broker prüfen
log "DEBUG" "Prüfe MQTT-Broker..."
nc -z localhost 1883 >/dev/null 2>&1
if [ $? -eq 0 ]; then
  log "INFO" "MQTT-Broker (Port 1883) ist erreichbar."
else
  log "WARNING" "MQTT-Broker (Port 1883) scheint nicht erreichbar zu sein."
fi

  log "INFO" "Installation abgeschlossen. Prüfe Status mit 'docker-compose ps'"
  log "INFO" "Für weitere Informationen lesen Sie bitte die INSTALLATION.md"
}

# Hauptfunktion aufrufen
main