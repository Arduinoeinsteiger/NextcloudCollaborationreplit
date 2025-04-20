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

# Funktion zum Überprüfen, ob ein Port bereits verwendet wird
check_port_usage() {
    local port=$1
    if netstat -tuln | grep -q ":$port "; then
        return 0  # Port wird verwendet
    else
        return 1  # Port ist frei
    fi
}

# Funktion zum Finden des nächsten freien Ports
find_next_free_port() {
    local start_port=$1
    local current_port=$start_port
    
    while check_port_usage $current_port; do
        print_warning "Port $current_port wird bereits verwendet, versuche den nächsten Port..."
        current_port=$((current_port + 1))
    done
    
    echo $current_port
}

# Funktion zum Testen von Verbindungen
test_connection() {
    local host=$1
    local port=$2
    local service_name=$3
    
    print_info "Teste Verbindung zu $service_name ($host:$port)..."
    
    # Versuche, eine TCP-Verbindung zum angegebenen Host und Port herzustellen
    if timeout 5 bash -c "echo > /dev/tcp/$host/$port" &>/dev/null; then
        print_success "Verbindung zu $service_name ($host:$port) erfolgreich."
        return 0
    else
        print_error "Verbindung zu $service_name ($host:$port) fehlgeschlagen."
        return 1
    fi
}

