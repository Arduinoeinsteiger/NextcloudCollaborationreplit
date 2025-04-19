#!/bin/bash

# SwissAirDry Installation Script
# ===============================
#
# Dieses Skript installiert und konfiguriert das SwissAirDry Docker-Setup automatisch.
# Führen Sie es mit Root-Rechten aus (sudo).
#
# Verwendung: sudo bash install.sh [option]
#   - Ohne Option für eine interaktive Installation
#   - --auto für eine automatische Installation mit Standardeinstellungen
#   - --update um nur die Docker-Container zu aktualisieren
#

set -e

# Farben für Ausgaben
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Log-Funktionen
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Überprüfen ob Docker & Docker Compose installiert ist
check_docker() {
    log_info "Überprüfe Docker-Installation..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker ist nicht installiert. Installation wird gestartet..."
        install_docker
    else
        log_success "Docker ist installiert."
    fi
    
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose ist nicht installiert. Installation wird gestartet..."
        install_docker_compose
    else
        log_success "Docker Compose ist installiert."
    fi
}

# Docker installieren
install_docker() {
    log_info "Installiere Docker..."
    
    # Installieren von notwendigen Paketen
    apt-get update
    apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
    
    # Docker GPG-Schlüssel hinzufügen
    curl -fsSL https://download.docker.com/linux/$(lsb_release -is | tr '[:upper:]' '[:lower:]')/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Repository einrichten
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/$(lsb_release -is | tr '[:upper:]' '[:lower:]') $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Docker installieren
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io
    
    # Docker-Service aktivieren und starten
    systemctl enable docker
    systemctl start docker
    
    log_success "Docker wurde erfolgreich installiert."
}

# Docker Compose installieren
install_docker_compose() {
    log_info "Installiere Docker Compose..."
    
    # Neueste Version von Docker Compose herunterladen
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    
    # Ausführungsrechte setzen
    chmod +x /usr/local/bin/docker-compose
    
    # Symlink erstellen für docker compose
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    log_success "Docker Compose wurde erfolgreich installiert."
}

# Konfiguration durch .env-Datei
setup_env() {
    log_info "Konfiguriere Umgebungsvariablen..."
    
    if [ ! -f .env ]; then
        log_info "Erstelle .env-Datei aus Vorlage..."
        cp .env.example .env
        
        # Sichere Passwörter generieren
        local db_password=$(openssl rand -base64 16)
        local api_key=$(openssl rand -base64 32)
        local jwt_secret=$(openssl rand -base64 32)
        local session_secret=$(openssl rand -base64 32)
        
        # Passwörter in .env-Datei ersetzen
        sed -i "s/change_me_to_secure_password/$db_password/g" .env
        sed -i "s/change_me_to_secure_key/$api_key/g" .env
        sed -i "s/change_me_to_secure_jwt_secret/$jwt_secret/g" .env
        sed -i "s/change_me_to_secure_session_secret/$session_secret/g" .env
        
        # Domäne konfigurieren (interaktiv oder automatisch)
        if [ "$1" != "--auto" ]; then
            read -p "Bitte geben Sie Ihre Hauptdomain ein (Standard: vgnc.org): " domain
            domain=${domain:-vgnc.org}
            
            sed -i "s/DOMAIN=vgnc.org/DOMAIN=$domain/g" .env
            sed -i "s/API_DOMAIN=api.vgnc.org/API_DOMAIN=api.$domain/g" .env
            sed -i "s/MQTT_DOMAIN=mqtt.vgnc.org/MQTT_DOMAIN=mqtt.$domain/g" .env
            sed -i "s/NEXTCLOUD_DOMAIN=vgnc.org/NEXTCLOUD_DOMAIN=$domain/g" .env
            
            log_info "Domäne auf $domain konfiguriert."
        fi
        
        log_success ".env-Datei erfolgreich konfiguriert."
    else
        log_info ".env-Datei existiert bereits. Überspringe Konfiguration."
    fi
}

