#!/bin/bash
# SwissAirDry - Komplettes Installationsskript
# Dieses Skript installiert den gesamten Stack:
# - Nextcloud
# - SwissAirDry API
# - MQTT-Broker
# - Datenbank
# - Alle nötigen Abhängigkeiten
#
# Version: 1.0.0
# Datum: 2025-04-19

# Farben für Ausgaben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funktion zum Anzeigen von Informationen
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Funktion zum Anzeigen von Erfolgen
print_success() {
    echo -e "${GREEN}[ERFOLG]${NC} $1"
}

# Funktion zum Anzeigen von Warnungen
print_warning() {
    echo -e "${YELLOW}[WARNUNG]${NC} $1"
}

# Funktion zum Anzeigen von Fehlern
print_error() {
    echo -e "${RED}[FEHLER]${NC} $1"
}

# Funktion zum Prüfen und Installieren von Abhängigkeiten
check_and_install_dependency() {
    local package=$1
    print_info "Prüfe auf $package..."
    if ! command -v $package &> /dev/null; then
        print_warning "$package ist nicht installiert. Installiere..."
        if [[ "$package" == "docker" ]]; then
            # Docker benötigt spezielle Installation
            install_docker
        elif [[ "$package" == "docker-compose" ]]; then
            # Docker Compose benötigt spezielle Installation
            install_docker_compose
        else
            apt-get update && apt-get install -y $package
        fi
        
        # Prüfen, ob die Installation erfolgreich war
        if command -v $package &> /dev/null; then
            print_success "$package wurde erfolgreich installiert."
        else
            print_error "Installation von $package fehlgeschlagen."
            exit 1
        fi
    else
        print_success "$package ist bereits installiert."
    fi
}

# Docker Installation
install_docker() {
    print_info "Installiere Docker..."
    apt-get update
    apt-get install -y apt-transport-https ca-certificates curl software-properties-common gnupg
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io
    systemctl enable docker
    systemctl start docker
}

# Docker Compose Installation
install_docker_compose() {
    print_info "Installiere Docker Compose..."
    mkdir -p /usr/local/lib/docker/cli-plugins/
    latest_compose_version=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
    curl -L "https://github.com/docker/compose/releases/download/${latest_compose_version}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    ln -sf /usr/local/bin/docker-compose /usr/local/lib/docker/cli-plugins/docker-compose
}

# SSL-Zertifikate erstellen/konfigurieren
setup_ssl() {
    local domain=$1
    local cert_dir=$2
    
    print_info "Konfiguriere SSL für $domain..."
    
    mkdir -p $cert_dir
    
    # Prüfen, ob Zertifikate bereits existieren
    if [[ -f "${cert_dir}/fullchain.pem" && -f "${cert_dir}/privkey.pem" ]]; then
        print_success "SSL-Zertifikate für $domain existieren bereits."
        return
    fi
    
    # Abfragen, ob vorhandene Zertifikate verwendet oder selbstsignierte Zertifikate erstellt werden sollen
    echo -e "\nBitte wählen Sie eine Option für SSL-Zertifikate für $domain:"
    echo "1) Vorhandene Zertifikate verwenden (z.B. Let's Encrypt)"
    echo "2) Selbstsignierte Zertifikate erstellen (für Entwicklung/Test)"
    read -p "Option (1-2): " ssl_option
    
    case $ssl_option in
        1)
            read -p "Pfad zu certificate.pem/fullchain.pem: " cert_path
            read -p "Pfad zu privkey.pem: " key_path
            
            # Prüfen, ob die Dateien existieren
            if [[ ! -f "$cert_path" || ! -f "$key_path" ]]; then
                print_error "Eine oder beide Zertifikatsdateien wurden nicht gefunden."
                exit 1
            fi
            
            # Kopieren der Zertifikate
            cp "$cert_path" "${cert_dir}/fullchain.pem"
            cp "$key_path" "${cert_dir}/privkey.pem"
            print_success "Zertifikate erfolgreich kopiert."
            ;;
        2)
            print_info "Erstelle selbstsignierte Zertifikate..."
            # SSL-Konfiguration erstellen
            cat > "${cert_dir}/openssl.cnf" << EOF
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
C = CH
ST = Zurich
L = Zurich
O = SwissAirDry
OU = Development
CN = ${domain}

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = ${domain}
DNS.2 = www.${domain}
DNS.3 = *.${domain}
EOF
            
            # Selbstsignierte Zertifikate erstellen
            openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
                -keyout "${cert_dir}/privkey.pem" \
                -out "${cert_dir}/fullchain.pem" \
                -config "${cert_dir}/openssl.cnf"
            
            if [[ $? -eq 0 ]]; then
                print_success "Selbstsignierte Zertifikate erfolgreich erstellt."
            else
                print_error "Erstellung der selbstsignierten Zertifikate fehlgeschlagen."
                exit 1
            fi
            ;;
        *)
            print_error "Ungültige Option. Bitte 1 oder 2 wählen."
            exit 1
            ;;
    esac
}