# Funktion zum Ermitteln der öffentlichen IP-Adressen
get_public_ips() {
    print_info "Ermittle öffentliche IP-Adressen..."
    
    # IPv4-Adresse ermitteln
    local ipv4=$(curl -s -4 https://api.ipify.org 2>/dev/null || curl -s -4 https://ifconfig.me 2>/dev/null || curl -s -4 https://icanhazip.com 2>/dev/null)
    if [ -z "$ipv4" ]; then
        print_warning "Konnte keine öffentliche IPv4-Adresse ermitteln. Verwende lokale Adresse."
        ipv4=$(ip -4 addr show scope global | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -n 1)
    fi
    
    # IPv6-Adresse ermitteln
    local ipv6=$(curl -s -6 https://api6.ipify.org 2>/dev/null || curl -s -6 https://ifconfig.co 2>/dev/null || curl -s -6 https://icanhazip.com 2>/dev/null)
    if [ -z "$ipv6" ]; then
        print_warning "Konnte keine öffentliche IPv6-Adresse ermitteln. Verwende lokale Adresse."
        ipv6=$(ip -6 addr show scope global | grep -oP '(?<=inet6\s)[\da-f:]+' | head -n 1)
    fi
    
    if [ -n "$ipv4" ]; then
        print_success "Öffentliche IPv4-Adresse: $ipv4"
    else
        print_error "Konnte keine IPv4-Adresse ermitteln."
        ipv4="127.0.0.1"
    fi
    
    if [ -n "$ipv6" ]; then
        print_success "Öffentliche IPv6-Adresse: $ipv6"
    else
        print_warning "Konnte keine IPv6-Adresse ermitteln. IPv6 wird nicht konfiguriert."
    fi
    
    # Array mit IPv4 und IPv6 zurückgeben
    echo "$ipv4 $ipv6"
}

# Funktion zum Konfigurieren von Cloudflare DNS
configure_cloudflare() {
    local domain=$1
    local ip=$2
    
    print_info "Konfiguriere Cloudflare DNS für Domain $domain..."
    
    # Fragen nach Cloudflare API-Token
    print_info "Für die automatische Konfiguration von Cloudflare DNS-Einträgen wird ein API-Token benötigt."
    print_info "Dieses Token benötigt Berechtigungen für 'Zone:DNS:Edit' und 'Zone:Zone:Read'."
    print_info "Sie können ein Token erstellen unter: https://dash.cloudflare.com/profile/api-tokens"
    
    read -p "Möchten Sie Cloudflare automatisch konfigurieren? (j/n): " use_cloudflare
    
    if [[ "$use_cloudflare" != "j" && "$use_cloudflare" != "J" ]]; then
        print_info "Cloudflare-Konfiguration übersprungen."
        return
    fi
    
    # Installiere jq, falls nicht vorhanden
    if ! command -v jq &>/dev/null; then
        print_info "Installiere jq für JSON-Verarbeitung..."
        apt-get update && apt-get install -y jq
    fi
    
    # Token abfragen und validieren, Zone ID automatisch ermitteln
    local token_valid=false
    local cf_token=""
    local cf_zone_id=""
    
    while [ "$token_valid" = false ]; do
        read -sp "Bitte geben Sie Ihren Cloudflare API-Token ein: " cf_token
        echo ""
        
        print_info "Teste Cloudflare API-Token..."
        # Zuerst prüfen wir, ob der Token gültig ist, indem wir alle Zonen abfragen
        local zones_response=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?per_page=50" \
            -H "Authorization: Bearer $cf_token" \
            -H "Content-Type: application/json")
        
        local success=$(echo "$zones_response" | jq -r '.success')
        
        if [[ "$success" == "true" ]]; then
            # Token ist gültig, jetzt versuchen wir die Zone für die angegebene Domain zu finden
            print_success "API-Token ist gültig."
            print_info "Suche nach Zone für Domain $domain..."
            
            local zone_count=$(echo "$zones_response" | jq -r '.result | length')
            if [[ "$zone_count" -eq 0 ]]; then
                print_error "Keine Zonen mit diesem API-Token gefunden. Stellen Sie sicher, dass der Token Zugriff auf die richtigen Zonen hat."
                read -p "Möchten Sie es erneut versuchen? (j/n): " retry
                if [[ "$retry" != "j" && "$retry" != "J" ]]; then
                    print_info "Cloudflare-Konfiguration übersprungen."
                    return
                fi
                continue
            fi
            
            # Alle Zonen anzeigen und nach passender Domain suchen
            local found=false
            local zones_info=""
            
            # Zonen-Liste erstellen
            for i in $(seq 0 $(($zone_count - 1))); do
                local zone_name=$(echo "$zones_response" | jq -r ".result[$i].name")
                local zone_id=$(echo "$zones_response" | jq -r ".result[$i].id")
                local zone_status=$(echo "$zones_response" | jq -r ".result[$i].status")
                
                zones_info+="$i) $zone_name (ID: $zone_id, Status: $zone_status)"$'\n'
                
                # Prüfen, ob die Domain gleich oder eine Subdomain der Zone ist
                if [[ "$domain" == "$zone_name" || "$domain" == *".$zone_name" ]]; then
                    cf_zone_id=$zone_id
                    found=true
                    print_success "Zone für $domain automatisch gefunden: $zone_name (ID: $cf_zone_id)"
                    token_valid=true
                    break
                fi
            done
            
            # Wenn keine passende Zone gefunden wurde, dem Benutzer erlauben, eine auszuwählen
            if [[ "$found" == "false" ]]; then
                print_warning "Keine automatisch passende Zone für $domain gefunden."
                echo "Verfügbare Zonen:"
                echo "$zones_info"
                read -p "Wählen Sie die Nummer der passenden Zone (oder drücken Sie Enter zum Abbrechen): " zone_number
                
                if [[ -z "$zone_number" ]]; then
                    print_info "Cloudflare-Konfiguration übersprungen."
                    return
                elif [[ "$zone_number" -ge 0 && "$zone_number" -lt "$zone_count" ]]; then
                    cf_zone_id=$(echo "$zones_response" | jq -r ".result[$zone_number].id")
                    local selected_zone_name=$(echo "$zones_response" | jq -r ".result[$zone_number].name")
                    print_success "Zone ausgewählt: $selected_zone_name (ID: $cf_zone_id)"
                    token_valid=true
                else
                    print_error "Ungültige Auswahl. Bitte erneut versuchen."
                fi
            fi
        else
            local error_message=$(echo "$zones_response" | jq -r '.errors[0].message')
            print_error "API-Token ungültig: $error_message"
            read -p "Möchten Sie es erneut versuchen? (j/n): " retry
            if [[ "$retry" != "j" && "$retry" != "J" ]]; then
                print_info "Cloudflare-Konfiguration übersprungen."
                return
            fi
        fi
    done
    
    # Öffentliche IP-Adressen ermitteln
    local ip_addresses=($ip)
    local ipv4=""
    local ipv6=""
    
    if [ -z "$ip" ]; then
        ip_addresses=($(get_public_ips))
    fi
    
    ipv4=${ip_addresses[0]}
    ipv6=${ip_addresses[1]}
    
    print_info "Verwende IPv4-Adresse: $ipv4"
    if [ -n "$ipv6" ]; then
        print_info "Verwende IPv6-Adresse: $ipv6"
    fi
    
    # Subdomains erstellen
    local subdomains=("" "api" "mqtt" "www")
    local all_successful=true
    
    # IPv4-Einträge erstellen
    for subdomain in "${subdomains[@]}"; do
        local name=$subdomain
        if [ -z "$subdomain" ]; then
            name="@"
        fi
        
        print_info "Erstelle/Aktualisiere IPv4 DNS-Eintrag für $name.$domain..."
        
        # Überprüfen, ob der Eintrag bereits existiert
        local record_id=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$cf_zone_id/dns_records?type=A&name=$name.$domain" \
            -H "Authorization: Bearer $cf_token" \
            -H "Content-Type: application/json" | jq -r '.result[0].id')
        
        local update_response=""
        if [ "$record_id" != "null" ] && [ ! -z "$record_id" ]; then
            # Eintrag aktualisieren
            update_response=$(curl -s -X PUT "https://api.cloudflare.com/client/v4/zones/$cf_zone_id/dns_records/$record_id" \
                -H "Authorization: Bearer $cf_token" \
                -H "Content-Type: application/json" \
                --data "{\"type\":\"A\",\"name\":\"$name\",\"content\":\"$ipv4\",\"ttl\":1,\"proxied\":true}")
            
            local success=$(echo "$update_response" | jq -r '.success')
            if [[ "$success" == "true" ]]; then
                print_success "IPv4 DNS-Eintrag für $name.$domain aktualisiert."
            else
                print_error "Fehler beim Aktualisieren des IPv4 DNS-Eintrags für $name.$domain"
                local error_message=$(echo "$update_response" | jq -r '.errors[0].message')
                print_error "Fehlermeldung: $error_message"
                all_successful=false
            fi
        else
            # Neuen Eintrag erstellen
            update_response=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$cf_zone_id/dns_records" \
                -H "Authorization: Bearer $cf_token" \
                -H "Content-Type: application/json" \
                --data "{\"type\":\"A\",\"name\":\"$name\",\"content\":\"$ipv4\",\"ttl\":1,\"proxied\":true}")
            
            local success=$(echo "$update_response" | jq -r '.success')
            if [[ "$success" == "true" ]]; then
                print_success "IPv4 DNS-Eintrag für $name.$domain erstellt."
            else
                print_error "Fehler beim Erstellen des IPv4 DNS-Eintrags für $name.$domain"
                local error_message=$(echo "$update_response" | jq -r '.errors[0].message')
                print_error "Fehlermeldung: $error_message"
                all_successful=false
            fi
        fi
    done
    
    # IPv6-Einträge erstellen, wenn verfügbar
    if [ -n "$ipv6" ]; then
        for subdomain in "${subdomains[@]}"; do
            local name=$subdomain
            if [ -z "$subdomain" ]; then
                name="@"
            fi
            
            print_info "Erstelle/Aktualisiere IPv6 DNS-Eintrag für $name.$domain..."
            
            # Überprüfen, ob der Eintrag bereits existiert
            local record_id=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$cf_zone_id/dns_records?type=AAAA&name=$name.$domain" \
                -H "Authorization: Bearer $cf_token" \
                -H "Content-Type: application/json" | jq -r '.result[0].id')
            
            local update_response=""
            if [ "$record_id" != "null" ] && [ ! -z "$record_id" ]; then
                # Eintrag aktualisieren
                update_response=$(curl -s -X PUT "https://api.cloudflare.com/client/v4/zones/$cf_zone_id/dns_records/$record_id" \
                    -H "Authorization: Bearer $cf_token" \
                    -H "Content-Type: application/json" \
                    --data "{\"type\":\"AAAA\",\"name\":\"$name\",\"content\":\"$ipv6\",\"ttl\":1,\"proxied\":true}")
                
                local success=$(echo "$update_response" | jq -r '.success')
                if [[ "$success" == "true" ]]; then
                    print_success "IPv6 DNS-Eintrag für $name.$domain aktualisiert."
                else
                    print_error "Fehler beim Aktualisieren des IPv6 DNS-Eintrags für $name.$domain"
                    local error_message=$(echo "$update_response" | jq -r '.errors[0].message')
                    print_error "Fehlermeldung: $error_message"
                    # IPv6-Fehler sind nicht kritisch, daher all_successful nicht ändern
                fi
            else
                # Neuen Eintrag erstellen
                update_response=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$cf_zone_id/dns_records" \
                    -H "Authorization: Bearer $cf_token" \
                    -H "Content-Type: application/json" \
                    --data "{\"type\":\"AAAA\",\"name\":\"$name\",\"content\":\"$ipv6\",\"ttl\":1,\"proxied\":true}")
                
                local success=$(echo "$update_response" | jq -r '.success')
                if [[ "$success" == "true" ]]; then
                    print_success "IPv6 DNS-Eintrag für $name.$domain erstellt."
                else
                    print_error "Fehler beim Erstellen des IPv6 DNS-Eintrags für $name.$domain"
                    local error_message=$(echo "$update_response" | jq -r '.errors[0].message')
                    print_error "Fehlermeldung: $error_message"
                    # IPv6-Fehler sind nicht kritisch, daher all_successful nicht ändern
                fi
            fi
        done
    fi
    
    if [[ "$all_successful" == "true" ]]; then
        print_success "Cloudflare DNS-Einträge wurden erfolgreich konfiguriert."
        print_info "Es kann bis zu 5 Minuten dauern, bis die Änderungen wirksam werden."
    else
        print_warning "Einige DNS-Einträge konnten nicht konfiguriert werden. Bitte überprüfen Sie die Fehler und versuchen Sie es später manuell."
    fi
}

# Funktion zum Konfigurieren von Hetzner Cloud
configure_hetzner() {
    local server_id=""
    
    print_info "Konfiguriere Hetzner Cloud Firewall und Port-Freigaben..."
    
    # Fragen nach Hetzner API-Token
    print_info "Für die automatische Konfiguration von Hetzner Cloud wird ein API-Token benötigt."
    print_info "Sie können ein Token erstellen unter: https://console.hetzner.cloud/projects/YOUR_PROJECT/security/tokens"
    
    read -p "Möchten Sie Hetzner Cloud automatisch konfigurieren? (j/n): " use_hetzner
    
    if [[ "$use_hetzner" != "j" && "$use_hetzner" != "J" ]]; then
        print_info "Hetzner-Konfiguration übersprungen."
        return
    fi
    
    # Installiere jq, falls nicht vorhanden
    if ! command -v jq &>/dev/null; then
        print_info "Installiere jq für JSON-Verarbeitung..."
        apt-get update && apt-get install -y jq
    fi
    
    # Token validieren und Server auflisten
    local token_valid=false
    local hcloud_token=""
    
    while [ "$token_valid" = false ]; do
        read -sp "Bitte geben Sie Ihren Hetzner API-Token ein: " hcloud_token
        echo ""
        
        print_info "Teste Hetzner API-Token..."
        # Token-Test durch Abfrage der Server
        local test_response=$(curl -s -H "Authorization: Bearer $hcloud_token" "https://api.hetzner.cloud/v1/servers")
        
        # Prüfen, ob die Antwort valid ist
        if echo "$test_response" | jq -e '.servers != null' &>/dev/null; then
            local server_count=$(echo "$test_response" | jq '.servers | length')
            print_success "API-Token ist gültig. $server_count Server gefunden."
            token_valid=true
            
            # Server anzeigen
            print_info "Verfügbare Server:"
            echo "$test_response" | jq -r '.servers[] | "ID: \(.id), Name: \(.name), Status: \(.status), Typ: \(.server_type.name)"'
        else
            local error_message=$(echo "$test_response" | jq -r '.error.message')
            print_error "API-Token ungültig: $error_message"
            read -p "Möchten Sie es erneut versuchen? (j/n): " retry
            if [[ "$retry" != "j" && "$retry" != "J" ]]; then
                print_info "Hetzner-Konfiguration übersprungen."
                return
            fi
        fi
    done
    
    # Server ID erfragen und validieren
    local server_valid=false
    
    while [ "$server_valid" = false ]; do
        read -p "Bitte geben Sie die ID des zu konfigurierenden Servers ein: " server_id
        
        if [ -z "$server_id" ]; then
            print_error "Keine Server-ID angegeben. Bitte geben Sie eine gültige ID ein."
            continue
        fi
        
        # Prüfen, ob Server existiert
        local server_check=$(curl -s -H "Authorization: Bearer $hcloud_token" "https://api.hetzner.cloud/v1/servers/$server_id")
        
        if echo "$server_check" | jq -e '.server != null' &>/dev/null; then
            local server_name=$(echo "$server_check" | jq -r '.server.name')
            print_success "Server mit ID $server_id gefunden: $server_name"
            server_valid=true
        else
            local error_message=$(echo "$server_check" | jq -r '.error.message')
            print_error "Server-ID ungültig: $error_message"
            read -p "Möchten Sie es erneut versuchen? (j/n): " retry
            if [[ "$retry" != "j" && "$retry" != "J" ]]; then
                print_info "Hetzner-Konfiguration übersprungen."
                return
            fi
        fi
    done
    
    # Aktuelle Ports aus der Umgebung holen
    HTTP_PORT=${HTTP_PORT:-80}
    HTTPS_PORT=${HTTPS_PORT:-443}
    MQTT_PORT=${MQTT_PORT:-1883}
    MQTT_SSL_PORT=${MQTT_SSL_PORT:-8883}
    POSTGRES_PORT=${POSTGRES_PORT:-5432}
    NEXTCLOUD_PORT=${NEXTCLOUD_PORT:-8080}
    
    # Firewall erstellen oder aktualisieren
    print_info "Erstelle/Aktualisiere Firewall-Regeln..."
    
    # Überprüfen, ob bereits eine Firewall mit dem Namen "SwissAirDry" existiert
    local firewall_check=$(curl -s -H "Authorization: Bearer $hcloud_token" "https://api.hetzner.cloud/v1/firewalls")
    local firewall_id=$(echo "$firewall_check" | jq -r '.firewalls[] | select(.name=="SwissAirDry") | .id')
    
    # Dynamische Firewall-Regeln basierend auf konfigurierten Ports
    local rules='{
        "rules": [
            {
                "direction": "in",
                "protocol": "tcp",
                "port": "22",
                "source_ips": ["0.0.0.0/0", "::/0"]
            },
            {
                "direction": "in",
                "protocol": "tcp",
                "port": "'$HTTP_PORT'",
                "source_ips": ["0.0.0.0/0", "::/0"]
            },
            {
                "direction": "in",
                "protocol": "tcp",
                "port": "'$HTTPS_PORT'",
                "source_ips": ["0.0.0.0/0", "::/0"]
            },
            {
                "direction": "in",
                "protocol": "tcp",
                "port": "'$MQTT_PORT'",
                "source_ips": ["0.0.0.0/0", "::/0"]
            },
            {
                "direction": "in",
                "protocol": "tcp",
                "port": "'$MQTT_SSL_PORT'",
                "source_ips": ["0.0.0.0/0", "::/0"]
            },
            {
                "direction": "in",
                "protocol": "tcp",
                "port": "'$POSTGRES_PORT'",
                "source_ips": ["0.0.0.0/0", "::/0"]
            },
            {
                "direction": "in",
                "protocol": "tcp",
                "port": "'$NEXTCLOUD_PORT'",
                "source_ips": ["0.0.0.0/0", "::/0"]
            }
        ]
    }'
    
    local firewall_operation_success=false
    
    if [ -z "$firewall_id" ]; then
        # Firewall erstellen
        print_info "Erstelle neue Firewall 'SwissAirDry'..."
        local create_response=$(curl -s -X POST -H "Authorization: Bearer $hcloud_token" -H "Content-Type: application/json" -d "{
            \"name\": \"SwissAirDry\",
            \"apply_to\": {
                \"server\": {
                    \"id\": $server_id
                }
            },
            $rules
        }" "https://api.hetzner.cloud/v1/firewalls")
        
        if echo "$create_response" | jq -e '.firewall != null' &>/dev/null; then
            firewall_id=$(echo "$create_response" | jq -r '.firewall.id')
            print_success "Neue Firewall 'SwissAirDry' mit ID $firewall_id erstellt und auf Server angewendet."
            firewall_operation_success=true
        else
            local error_message=$(echo "$create_response" | jq -r '.error.message')
            print_error "Fehler beim Erstellen der Firewall: $error_message"
        fi
    else
        # Firewall aktualisieren
        print_info "Aktualisiere bestehende Firewall 'SwissAirDry' mit ID $firewall_id..."
        local update_response=$(curl -s -X PUT -H "Authorization: Bearer $hcloud_token" -H "Content-Type: application/json" -d "$rules" "https://api.hetzner.cloud/v1/firewalls/$firewall_id")
        
        if echo "$update_response" | jq -e '.firewall != null' &>/dev/null; then
            print_success "Firewall-Regeln aktualisiert."
            
            # Server der Firewall zuweisen, falls noch nicht geschehen
            local firewall_details=$(curl -s -H "Authorization: Bearer $hcloud_token" "https://api.hetzner.cloud/v1/firewalls/$firewall_id")
            local assigned=$(echo "$firewall_details" | jq -r ".firewall.applied_to[] | select(.server.id==$server_id) | .server.id")
            
            if [ -z "$assigned" ]; then
                print_info "Wende Firewall auf Server an..."
                local apply_response=$(curl -s -X POST -H "Authorization: Bearer $hcloud_token" -H "Content-Type: application/json" -d "{
                    \"apply_to\": [
                        {
                            \"type\": \"server\",
                            \"server\": {
                                \"id\": $server_id
                            }
                        }
                    ]
                }" "https://api.hetzner.cloud/v1/firewalls/$firewall_id/actions/apply_to_resources")
                
                if echo "$apply_response" | jq -e '.action != null' &>/dev/null; then
                    print_success "Firewall 'SwissAirDry' mit ID $firewall_id auf Server angewendet."
                    firewall_operation_success=true
                else
                    local error_message=$(echo "$apply_response" | jq -r '.error.message')
                    print_error "Fehler beim Anwenden der Firewall auf den Server: $error_message"
                fi
            else
                print_success "Firewall 'SwissAirDry' mit ID $firewall_id ist bereits auf Server angewendet."
                firewall_operation_success=true
            fi
        else
            local error_message=$(echo "$update_response" | jq -r '.error.message')
            print_error "Fehler beim Aktualisieren der Firewall: $error_message"
        fi
    fi
    
    if [[ "$firewall_operation_success" == "true" ]]; then
        print_success "Hetzner Cloud Firewall wurde erfolgreich konfiguriert."
        print_info "Die Firewall-Regeln wurden für folgende Ports eingerichtet:"
        print_info "SSH: 22"
        print_info "HTTP: $HTTP_PORT"
        print_info "HTTPS: $HTTPS_PORT"
        print_info "MQTT: $MQTT_PORT"
        print_info "MQTT (SSL): $MQTT_SSL_PORT"
        print_info "PostgreSQL: $POSTGRES_PORT"
        print_info "Nextcloud: $NEXTCLOUD_PORT"
    else
        print_warning "Die Hetzner Cloud Konfiguration konnte nicht vollständig abgeschlossen werden. Bitte prüfen Sie die Fehler und versuchen Sie es später manuell."
    fi
}

