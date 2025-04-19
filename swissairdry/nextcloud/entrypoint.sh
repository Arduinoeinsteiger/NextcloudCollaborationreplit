#!/bin/bash
set -e

# Umgebungsvariablen holen
API_SERVER=${API_SERVER:-http://api:5000}
NEXTCLOUD_DOMAIN=${NEXTCLOUD_DOMAIN:-localhost}

# Warten auf API-Server-Verfügbarkeit
echo "Warte auf API-Server..."
until curl -s "$API_SERVER/health" | grep -q "ok"; do
  echo "API-Server ist noch nicht verfügbar - warte..."
  sleep 2
done
echo "API-Server ist verfügbar!"

# Konfiguration der External App anpassen
CONFIG_FILE="/var/www/html/custom_apps/swissairdry/appinfo/info.xml"
if [ -f "$CONFIG_FILE" ]; then
    # Ersetze die API-Server-URL in der iframe-Konfiguration
    sed -i "s|https://api.swissairdry.com|$API_SERVER|g" "$CONFIG_FILE"
    echo "External App-Konfiguration aktualisiert: API-Server = $API_SERVER"
fi

# AppAPI Konfiguration
cat > /var/www/html/custom_apps/swissairdry/.nextcloud/appapi.json <<EOL
{
  "external-app": {
    "enabled": true,
    "hosts": ["$NEXTCLOUD_DOMAIN", "localhost", "api", "$API_SERVER"]
  }
}
EOL
echo "AppAPI-Konfiguration erstellt/aktualisiert."

# Berechtigungen setzen
chown -R www-data:www-data /var/www/html
chmod -R 755 /var/www/html/custom_apps

# Starte Apache-Server
echo "Starte Apache..."
exec "$@"