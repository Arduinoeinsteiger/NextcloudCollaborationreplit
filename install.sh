#!/bin/bash
# Installation und Setup-Skript für SwissAirDry

# Farbkodierung
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== SwissAirDry Installation ===${NC}"
echo -e "${BLUE}=================================${NC}\n"

# Überprüfen, ob Docker installiert ist
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker ist nicht installiert.${NC}"
    echo -e "${YELLOW}Bitte installieren Sie Docker und Docker Compose:${NC}"
    echo "curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "sudo sh get-docker.sh"
    echo "sudo apt-get install -y docker-compose-plugin"
    exit 1
fi

# Überprüfen, ob .env-Datei existiert
if [ ! -f .env ]; then
    echo -e "${YELLOW}Keine .env-Datei gefunden. Es wird eine Beispiel-Datei erstellt.${NC}"
    echo -e "${YELLOW}Bitte passen Sie die .env-Datei an Ihre Umgebung an.${NC}"
    cp .env.example .env
fi

# Verzeichnisstruktur erstellen
echo -e "${BLUE}Erstelle Verzeichnisstruktur...${NC}"
chmod +x mkdir.sh
./mkdir.sh

# SSL-Zertifikate überprüfen
if [ ! -f "./ssl/certs/vgnc.org.cert.pem" ] || [ ! -f "./ssl/private/vgnc.org.key.pem" ]; then
    echo -e "${YELLOW}SSL-Zertifikate nicht gefunden.${NC}"
    echo -e "${YELLOW}Bitte fügen Sie Ihre SSL-Zertifikate hinzu oder setzen Sie in .env SSL_ENABLED=false${NC}"
    
    # Kopieren Sie die SSL-Zertifikate aus den bereitgestellten Dateien
    read -p "Möchten Sie die bereitgestellten SSL-Zertifikate verwenden? (j/n): " use_provided_ssl
    if [[ $use_provided_ssl == "j" ]]; then
        mkdir -p ssl/certs ssl/private
        echo "-----BEGIN CERTIFICATE-----
MIIEnDCCA4SgAwIBAgIUC5fhFswAbK1QniZMT/WBz/kSJBUwDQYJKoZIhvcNAQEL
BQAwgYsxCzAJBgNVBAYTAlVTMRkwFwYDVQQKExBDbG91ZEZsYXJlLCBJbmMuMTQw
MgYDVQQLEytDbG91ZEZsYXJlIE9yaWdpbiBTU0wgQ2VydGlmaWNhdGUgQXV0aG9y
aXR5MRYwFAYDVQQHEw1TYW4gRnJhbmNpc2NvMRMwEQYDVQQIEwpDYWxpZm9ybmlh
MB4XDTI1MDQxNjA5MDcwMFoXDTQwMDQxMjA5MDcwMFowYjEZMBcGA1UEChMQQ2xv
dWRGbGFyZSwgSW5jLjEdMBsGA1UECxMUQ2xvdWRGbGFyZSBPcmlnaW4gQ0ExJjAk
BgNVBAMTHUNsb3VkRmxhcmUgT3JpZ2luIENlcnRpZmljYXRlMIIBIjANBgkqhkiG
9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwFYRY28fCNjQQLIUGJMgzGG1ZsBL5ah9MFTj
WWpUYVEDpcCaHF2OlHPpPLBPT9n1DbKY/IaRtSOro5/R7LvKU6wq7eAcPPtVI5i6
6q2whsdTgUzaAkqRnfRUfl3Z5BwE+3/+4XwcAgytYd2x3pJwWIW0HVZ5ImkQkYvG
m/QikJZKlVocjeLvbFCq2poYeWzi+vvELQV8xBNpXN/kn15Kg/93IqXZMOL1mXJK
M5fmgvjML3gcR3Wi+8NQ14BT0jH7NDBVVkNoRtXJuiTsCjEMTJlD+uKqDgKyF/KB
ghZ5Ztd+//lsVuRWUFAz5gsGzSpM24lL1v8U375ryhkMMNxaSwIDAQABo4IBHjCC
ARowDgYDVR0PAQH/BAQDAgWgMB0GA1UdJQQWMBQGCCsGAQUFBwMCBggrBgEFBQcD
ATAMBgNVHRMBAf8EAjAAMB0GA1UdDgQWBBS4yZqPCGz9VnBd+pIgWnzoIxF1ojAf
BgNVHSMEGDAWgBQk6FNXXXw0QIep65TbuuEWePwppDBABggrBgEFBQcBAQQ0MDIw
MAYIKwYBBQUHMAGGJGh0dHA6Ly9vY3NwLmNsb3VkZmxhcmUuY29tL29yaWdpbl9j
YTAfBgNVHREEGDAWggoqLnZnbmMub3Jnggh2Z25jLm9yZzA4BgNVHR8EMTAvMC2g
K6AphidodHRwOi8vY3JsLmNsb3VkZmxhcmUuY29tL29yaWdpbl9jYS5jcmwwDQYJ
KoZIhvcNAQELBQADggEBAJgam0RFtz6l7BTwOOiGRosp2XONUX/dDL8WAsGaZxGU
aYxTH7wFjZxI7J/4yVYiu9LnpVkfcm9GhbZ2JJg83XkoIXih1uVYyyzd41FytRLS
d3J4ep8C5SC00DLsFxP5S0RtWqZenB0nZ24lwl7WERA6Ata9CvKbYuHmYx+7u6Pd
UGjQ4CoO7lrL+dl4Qn4XWRW72Mwl/z+es+ZBUTlhyHkfT0NQYo+O3U//PmjMFWJb
0xm2kjwA+lebZmUaJYeeRV6ZmQCv5D9RwAhSuFZPj1AOGgsHLdNetKiTFM02jLIB
5C++W8bV8OMgZBlOgGhdDQTghytvX3UlhbhuXvpqlLU=
-----END CERTIFICATE-----" > ssl/certs/vgnc.org.cert.pem

        echo "-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDAVhFjbx8I2NBA