# Funktion zum Testen der API-Verbindung
test_api_connection() {
    local api_url=$1
    local method=${2:-GET}
    local auth_header=$3
    local payload=$4
    
    print_info "Teste Verbindung zu API: $api_url..."
    
    local response=""
    local status_code=""
    
    # Abhängig von den übergebenen Parametern die passende curl-Anfrage erstellen
    if [ -n "$auth_header" ] && [ -n "$payload" ]; then
        response=$(curl -s -w "%{http_code}" -X $method -H "$auth_header" -H "Content-Type: application/json" -d "$payload" "$api_url")
    elif [ -n "$auth_header" ]; then
        response=$(curl -s -w "%{http_code}" -X $method -H "$auth_header" "$api_url")
    else
        response=$(curl -s -w "%{http_code}" -X $method "$api_url")
    fi
    
    # Status-Code aus der Antwort extrahieren
    status_code="${response: -3}"
    # Eigentliche Antwort (ohne Status-Code)
    local body="${response:0:${#response}-3}"
    
    # HTTP-Status-Code überprüfen
    if [[ $status_code -ge 200 && $status_code -lt 300 ]]; then
        print_success "Verbindung zu API erfolgreich (HTTP $status_code)."
        return 0
    else
        print_error "Verbindung zu API fehlgeschlagen (HTTP $status_code)."
        if [ -n "$body" ]; then
            print_info "API-Antwort: $body"
        fi
        return 1
    fi
}