# Nextcloud Docker Compose Datei erstellen
create_nextcloud_docker_compose() {
    local install_dir=$1
    local nextcloud_volume="${install_dir}/nextcloud_data"
    local db_volume="${install_dir}/db_data"
    local redis_volume="${install_dir}/redis_data"
    
    print_info "Erstelle Nextcloud Docker Compose Konfiguration..."
    
    mkdir -p "${install_dir}"
    mkdir -p "${nextcloud_volume}"
    mkdir -p "${db_volume}"
    mkdir -p "${redis_volume}"
    
    # Docker Compose Datei erstellen
    cat > "${install_dir}/docker-compose.yml" << EOF
version: '3'

services:
  db:
    image: mariadb:10.6
    container_name: nextcloud_db
    restart: always
    volumes:
      - ${db_volume}:/var/lib/mysql
    environment:
      - MYSQL_ROOT_PASSWORD=\${MYSQL_ROOT_PASSWORD}
      - MYSQL_PASSWORD=\${MYSQL_PASSWORD}
      - MYSQL_DATABASE=\${MYSQL_DATABASE}
      - MYSQL_USER=\${MYSQL_USER}

  redis:
    image: redis:alpine
    container_name: nextcloud_redis
    restart: always
    volumes:
      - ${redis_volume}:/data

  app:
    image: nextcloud:latest
    container_name: nextcloud_app
    restart: always
    volumes:
      - ${nextcloud_volume}:/var/www/html
    environment:
      - MYSQL_HOST=db
      - MYSQL_PASSWORD=\${MYSQL_PASSWORD}
      - MYSQL_DATABASE=\${MYSQL_DATABASE}
      - MYSQL_USER=\${MYSQL_USER}
      - REDIS_HOST=redis
      - NEXTCLOUD_ADMIN_USER=\${NEXTCLOUD_ADMIN_USER}
      - NEXTCLOUD_ADMIN_PASSWORD=\${NEXTCLOUD_ADMIN_PASSWORD}
      - NEXTCLOUD_TRUSTED_DOMAINS=\${NEXTCLOUD_TRUSTED_DOMAINS}
    depends_on:
      - db
      - redis
    ports:
      - "8080:80"

networks:
  default:
    external:
      name: swissairdry_network
EOF
    
    print_success "Nextcloud Docker Compose Konfiguration erstellt in ${install_dir}/docker-compose.yml"
}