# SSL-Zertifikate vorbereiten
setup_ssl() {
    log_info "Überprüfe SSL-Zertifikate..."
    
    # Stellen Sie sicher, dass die SSL-Verzeichnisse existieren
    mkdir -p ./ssl/certs ./ssl/private
    
    # Prüfen ob Zertifikate vorhanden sind
    if [ ! -f ./ssl/certs/vgnc.org.cert.pem ] || [ ! -f ./ssl/private/vgnc.org.key.pem ]; then
        log_warning "SSL-Zertifikate nicht gefunden."
        
        # Selbstsignierte Zertifikate erstellen (für Entwicklung)
        if [ "$1" == "--auto" ] || [ "$1" == "--dev" ]; then
            log_info "Erstelle selbstsignierte Zertifikate für Entwicklung..."
            
            # Domain aus .env-Datei lesen
            local domain=$(grep -oP '^DOMAIN=\K.*' .env)
            
            # Selbstsigniertes Zertifikat erstellen
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout ./ssl/private/vgnc.org.key.pem \
                -out ./ssl/certs/vgnc.org.cert.pem \
                -subj "/C=CH/ST=Zurich/L=Zurich/O=SwissAirDry/CN=$domain"
                
            log_success "Selbstsignierte Zertifikate wurden erstellt."
        else
            log_info "Für eine Produktionsumgebung empfehlen wir Let's Encrypt-Zertifikate."
            log_info "Sie können Let's Encrypt mit Certbot automatisch einrichten:"
            log_info "sudo certbot certonly --standalone -d Ihre-Domain.com -d www.Ihre-Domain.com"
            log_info "Und dann die Zertifikate nach ./ssl/certs/ und ./ssl/private/ kopieren."
            
            read -p "Möchten Sie trotzdem mit selbstsignierten Zertifikaten fortfahren? (j/n): " continue_ssl
            if [ "$continue_ssl" == "j" ] || [ "$continue_ssl" == "J" ]; then
                # Domain aus .env-Datei lesen
                local domain=$(grep -oP '^DOMAIN=\K.*' .env)
                
                # Selbstsigniertes Zertifikat erstellen
                openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                    -keyout ./ssl/private/vgnc.org.key.pem \
                    -out ./ssl/certs/vgnc.org.cert.pem \
                    -subj "/C=CH/ST=Zurich/L=Zurich/O=SwissAirDry/CN=$domain"
                    
                log_success "Selbstsignierte Zertifikate wurden erstellt."
            else
                log_error "SSL-Zertifikate fehlen. Bitte installieren Sie Zertifikate manuell, bevor Sie fortfahren."
                exit 1
            fi
        fi
    else
        log_success "SSL-Zertifikate gefunden."
    fi
}

# Docker-Container starten
start_containers() {
    log_info "Starte Docker-Container..."
    
    # Falls notwendig, alte Container und Images löschen
    if [ "$1" == "--update" ]; then
        log_info "Stoppe laufende Container..."
        docker compose down
        
        log_info "Entferne alte Images..."
        docker image prune -af
    fi
    
    # Docker-Container bauen und starten
    docker compose up -d --build
    
    log_success "Docker-Container wurden erfolgreich gestartet."
}

# Prüfen, ob alle Dienste erreichbar sind
check_services() {
    log_info "Überprüfe Dienste..."
    local timeout=60
    local api_up=false
    local simple_api_up=false
    
    # Warten bis API erreichbar ist
    log_info "Warte auf API-Server..."
    for i in $(seq 1 $timeout); do
        if curl -s http://localhost:5000 > /dev/null; then
            api_up=true
            break
        fi
        echo -n "."
        sleep 1
    done
    echo ""
    
    # Warten bis Simple API erreichbar ist
    log_info "Warte auf Simple API-Server..."
    for i in $(seq 1 $timeout); do
        if curl -s http://localhost:5001 > /dev/null; then
            simple_api_up=true
            break
        fi
        echo -n "."
        sleep 1
    done
    echo ""
    
    # Status ausgeben
    if [ "$api_up" = true ] && [ "$simple_api_up" = true ]; then
        log_success "Alle Dienste sind erfolgreich gestartet und erreichbar."
    else
        log_warning "Nicht alle Dienste konnten erreicht werden. Bitte überprüfen Sie die Logs:"
        log_info "docker logs swissairdry-api"
        log_info "docker logs swissairdry-simple-api"
    fi
}

# Hauptfunktion
main() {
    log_info "SwissAirDry Installation wird gestartet..."
    
    # Verzeichnisstruktur erstellen
    mkdir -p ./swissairdry/db/init ./swissairdry/mqtt
    
    # Docker überprüfen und installieren
    check_docker
    
    # .env-Datei konfigurieren
    setup_env $1
    
    # SSL-Zertifikate vorbereiten
    setup_ssl $1
    
    # Docker-Container starten
    start_containers $1
    
    # Dienste prüfen
    check_services
    
    log_success "SwissAirDry wurde erfolgreich installiert!"
    log_info "API ist verfügbar unter: http://localhost:5000"
    log_info "Simple API ist verfügbar unter: http://localhost:5001"
    log_info "MQTT-Broker ist verfügbar unter: localhost:1883"
    log_info "Nextcloud ExApp ist verfügbar unter: http://localhost:8000"
    
    # Abschlussinformationen
    log_info "Um die Installation abzuschließen, fügen Sie folgende Einträge zu Ihrer DNS-Konfiguration hinzu:"
    local domain=$(grep -oP '^DOMAIN=\K.*' .env)
    log_info "   $domain              → Server-IP"
    log_info "   api.$domain          → Server-IP"
    log_info "   mqtt.$domain         → Server-IP"
    
    log_info "Für weitere Informationen und Updates besuchen Sie: https://github.com/SwissAirDry/swissairdry"
}

# Skript mit Root-Rechten ausführen
if [ "$EUID" -ne 0 ]; then
    log_error "Bitte führen Sie das Skript mit Root-Rechten aus (sudo)."
    exit 1
fi

# Skript starten
main $1