# Funktion zum Sammeln von Diagnose-Informationen
collect_diagnostics() {
    local output_file="$install_dir/diagnostics_$(date +%Y%m%d_%H%M%S).txt"
    
    print_info "Sammle Diagnose-Informationen in $output_file..."
    
    {
        echo "=== SwissAirDry Diagnose-Bericht ==="
        echo "Datum: $(date)"
        echo "Hostname: $(hostname)"
        echo "Kernel: $(uname -a)"
        echo ""
        
        echo "=== Disk Space ==="
        df -h
        echo ""
        
        echo "=== Memory Info ==="
        free -m
        echo ""
        
        echo "=== Network Interfaces ==="
        ip a
        echo ""
        
        echo "=== Open Ports ==="
        netstat -tuln
        echo ""
        
        echo "=== Docker Info ==="
        docker info 2>/dev/null || echo "Docker information nicht verfügbar"
        echo ""
        
        echo "=== Docker Containers ==="
        docker ps -a 2>/dev/null || echo "Docker container information nicht verfügbar"
        echo ""
        
        echo "=== Docker Networks ==="
        docker network ls 2>/dev/null || echo "Docker network information nicht verfügbar"
        echo ""
        
        echo "=== Installed Packages ==="
        if command -v dpkg &>/dev/null; then
            dpkg -l | grep -E 'docker|nginx|ssl|certbot'
        elif command -v rpm &>/dev/null; then
            rpm -qa | grep -E 'docker|nginx|ssl|certbot'
        else
            echo "Paketinformationen nicht verfügbar"
        fi
        echo ""
        
        echo "=== Environment Variables ==="
        if [ -f "$install_dir/.env" ]; then
            echo "Umgebungsvariablen existieren (Inhalte werden aus Sicherheitsgründen nicht angezeigt)"
        else
            echo "Keine .env-Datei gefunden"
        fi
        echo ""
        
        echo "=== Installation Directory ==="
        ls -la "$install_dir"
        echo ""
        
        echo "=== Service Status ==="
        systemctl status docker 2>/dev/null || echo "Docker service status nicht verfügbar"
        echo ""
        
        # Internet-Konnektivität testen
        echo "=== Internet-Konnektivität ==="
        ping -c 3 google.com 2>/dev/null || echo "Ping zu google.com fehlgeschlagen"
        ping -c 3 cloudflare.com 2>/dev/null || echo "Ping zu cloudflare.com fehlgeschlagen"
        echo ""
        
        # DNS-Auflösung testen
        echo "=== DNS-Auflösung ==="
        if command -v dig &>/dev/null; then
            dig +short google.com
        elif command -v nslookup &>/dev/null; then
            nslookup google.com | grep -A2 "Non-authoritative"
        else
            echo "Keine DNS-Tools verfügbar"
        fi
        echo ""
        
        # Externe IP-Adresse ermitteln
        echo "=== Externe IP-Adresse ==="
        curl -s https://api.ipify.org || echo "Externe IP konnte nicht ermittelt werden"
        echo ""
        
    } > "$output_file"
    
    print_success "Diagnose-Informationen wurden in $output_file gespeichert."
    print_info "Bitte teilen Sie diese Datei mit dem Support-Team, wenn Sie Hilfe benötigen."
}