# SwissAirDry Docker Compose Datei erstellen
create_swissairdry_docker_compose() {
    local install_dir=$1
    
    print_info "Erstelle SwissAirDry Docker Compose Konfiguration..."
    
    mkdir -p "${install_dir}/mqtt/config"
    mkdir -p "${install_dir}/mqtt/data"
    mkdir -p "${install_dir}/mqtt/log"
    mkdir -p "${install_dir}/api"
    mkdir -p "${install_dir}/nginx/conf.d"
    mkdir -p "${install_dir}/nginx/ssl"
    mkdir -p "${install_dir}/postgres/data"
    
    # Mosquitto Konfiguration erstellen
    cat > "${install_dir}/mqtt/config/mosquitto.conf" << EOF
# Mosquitto Konfiguration für SwissAirDry
persistence true
persistence_location /mosquitto/data
log_dest file /mosquitto/log/mosquitto.log
log_dest stdout

# Listener für unverschlüsselte Verbindungen (nur für lokale Verbindungen)
listener 1883
allow_anonymous true

# Listener für verschlüsselte Verbindungen
listener 8883
certfile /mosquitto/certs/fullchain.pem
keyfile /mosquitto/certs/privkey.pem
require_certificate false
EOF
    
    # Nginx Konfiguration erstellen
    cat > "${install_dir}/nginx/conf.d/default.conf" << EOF
# Nginx Konfiguration für SwissAirDry
# API Backend
server {
    listen 80;
    listen [::]:80;
    server_name api.\${DOMAIN};

    location / {
        return 301 https://api.\${DOMAIN}\$request_uri;
    }
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.\${DOMAIN};

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305';

    location / {
        proxy_pass http://api:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

# Nextcloud Frontend
server {
    listen 80;
    listen [::]:80;
    server_name \${DOMAIN};

    location / {
        return 301 https://\${DOMAIN}\$request_uri;
    }
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name \${DOMAIN};

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305';

    location / {
        proxy_pass http://nextcloud_app:80;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    
    # Docker Compose Datei erstellen
    cat > "${install_dir}/docker-compose.yml" << EOF
version: '3'

services:
  # MQTT Broker
  mqtt:
    image: eclipse-mosquitto:latest
    container_name: swissairdry_mqtt
    restart: always
    ports:
      - "1883:1883"
      - "8883:8883"
    volumes:
      - ${install_dir}/mqtt/config:/mosquitto/config
      - ${install_dir}/mqtt/data:/mosquitto/data
      - ${install_dir}/mqtt/log:/mosquitto/log
      - ${install_dir}/nginx/ssl:/mosquitto/certs:ro
    networks:
      - swissairdry_network

  # PostgreSQL Datenbank
  postgres:
    image: postgres:14-alpine
    container_name: swissairdry_postgres
    restart: always
    volumes:
      - ${install_dir}/postgres/data:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD=\${POSTGRES_PASSWORD}
      - POSTGRES_USER=\${POSTGRES_USER}
      - POSTGRES_DB=\${POSTGRES_DB}
    ports:
      - "5432:5432"
    networks:
      - swissairdry_network

  # SwissAirDry API
  api:
    build:
      context: ./api
      dockerfile: Dockerfile
    container_name: swissairdry_api
    restart: always
    volumes:
      - ${install_dir}/api:/app
    environment:
      - DATABASE_URL=postgresql://\${POSTGRES_USER}:\${POSTGRES_PASSWORD}@postgres:5432/\${POSTGRES_DB}
      - MQTT_HOST=mqtt
      - MQTT_PORT=1883
      - NEXTCLOUD_URL=https://\${DOMAIN}
      - NEXTCLOUD_USER=\${NEXTCLOUD_ADMIN_USER}
      - NEXTCLOUD_PASSWORD=\${NEXTCLOUD_ADMIN_PASSWORD}
    depends_on:
      - postgres
      - mqtt
    networks:
      - swissairdry_network

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: swissairdry_nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ${install_dir}/nginx/conf.d:/etc/nginx/conf.d
      - ${install_dir}/nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
    networks:
      - swissairdry_network

networks:
  swissairdry_network:
    external: true
EOF
    
    # API Dockerfile erstellen
    mkdir -p "${install_dir}/api"
    cat > "${install_dir}/api/Dockerfile" << EOF
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "run.py"]
EOF
    
    # API requirements.txt erstellen
    cat > "${install_dir}/api/requirements.txt" << EOF
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.4.2
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
paho-mqtt==2.2.1
python-dotenv==1.0.0
requests==2.31.0
python-multipart==0.0.6
pandas==2.1.3
aiofiles==23.2.1
httpx==0.25.1
jinja2==3.1.2
itsdangerous==2.1.2
bcrypt==4.0.1
passlib==1.7.4
python-jose==3.3.0
python-dateutil==2.8.2
pytz==2023.3.post1
EOF
    
    print_success "SwissAirDry Docker Compose Konfiguration erstellt in ${install_dir}/docker-compose.yml"
}

# Umgebungsvariablen-Datei erstellen
create_env_file() {
    local install_dir=$1
    local domain=$2
    
    print_info "Erstelle Umgebungsvariablen-Datei..."
    
    # Passwörter generieren
    MYSQL_ROOT_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)
    MYSQL_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)
    POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)
    NEXTCLOUD_ADMIN_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)
    
    # .env-Datei erstellen
    cat > "${install_dir}/.env" << EOF
# Allgemeine Konfiguration
DOMAIN=${domain}

# Nextcloud Konfiguration
NEXTCLOUD_ADMIN_USER=admin
NEXTCLOUD_ADMIN_PASSWORD=${NEXTCLOUD_ADMIN_PASSWORD}
NEXTCLOUD_TRUSTED_DOMAINS=${domain}

# MySQL (Nextcloud) Konfiguration
MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
MYSQL_PASSWORD=${MYSQL_PASSWORD}
MYSQL_DATABASE=nextcloud
MYSQL_USER=nextcloud

# PostgreSQL (SwissAirDry) Konfiguration
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_USER=swissairdry
POSTGRES_DB=swissairdry

# MQTT Konfiguration
MQTT_HOST=mqtt
MQTT_PORT=1883
EOF
    
    print_success "Umgebungsvariablen-Datei erstellt in ${install_dir}/.env"
    print_warning "WICHTIG: Bewahren Sie die generierten Passwörter sicher auf!"
    print_warning "Nextcloud Admin-Passwort: ${NEXTCLOUD_ADMIN_PASSWORD}"
    print_warning "MySQL Root-Passwort: ${MYSQL_ROOT_PASSWORD}"
    print_warning "PostgreSQL Passwort: ${POSTGRES_PASSWORD}"
}