shQYkyDMYbVmwEvlqH0wVONZalRhUQOlwJocXY6Uc+k8sE9P2fUNspj8hpG1I6uj
n9Hsu8pTrCrt4Bw8+1UjmLrqrbCGx1OBTNoCSpGd9FR+XdnkHAT7f/7hfBwCDK1h
3bHeknBYhbQdVnkiaRCRi8ab9CKQlkqVWhyN4u9sUKramhh5bOL6+8QtBXzEE2lc
3+SfXkqD/3cipdkw4vWZckozl+aC+MwveBxHdaL7w1DXgFPSMfs0MFVWQ2hG1cm6
JOwKMQxMmUP64qoOArIX8oGCFnlm137/+WxW5FZQUDPmCwbNKkzbiUvW/xTfvmvK
GQww3FpLAgMBAAECggEAT0XKEe0VYfyWzOt4y+4sGQD2ltyQC56HxpleQRbJo3iU
I8d/3UwUPYyOp6RVdCh1z4j6dC50tK94iU6QY928lQMDiJqTmPDQFQVYmOwws0RJ
XyQRQNuCLBOtlY3SBiokRZJqN36DPrcB6THKI13A70NgSq0+7RdXrF1rZRDZBDUt
gbm1B6lODJrsL+F7qee9kiClSPZrL2Z/hjg7lpQ+FiZH4jwg+s1UXuHd8pNib/Kh
klPOBknTD6gViJ7reW2doC8nbYVii3JX6EL/Wi1j9jLztlLujKAAwsMKo7uW0YTw
DEOtbriThn+HUPv9MYvGLCsDWXLZiBJXwIf6/8lwhQKBgQD4Ww7aWeR5glohcCS3
9CX1137PtoKRpP1nn1eGhj3A4Z4n1jK3crPYBREcIHEtrea8VQz/GyXJ8UaAWwJJ
+6+2qb8FCl74WOei+Mc1OKHi5M1kl3ypNevtH46wkZ5O1v4cHfm6sUtKQDdfXLX4
lK2VmDxxxHVCZEGWVLTd401qRQKBgQDGQZlcHGbFqHIbDYkIZ7aMEmcoWwxvTOJM
b02s8pHZMGHGGl2186v75kWfBdZINWwfBHsBGZrYIZ2qiWMIE5mATX7KHizHJuVA
4jc+fcWF5lSfnd5BGvm7SpIZpwWS8NMe/AbGxebRExYsbh6ewsXbIX4NyB6dEEGb
MAwil07DTwKBgBS6lOzIn/c8WAV+dLId4KU6TU1M8Gzzlmr1s7p4reLRcf/lMup4
2mXnVlxAoPGtGBsUBjesrmTCjJ3d+rzuEuZuGJF1IiQcV4kUtpvMlEZ5zmLc+fyt
kXmDLsex/8KY0zDJl7RrY9tYrMZ62H1c+3gG8tSUDy1xbL/9ZfM3K5j5AoGAA/Qs
9cxPNGPumqGDeRpwZoy7Z++g6NtUrAeQOgHAbN9tI8FE2ysX4/csrkY0hs4h8OBq
/5OeJe9NsKf6xJ93cTqaa7d8VyBsdAXO6j0h4lC8oU5Jr2y1TEnpbf+Juet5mmWW
UQKDXuoNiCdODwZ9YahiVi4GhkVbuZeUtl/kHzsCgYB1XjMCXvzT6NMS7f1Ztg4+
qRtWwrQrQ+JszraKzr9zi0N3AkN/TJloXSgiyGMbQvbIWgFB52fEF2nJV8jkulLc
amHH46R5ILtZual5Na5ZylOaoIU7uUXLEUBql/wK5YfOnv7m//UIRa3p4sbby8We
CZ+QZW4jyWgC+sfi33mYHg==
-----END PRIVATE KEY-----" > ssl/private/vgnc.org.key.pem
        
        echo -e "${GREEN}SSL-Zertifikate erfolgreich erstellt.${NC}"
    else
        echo -e "${YELLOW}Bitte fügen Sie Ihre eigenen SSL-Zertifikate hinzu.${NC}"
    fi