# Debugging-Funktion
debug_installation() {
    print_info "Starte Diagnose-Modus..."
    
    print_info "1. Überprüfe Docker-Installation..."
    if command -v docker &>/dev/null; then
        docker --version
        print_success "Docker ist installiert."
        
        if systemctl is-active --quiet docker; then
            print_success "Docker-Dienst läuft."
        else
            print_error "Docker-Dienst läuft nicht."
            print_info "Versuche, Docker-Dienst zu starten..."
            systemctl start docker
        fi
    else
        print_error "Docker ist nicht installiert."
    fi
    
    print_info "2. Überprüfe Docker Compose Installation..."
    if command -v docker-compose &>/dev/null; then
        docker-compose --version
        print_success "Docker Compose ist installiert."
    else
        print_error "Docker Compose ist nicht installiert."
    fi
    
    print_info "3. Überprüfe Netzwerk-Ports..."
    for port in 80 443 1883 8883 5432 8080; do
        if check_port_usage $port; then
            print_warning "Port $port wird bereits verwendet."
            lsof -i :$port 2>/dev/null || print_info "Verwenden Sie 'sudo lsof -i :$port' um zu sehen, welcher Prozess diesen Port belegt."
        else
            print_success "Port $port ist frei."
        fi
    done
    
    print_info "4. Überprüfe Docker-Netzwerke..."
    docker network ls
    
    print_info "5. Überprüfe Installation Directory..."
    if [ -d "$install_dir" ]; then
        print_success "Installationsverzeichnis $install_dir existiert."
        
        if [ -f "$install_dir/docker-compose.yml" ]; then
            print_success "docker-compose.yml ist vorhanden."
        else
            print_error "docker-compose.yml fehlt."
        fi
        
        if [ -f "$install_dir/.env" ]; then
            print_success ".env-Datei ist vorhanden."
        else
            print_error ".env-Datei fehlt."
        fi
    else
        print_error "Installationsverzeichnis $install_dir existiert nicht."
    fi
    
    print_info "6. Sammle vollständige Diagnose-Informationen..."
    collect_diagnostics
    
    print_info "Diagnose abgeschlossen. Bitte überprüfen Sie die oben genannten Probleme."
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
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p\${MYSQL_ROOT_PASSWORD}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:alpine
    container_name: nextcloud_redis
    restart: always
    volumes:
      - ${redis_volume}:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

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
      - "\${NEXTCLOUD_PORT}:80"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/status.php"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s

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
    
    # Mosquitto Konfiguration direkt erstellen
    cat > "${install_dir}/mqtt/config/mosquitto.conf" << EOF
# Mosquitto Konfiguration für SwissAirDry
# Diese Datei wird automatisch erstellt - manuelle Änderungen werden überschrieben

# Netzwerk-Einstellungen
listener 1883
allow_anonymous true

# WebSockets für Web-Clients
listener 9001
protocol websockets

# Persistenz und Logging
persistence true
persistence_location /mosquitto/data
log_dest file /mosquitto/log/mosquitto.log
log_dest stdout
log_type all

# Erweiterte Einstellungen
max_connections -1
max_packet_size 16384
max_inflight_messages 40
max_queued_messages 1000
queue_qos0_messages false
EOF

    # Erstelle Update-Skript für MQTT-Konfiguration
    cat > "${install_dir}/update_mqtt_config.sh" << 'EOF'
#!/bin/bash

# Farben für Ausgaben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funktionen
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[ERFOLG]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNUNG]${NC} $1"; }
print_error() { echo -e "${RED}[FEHLER]${NC} $1"; }

# Pfade
MQTT_CONFIG_DIR="./mqtt/config"
MQTT_CONFIG="${MQTT_CONFIG_DIR}/mosquitto.conf"
ENV_FILE="./.env"

# Prüfen, ob die .env-Datei existiert
if [ ! -f "$ENV_FILE" ]; then
    print_error "Umgebungsvariablen-Datei nicht gefunden: $ENV_FILE"
    exit 1
fi

# Lade Umgebungsvariablen
source "$ENV_FILE"

print_info "Aktualisiere MQTT-Konfiguration..."

# SSL-Konfiguration basierend auf Umgebungsvariablen
SSL_CONFIG=""
if [ "${MQTT_SSL_ENABLED:-false}" = "true" ]; then
    SSL_CONFIG="# SSL/TLS Konfiguration\nlistener ${MQTT_SSL_PORT:-8883}\ncertfile /mosquitto/certs/fullchain.pem\nkeyfile /mosquitto/certs/privkey.pem\nrequire_certificate false"
else
    SSL_CONFIG="# SSL/TLS Konfiguration (deaktiviert)\n# listener ${MQTT_SSL_PORT:-8883}\n# certfile /mosquitto/certs/fullchain.pem\n# keyfile /mosquitto/certs/privkey.pem\n# require_certificate false"
fi

# Auth-Konfiguration basierend auf Umgebungsvariablen
AUTH_CONFIG=""
if [ "${MQTT_AUTH_ENABLED:-false}" = "true" ]; then
    AUTH_CONFIG="# Authentifizierung\nallow_anonymous false\npassword_file /mosquitto/config/mosquitto.passwd"
else
    AUTH_CONFIG="# Authentifizierung (deaktiviert)\nallow_anonymous true\n# password_file /mosquitto/config/mosquitto.passwd"
fi

# Neue Konfiguration erstellen
cat > "$MQTT_CONFIG" << EOL
# Mosquitto Konfiguration für SwissAirDry
# Diese Datei wird automatisch erstellt - manuelle Änderungen werden überschrieben

# Netzwerk-Einstellungen
listener ${MQTT_PORT:-1883}

# WebSockets für Web-Clients
listener ${MQTT_WS_PORT:-9001}
protocol websockets

# Persistenz und Logging
persistence true
persistence_location /mosquitto/data
log_dest file /mosquitto/log/mosquitto.log
log_dest stdout
log_type all

# Erweiterte Einstellungen
max_connections -1
max_packet_size 16384
max_inflight_messages 40
max_queued_messages 1000
queue_qos0_messages false

$(echo -e "$SSL_CONFIG")

$(echo -e "$AUTH_CONFIG")
EOL