# Start der Installation

# Prüfen, ob das Skript als root ausgeführt wird
if [[ $EUID -ne 0 ]]; then
    print_error "Dieses Skript muss als root ausgeführt werden."
    exit 1
fi

print_info "Willkommen bei der SwissAirDry-Installation!"
print_info "Dieses Skript installiert den gesamten SwissAirDry-Stack mit Nextcloud."

# Erforderliche Abhängigkeiten prüfen und installieren
print_info "Prüfe und installiere erforderliche Abhängigkeiten..."
check_and_install_dependency "curl"
check_and_install_dependency "openssl"
check_and_install_dependency "docker"
check_and_install_dependency "docker-compose"

# Installationsverzeichnis erfragen
read -p "Bitte geben Sie das Installationsverzeichnis an (Standard: /opt/swissairdry): " install_dir
install_dir=${install_dir:-/opt/swissairdry}

# Domain-Namen erfragen
read -p "Bitte geben Sie Ihren Domain-Namen an (z.B. swissairdry.example.com): " domain_name

# Prüfen, ob bereits Installationsdaten vorhanden sind
if [ -d "$install_dir" ]; then
    print_warning "Das Verzeichnis $install_dir existiert bereits."
    read -p "Möchten Sie vorhandene Installationsdaten entfernen und neu installieren? (j/n): " remove_existing
    
    if [[ "$remove_existing" == "j" || "$remove_existing" == "J" ]]; then
        print_info "Entferne vorhandene Daten..."
        
        # Stoppe laufende Container
        if [ -f "${install_dir}/docker-compose.yml" ]; then
            cd "$install_dir"
            docker-compose down -v
        fi
        
        if [ -f "${install_dir}/nextcloud/docker-compose.yml" ]; then
            cd "${install_dir}/nextcloud"
            docker-compose down -v
        fi
        
        # Entferne alte Daten
        rm -rf "$install_dir"
        print_success "Vorhandene Daten wurden entfernt."
    else
        print_error "Installation abgebrochen, um Daten zu schützen. Bitte wählen Sie ein anderes Verzeichnis."
        exit 1
    fi
fi

# Verzeichnisse erstellen
mkdir -p $install_dir
mkdir -p "${install_dir}/nginx/ssl"

# Docker-Netzwerk erstellen
print_info "Erstelle Docker-Netzwerk..."
if ! docker network inspect swissairdry_network &> /dev/null; then
    docker network create swissairdry_network
    print_success "Docker-Netzwerk 'swissairdry_network' erstellt."
else
    print_success "Docker-Netzwerk 'swissairdry_network' existiert bereits."
fi

# SSL-Zertifikate einrichten
setup_ssl "$domain_name" "${install_dir}/nginx/ssl"

# Nextcloud Docker Compose erstellen
create_nextcloud_docker_compose "${install_dir}/nextcloud"

# SwissAirDry Docker Compose erstellen
create_swissairdry_docker_compose "$install_dir"

# Umgebungsvariablen-Datei erstellen
create_env_file "$install_dir" "$domain_name"

# Starten der Dienste
print_info "Möchten Sie die Dienste jetzt starten? (j/n): "
read start_services

if [[ "$start_services" == "j" || "$start_services" == "J" ]]; then
    print_info "Starte SwissAirDry-Dienste..."
    
    # Kopieren der .env-Datei in das Nextcloud-Verzeichnis
    cp "${install_dir}/.env" "${install_dir}/nextcloud/.env"
    
    # Starten der SwissAirDry-Dienste
    cd "$install_dir"
    docker-compose up -d
    
    # Starten der Nextcloud
    cd "${install_dir}/nextcloud"
    docker-compose up -d
    
    print_success "Alle Dienste wurden gestartet!"
    print_info "SwissAirDry ist verfügbar unter: https://$domain_name"
    print_info "SwissAirDry API ist verfügbar unter: https://api.$domain_name"
    print_info "Nextcloud ist verfügbar unter: https://$domain_name"
else
    print_info "Sie können die Dienste später mit folgenden Befehlen starten:"
    print_info "cd $install_dir && docker-compose up -d"
    print_info "cd ${install_dir}/nextcloud && docker-compose up -d"
fi

print_success "Installation abgeschlossen!"
print_info "Bitte sehen Sie in die Datei $install_dir/.env für die generierten Passwörter."
print_info "Für weitere Informationen und Fehlerbehebung besuchen Sie: https://github.com/swissairdry/docs"