fi

# Nginx-Konfiguration erstellen
echo -e "${BLUE}Erstelle Nginx-Konfiguration...${NC}"
cat > nginx/nginx.conf << 'EOF'
user  nginx;
worker_processes  auto;

error_log  /var/log/nginx/error.log notice;
pid        /var/run/nginx.pid;

events {
    worker_connections  1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile        on;
    #tcp_nopush     on;

    keepalive_timeout  65;

    #gzip  on;

    include /etc/nginx/conf.d/*.conf;
}
EOF

cat > nginx/conf.d/default.conf << 'EOF'
# HTTP-Redirect
server {
    listen 80;
    listen [::]:80;
    server_name _;
    
    return 301 https://$host$request_uri;
}

# HTTPS Server für Hauptwebsite (Nextcloud)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name vgnc.org www.vgnc.org;

    ssl_certificate /etc/ssl/certs/vgnc.org.cert.pem;
    ssl_certificate_key /etc/ssl/private/vgnc.org.key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;

    # HSTS (optional, vorsichtig einsetzen)
    # add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Reverse Proxy zu Nextcloud
    location / {
        proxy_pass http://nextcloud:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        
        # Websockets für Nextcloud Talk
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        client_max_body_size 10G;
        proxy_buffering off;
        proxy_request_buffering off;
    }
}

# HTTPS Server für API
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.vgnc.org;

    ssl_certificate /etc/ssl/certs/vgnc.org.cert.pem;
    ssl_certificate_key /etc/ssl/private/vgnc.org.key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;

    # CORS-Header hinzufügen
    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'Origin, X-Requested-With, Content-Type, Accept, Authorization, X-API-Key' always;
    
    # Preflight requests
    if ($request_method = 'OPTIONS') {
        add_header 'Access-Control-Allow-Origin' '*';
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS';
        add_header 'Access-Control-Allow-Headers' 'Origin, X-Requested-With, Content-Type, Accept, Authorization, X-API-Key';
        add_header 'Access-Control-Max-Age' 1728000;
        add_header 'Content-Type' 'text/plain charset=UTF-8';
        add_header 'Content-Length' 0;
        return 204;
    }

    # Reverse Proxy zur API
    location / {
        proxy_pass http://api:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        client_max_body_size 10M;
    }
}

# HTTPS Server für Nextcloud ExApp
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name exapp.vgnc.org;

    ssl_certificate /etc/ssl/certs/vgnc.org.cert.pem;
    ssl_certificate_key /etc/ssl/private/vgnc.org.key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;

    # Reverse Proxy zur ExApp
    location / {
        proxy_pass http://exapp:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        client_max_body_size 10M;
    }
}
EOF

# MQTT-Konfiguration erstellen
echo -e "${BLUE}Erstelle MQTT-Konfiguration...${NC}"
cat > swissairdry/mqtt/mosquitto.conf << 'EOF'
# SwissAirDry MQTT-Broker Konfiguration

# Netzwerk-Einstellungen
listener 1883
listener 9001
protocol websockets

# Persistenz und Logging
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
log_type all

# Sicherheit (kann später aktiviert werden)
# allow_anonymous false
# password_file /mosquitto/config/mosquitto.passwd

# Erweiterte Einstellungen
max_connections -1
max_packet_size 0
max_inflight_messages 40
max_queued_messages 1000
queue_qos0_messages false
EOF

# .env.example erstellen
echo -e "${BLUE}Erstelle .env.example...${NC}"
cat > .env.example << 'EOF'
# SwissAirDry Umgebungsvariablen (.env.example)

# API-Server-Konfiguration
HOST=0.0.0.0
PORT=5000
API_URL=https://api.vgnc.org
API_SECRET_KEY=change_me_to_secure_key
DEBUG=False
LOG_LEVEL=INFO

# MQTT-Konfiguration
MQTT_HOST=mqtt
MQTT_PORT=1883
MQTT_USER=
MQTT_PASSWORD=
MQTT_TOPIC_PREFIX=swissairdry/
MQTT_WEBSOCKET_PORT=9001

# Datenbank-Konfiguration
PGHOST=db
PGPORT=5432
PGDATABASE=swissairdry
PGUSER=swissairdry
PGPASSWORD=change_me_to_secure_password
DATABASE_URL=postgresql://swissairdry:change_me_to_secure_password@db:5432/swissairdry

# Domain-Konfiguration
DOMAIN=vgnc.org
API_DOMAIN=api.vgnc.org
MQTT_DOMAIN=mqtt.vgnc.org
NEXTCLOUD_DOMAIN=vgnc.org

# Docker-Konfiguration
DOCKER_REGISTRY=ghcr.io
DOCKER_IMAGE=swissairdry/nextcloud-exapp
DOCKER_TAG=2.1.0

# Nextcloud-Konfiguration
NEXTCLOUD_APP_VERSION=2.1.0
NEXTCLOUD_MIN_VERSION=27
NEXTCLOUD_MAX_VERSION=29
NEXTCLOUD_PORT=8080
NEXTCLOUD_ADMIN_USER=admin
NEXTCLOUD_ADMIN_PASSWORD=change_me_to_secure_password

# SSL-Konfiguration
SSL_ENABLED=true
SSL_CERT_PATH=/etc/ssl/certs/vgnc.org.cert.pem
SSL_KEY_PATH=/etc/ssl/private/vgnc.org.key.pem

# Sicherheits-Einstellungen
JWT_SECRET=change_me_to_secure_jwt_secret
SESSION_SECRET=change_me_to_secure_session_secret
CORS_ALLOWED_ORIGINS=https://vgnc.org,https://www.vgnc.org,https://api.vgnc.org

# Benachrichtigungs-Einstellungen
NOTIFICATIONS_ENABLED=true
EMAIL_SMTP_HOST=smtp.example.com
EMAIL_SMTP_PORT=587
EMAIL_USER=
EMAIL_PASSWORD=
EMAIL_FROM=noreply@vgnc.org

# ESP-Geräte-Konfiguration
ESP_UPDATE_ENDPOINT=https://api.vgnc.org/esp/update
ESP_OTA_ENABLED=true
ESP_DEFAULT_PIN_CONFIGURATION=ESP32C6

# Bexio-Integration (falls verwendet)
BEXIO_API_URL=https://api.bexio.com/2.0
BEXIO_CLIENT_ID=
BEXIO_CLIENT_SECRET=
EOF

# Installation abschließen
echo -e "\n${GREEN}Installation abgeschlossen!${NC}"
echo -e "${YELLOW}Bitte passen Sie die Datei .env an Ihre Umgebung an.${NC}"
echo -e "${YELLOW}Führen Sie anschließend 'docker-compose up -d' aus, um das System zu starten.${NC}"
echo -e "\n${BLUE}=== SwissAirDry Installation abgeschlossen ===${NC}"