print_success "MQTT-Konfiguration aktualisiert!"
print_info "Um Änderungen anzuwenden, führen Sie aus: docker-compose restart mqtt"
EOF

    chmod +x "${install_dir}/update_mqtt_config.sh"
    print_success "MQTT-Konfigurationsskript erstellt: ${install_dir}/update_mqtt_config.sh"
    
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

    # Erhöhte Timeouts für Nextcloud
    proxy_connect_timeout 600;
    proxy_send_timeout 600;
    proxy_read_timeout 600;
    send_timeout 600;
    
    client_max_body_size 512M; # Erhöht von Standard 1M für große Uploads

    location / {
        proxy_pass http://nextcloud_app:80;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Spezifische Headers für Nextcloud
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Server \$host;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
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
      - "\${MQTT_PORT}:1883"
      - "\${MQTT_SSL_PORT}:8883"
    user: "1883"
    volumes:
      - ${install_dir}/mqtt/config:/mosquitto/config
      - ${install_dir}/mqtt/data:/mosquitto/data
      - ${install_dir}/mqtt/log:/mosquitto/log
      - ${install_dir}/nginx/ssl:/mosquitto/certs
    healthcheck:
      test: ["CMD", "mosquitto_sub", "-t", "$$" , "-C", "1", "-i", "healthcheck"]
      interval: 30s
      timeout: 10s
      retries: 3
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
      - "\${POSTGRES_PORT}:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U \${POSTGRES_USER} -d \${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
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
      postgres:
        condition: service_healthy
      mqtt:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    networks:
      - swissairdry_network

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: swissairdry_nginx
    restart: always
    ports:
      - "\${HTTP_PORT}:80"
      - "\${HTTPS_PORT}:443"
    volumes:
      - ${install_dir}/nginx/conf.d:/etc/nginx/conf.d
      - ${install_dir}/nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      api:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost"]
      interval: 30s
      timeout: 10s
      retries: 3
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

# Installiere curl für Health-Checks
RUN apt-get update && apt-get install -y curl && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Erstelle einfachen API Endpunkt für Gesundheitsprüfung
RUN mkdir -p /app && echo 'from fastapi import FastAPI\nimport uvicorn\n\napp = FastAPI()\n\n@app.get("/health")\nasync def health_check():\n    return {"status": "ok"}\n\nif __name__ == "__main__":\n    uvicorn.run(app, host="0.0.0.0", port=5000)' > /app/run.py

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
paho-mqtt==1.6.1  # Ältere, stabilere Version für bessere Kompatibilität
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

# Umgebungsvariablen-Datei erstellen mit automatischer Port-Erkennung
create_env_file() {
    local install_dir=$1
    local domain=$2
    
    print_info "Erstelle Umgebungsvariablen-Datei mit automatischer Port-Erkennung..."
    
    # Passwörter generieren
    MYSQL_ROOT_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)
    MYSQL_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)
    POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)
    NEXTCLOUD_ADMIN_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)
    
    # Finde freie Ports für alle Dienste
    print_info "Prüfe auf verfügbare Ports..."
    
    HTTP_PORT=$(find_next_free_port 80)
    HTTPS_PORT=$(find_next_free_port 443)
    NEXTCLOUD_PORT=$(find_next_free_port 8080)
    POSTGRES_PORT=$(find_next_free_port 5432)
    MQTT_PORT=$(find_next_free_port 1883)
    MQTT_SSL_PORT=$(find_next_free_port 8883)
    
    if [ "$HTTP_PORT" != "80" ]; then
        print_warning "Standard HTTP-Port 80 ist nicht verfügbar, verwende Port $HTTP_PORT"
    fi
    
    if [ "$HTTPS_PORT" != "443" ]; then
        print_warning "Standard HTTPS-Port 443 ist nicht verfügbar, verwende Port $HTTPS_PORT"
    fi
    
    # .env-Datei erstellen
    cat > "${install_dir}/.env" << EOF
# Allgemeine Konfiguration
DOMAIN=${domain}

# Ports (automatisch erkannt)
HTTP_PORT=${HTTP_PORT}
HTTPS_PORT=${HTTPS_PORT}
NEXTCLOUD_PORT=${NEXTCLOUD_PORT}
POSTGRES_PORT=${POSTGRES_PORT}
MQTT_PORT=${MQTT_PORT}
MQTT_SSL_PORT=${MQTT_SSL_PORT}
MQTT_WS_PORT=9001

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
MQTT_PORT=${MQTT_PORT}
MQTT_SSL_ENABLED=false
MQTT_AUTH_ENABLED=false
MQTT_ALLOW_ANONYMOUS=true
EOF
    
    print_success "Umgebungsvariablen-Datei erstellt in ${install_dir}/.env"
    print_info "Die folgenden Ports werden verwendet:"
    print_info "HTTP: ${HTTP_PORT}"
    print_info "HTTPS: ${HTTPS_PORT}"
    print_info "Nextcloud: ${NEXTCLOUD_PORT}"
    print_info "PostgreSQL: ${POSTGRES_PORT}"
    print_info "MQTT: ${MQTT_PORT}"
    print_info "MQTT (SSL): ${MQTT_SSL_PORT}"
    
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

# Berechtigungen für MQTT anpassen
print_info "Setze Berechtigungen für SSL-Verzeichnis..."
mkdir -p "${install_dir}/nginx/ssl"
# Erstelle einen MQTT-Benutzer im Container falls er nicht existiert
if ! id -u 1883 &>/dev/null; then
    print_info "Erstelle MQTT-Benutzer (ID: 1883)..."
    groupadd -g 1883 mosquitto || true
    useradd -u 1883 -g 1883 -M -s /usr/sbin/nologin mosquitto || true
fi

# SSL-Zertifikate einrichten
setup_ssl "$domain_name" "${install_dir}/nginx/ssl"

# Berechtigungen für SSL-Verzeichnis setzen
print_info "Setze Berechtigungen für SSL-Verzeichnis..."
chmod -R 755 "${install_dir}/nginx/ssl"
chown -R 1883:1883 "${install_dir}/nginx/ssl" || true
chmod 600 "${install_dir}/nginx/ssl/privkey.pem" || true

# SSL-Verzeichnis für MQTT konfigurieren
print_info "Konfiguriere SSL-Verzeichnis für MQTT..."
mkdir -p "${install_dir}/mqtt/certs"
if [ -f "${install_dir}/nginx/ssl/privkey.pem" ] && [ -f "${install_dir}/nginx/ssl/fullchain.pem" ]; then
    cp "${install_dir}/nginx/ssl/fullchain.pem" "${install_dir}/mqtt/certs/fullchain.pem"
    cp "${install_dir}/nginx/ssl/privkey.pem" "${install_dir}/mqtt/certs/privkey.pem"
    chmod -R 755 "${install_dir}/mqtt/certs"
    chown -R 1883:1883 "${install_dir}/mqtt/certs" || true
    chmod 600 "${install_dir}/mqtt/certs/privkey.pem" || true
    print_success "SSL-Zertifikate für MQTT konfiguriert"
else
    print_warning "SSL-Zertifikate nicht gefunden, MQTT wird ohne SSL konfiguriert"
fi

# IP-Adressen ermitteln und anzeigen
print_info "Ermittle Ihre öffentlichen IP-Adressen..."
ip_addresses=($(get_public_ips))
ipv4=${ip_addresses[0]}
ipv6=${ip_addresses[1]}

print_info "-------------------------------------------------"
print_info "WICHTIG: Die folgenden IP-Adressen werden für DNS verwendet:"
print_info "IPv4: $ipv4"
if [ -n "$ipv6" ]; then
    print_info "IPv6: $ipv6"
fi
print_info "-------------------------------------------------"
print_info "Stellen Sie sicher, dass diese IP-Adressen in Ihrer Cloudflare/DNS-Konfiguration erlaubt sind."
print_info "Wenn Sie einen Cloudflare API-Token verwenden, muss dieser Zugriff auf diese IPs haben."
print_info "-------------------------------------------------"

# Subdomains erklären
print_info "\nFolgende Subdomains werden für SwissAirDry benötigt:"
print_info "1. ${domain_name} - Hauptdomain für Nextcloud und Web-Interface"
print_info "2. api.${domain_name} - API-Server für Geräte und API-Clients"
print_info "3. exapp.${domain_name} - Nextcloud ExApp Integration (Dashboard)"
print_info "4. mqtt.${domain_name} - MQTT-Broker (optional für WebSocket-Clients)"
print_info "-------------------------------------------------"

# Fragen, ob Cloudflare konfiguriert werden soll
read -p "Möchten Sie Cloudflare DNS für Ihre Domain konfigurieren? (j/n): " configure_cf
if [[ "$configure_cf" == "j" || "$configure_cf" == "J" ]]; then
    # Modifizierter Aufruf für alle Subdomains
    configure_cloudflare "$domain_name" "$ipv4 $ipv6" "api exapp mqtt"
fi

# Fragen, ob Hetzner Cloud konfiguriert werden soll
read -p "Möchten Sie eine Hetzner Cloud Server-Konfiguration durchführen? (j/n): " configure_hetzner_cloud
if [[ "$configure_hetzner_cloud" == "j" || "$configure_hetzner_cloud" == "J" ]]; then
    configure_hetzner
fi

# Nextcloud Docker Compose erstellen
create_nextcloud_docker_compose "${install_dir}/nextcloud"

# SwissAirDry Docker Compose erstellen
create_swissairdry_docker_compose "$install_dir"

# Umgebungsvariablen-Datei erstellen
create_env_file "$install_dir" "$domain_name"

# Fragen, ob der Debugging-Modus ausgeführt werden soll
print_info "Möchten Sie vor dem Start einen Diagnose-Modus ausführen, um mögliche Probleme zu erkennen? (j/n): "
read run_diagnostics

if [[ "$run_diagnostics" == "j" || "$run_diagnostics" == "J" ]]; then
    debug_installation
fi

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
    
    # Warten und prüfen, ob die Services gestartet sind
    print_info "Warte auf den Start der SwissAirDry-Dienste..."
    sleep 10
    
    # Überprüfen des Status der Container
    if docker-compose ps | grep -q "Up"; then
        print_success "SwissAirDry-Dienste erfolgreich gestartet."
    else
        print_warning "Einige SwissAirDry-Dienste konnten nicht gestartet werden. Führen Sie 'cd $install_dir && docker-compose logs' aus, um Details zu sehen."
    fi
    
    # Starten der Nextcloud
    cd "${install_dir}/nextcloud"
    docker-compose up -d
    
    # Warten und prüfen, ob die Nextcloud gestartet ist
    print_info "Warte auf den Start von Nextcloud..."
    sleep 10
    
    # Überprüfen des Status der Container
    if docker-compose ps | grep -q "Up"; then
        print_success "Nextcloud erfolgreich gestartet."
    else
        print_warning "Nextcloud konnte nicht gestartet werden. Führen Sie 'cd ${install_dir}/nextcloud && docker-compose logs' aus, um Details zu sehen."
    fi
    
    # Warten auf den Start aller Dienste
    print_info "Warte auf den vollständigen Start aller Dienste (60 Sekunden)..."
    sleep 60
    
    # Verbindungstests durchführen
    print_info "Führe Verbindungstests durch..."
    
    # Container-Status prüfen
    print_info "Prüfe Container-Status..."
    container_status=$(docker ps --format "{{.Names}}: {{.Status}}")
    echo "$container_status"
    
    # HTTP/HTTPS-Verbindung testen
    print_info "Teste HTTP/HTTPS Verbindung..."
    if test_connection "localhost" "$HTTP_PORT" "HTTP Server"; then
        print_success "HTTP-Server ist erreichbar."
    else
        print_warning "HTTP-Server ist nicht erreichbar. Prüfe Status mit: docker-compose logs nginx"
        print_info "Versuche alternativen Test..."
        if command -v curl &> /dev/null; then
            curl -s -o /dev/null -w "%{http_code}" http://localhost:$HTTP_PORT || print_warning "curl fehlgeschlagen mit Code: $?"
        fi
    fi
    
    if test_connection "localhost" "$HTTPS_PORT" "HTTPS Server"; then
        print_success "HTTPS-Server ist erreichbar."
    else
        print_warning "HTTPS-Server ist nicht erreichbar. Prüfe Status mit: docker-compose logs nginx"
        print_info "Versuche alternativen Test..."
        if command -v curl &> /dev/null; then
            curl -s -k -o /dev/null -w "%{http_code}" https://localhost:$HTTPS_PORT || print_warning "curl fehlgeschlagen mit Code: $?"
        fi
    fi
    
    # MQTT-Verbindung testen
    print_info "Teste MQTT Verbindung..."
    if test_connection "localhost" "$MQTT_PORT" "MQTT Broker"; then
        print_success "MQTT-Broker ist erreichbar."
    else
        print_warning "MQTT-Broker ist nicht erreichbar. Prüfe Status mit: docker-compose logs mqtt"
        print_info "Wenn Sie mosquitto-clients installiert haben, können Sie mit folgendem Befehl testen:"
        print_info "mosquitto_sub -h localhost -p $MQTT_PORT -t test -C 1"
    fi
    
    # PostgreSQL-Verbindung testen
    print_info "Teste PostgreSQL Verbindung..."
    if test_connection "localhost" "$POSTGRES_PORT" "PostgreSQL"; then
        print_success "PostgreSQL-Datenbank ist erreichbar."
    else
        print_warning "PostgreSQL-Datenbank ist nicht erreichbar. Prüfe Status mit: docker-compose logs postgres"
        if command -v pg_isready &> /dev/null; then
            print_info "Testergebnis pg_isready:"
            pg_isready -h localhost -p $POSTGRES_PORT || print_warning "pg_isready fehlgeschlagen mit Code: $?"
        fi
    fi
    
    # Prüfen auf mögliche Firewall-Blockierungen
    print_info "Prüfe auf mögliche Firewall-Blockierungen..."
    if command -v ufw &> /dev/null; then
        ufw_status=$(sudo ufw status)
        if echo "$ufw_status" | grep -q "Status: active"; then
            print_warning "Firewall ist aktiv. Bitte stellen Sie sicher, dass die Ports freigegeben sind:"
            print_info "sudo ufw allow $HTTP_PORT/tcp"
            print_info "sudo ufw allow $HTTPS_PORT/tcp"
            print_info "sudo ufw allow $MQTT_PORT/tcp"
            print_info "sudo ufw allow $POSTGRES_PORT/tcp"
            print_info "sudo ufw allow $NEXTCLOUD_PORT/tcp"
        else
            print_success "Keine aktive UFW-Firewall erkannt."
        fi
    elif command -v firewall-cmd &> /dev/null; then
        print_warning "FirewallD erkannt. Bitte stellen Sie sicher, dass die Ports freigegeben sind:"
        print_info "sudo firewall-cmd --permanent --add-port=$HTTP_PORT/tcp"
        print_info "sudo firewall-cmd --permanent --add-port=$HTTPS_PORT/tcp"
        print_info "sudo firewall-cmd --permanent --add-port=$MQTT_PORT/tcp"
        print_info "sudo firewall-cmd --permanent --add-port=$POSTGRES_PORT/tcp"
        print_info "sudo firewall-cmd --permanent --add-port=$NEXTCLOUD_PORT/tcp"
        print_info "sudo firewall-cmd --reload"
    fi
    
    print_success "Alle Dienste wurden gestartet!"
    print_info "SwissAirDry ist verfügbar unter: https://$domain_name"
    print_info "Bei Verwendung angepasster Ports: https://$domain_name:$HTTPS_PORT"
    print_info "SwissAirDry API ist verfügbar unter: https://api.$domain_name"
    print_info "Nextcloud ist verfügbar unter: https://$domain_name"
else
    print_info "Sie können die Dienste später mit folgenden Befehlen starten:"
    print_info "cd $install_dir && docker-compose up -d"
    print_info "cd ${install_dir}/nextcloud && docker-compose up -d"
fi

print_success "Installation abgeschlossen!"
print_info "Bitte sehen Sie in die Datei $install_dir/.env für die generierten Passwörter."

# Informationen zur Fehlerbehebung anzeigen
print_info "Falls Probleme auftreten:"
print_info "1. Überprüfen Sie die Logs mit 'docker-compose logs' im jeweiligen Verzeichnis"
print_info "2. Führen Sie das Diagnose-Tool mit dem Befehl aus: $install_dir/diagnose.sh"
print_info "3. Prüfen Sie, ob alle Ports korrekt konfiguriert sind in der Datei $install_dir/.env"
print_info "4. Für detaillierte Fehlerbehebung konsultieren Sie die FEHLERBEHEBUNG.md"

# Diagnose-Skript erstellen
cat > "${install_dir}/diagnose.sh" << 'EOF'
#!/bin/bash

# Farben für Ausgaben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funktionen für Ausgaben
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[ERFOLG]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNUNG]${NC} $1"; }
print_error() { echo -e "${RED}[FEHLER]${NC} $1"; }

# Installationsverzeichnis ermitteln
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

print_info "SwissAirDry Diagnose-Tool"
print_info "=========================="
print_info "Installationsverzeichnis: $SCRIPT_DIR"

# System-Informationen
print_info "\nSystem-Informationen:"
echo "Hostname: $(hostname)"
echo "Kernel: $(uname -a)"
echo "Freier Speicherplatz: $(df -h / | awk 'NR==2 {print $4}')"
echo "RAM: $(free -h | awk '/^Mem:/ {print $4}') frei von $(free -h | awk '/^Mem:/ {print $2}')"

# Docker-Status
print_info "\nDocker-Status:"
if command -v docker &> /dev/null; then
    docker --version
    echo "Docker-Daemon: $(systemctl is-active docker)"
    echo "Anzahl Container: $(docker ps -q | wc -l)"
    echo "Laufende SwissAirDry Container:"
    docker ps --filter "name=swissairdry" --format "{{.Names}}: {{.Status}}"
    echo "Laufende Nextcloud Container:"
    docker ps --filter "name=nextcloud" --format "{{.Names}}: {{.Status}}"
else
    print_error "Docker ist nicht installiert!"
fi

# Port-Belegung
print_info "\nPort-Belegung:"
echo "Offene Ports:"
netstat -tuln | grep -E ':(80|443|1883|8883|5432|8080)' || echo "Keine der Standard-Ports sind geöffnet"

# Umgebungsvariablen überprüfen
print_info "\nUmgebungsvariablen:"
if [ -f "$SCRIPT_DIR/.env" ]; then
    echo "Umgebungsvariablen-Datei existiert"
    # Zeige nur die Port-Konfigurationen ohne sensible Daten
    grep -E "PORT=" "$SCRIPT_DIR/.env" || echo "Keine Port-Konfigurationen gefunden"
else
    print_error ".env Datei fehlt!"
fi

# Verbindungstests
print_info "\nVerbindungstests:"

# Funktion zum Testen von TCP-Verbindungen
test_connection() {
    local host=$1
    local port=$2
    local service=$3
    
    if timeout 2 bash -c "echo > /dev/tcp/$host/$port" &>/dev/null; then
        print_success "$service auf $host:$port ist erreichbar"
        return 0
    else
        print_error "$service auf $host:$port ist NICHT erreichbar"
        return 1
    fi
}

# Ports aus .env-Datei auslesen, falls vorhanden
if [ -f "$SCRIPT_DIR/.env" ]; then
    source "$SCRIPT_DIR/.env" &>/dev/null || true
fi

# HTTP-Port testen (Default: 80)
HTTP_PORT=${HTTP_PORT:-80}
test_connection localhost $HTTP_PORT "HTTP Server"

# HTTPS-Port testen (Default: 443)
HTTPS_PORT=${HTTPS_PORT:-443}
test_connection localhost $HTTPS_PORT "HTTPS Server"

# MQTT-Port testen (Default: 1883)
MQTT_PORT=${MQTT_PORT:-1883}
test_connection localhost $MQTT_PORT "MQTT Broker"

# PostgreSQL-Port testen (Default: 5432)
POSTGRES_PORT=${POSTGRES_PORT:-5432}
test_connection localhost $POSTGRES_PORT "PostgreSQL"

# Nextcloud-Port testen (Default: 8080)
NEXTCLOUD_PORT=${NEXTCLOUD_PORT:-8080}
test_connection localhost $NEXTCLOUD_PORT "Nextcloud"

# Container-Logs überprüfen
print_info "\nContainer-Logs (letzte 10 Zeilen):"

# Funktion zum Anzeigen der letzten Zeilen von Container-Logs
show_container_logs() {
    local container=$1
    local lines=${2:-10}
    
    if docker ps -q --filter "name=$container" &>/dev/null; then
        echo "=== $container Logs ==="
        docker logs --tail $lines $container
        echo ""
    else
        echo "Container $container ist nicht aktiv"
    fi
}

show_container_logs "swissairdry_nginx"
show_container_logs "swissairdry_api"
show_container_logs "swissairdry_mqtt"
show_container_logs "swissairdry_postgres"
show_container_logs "nextcloud_app"
show_container_logs "nextcloud_db"

print_info "\nDiagnose abgeschlossen."
print_info "Falls Probleme auftreten, überprüfen Sie die FEHLERBEHEBUNG.md oder kontaktieren Sie den Support."
EOF

# Diagnose-Skript ausführbar machen
chmod +x "${install_dir}/diagnose.sh"

print_info "Für weitere Informationen und Fehlerbehebung besuchen Sie: https://github.com/swissairdry/docs"