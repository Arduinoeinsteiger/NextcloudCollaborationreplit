#!/bin/bash

# SwissAirDry Docker Reset Script
# Dieses Skript stoppt alle Docker-Container für SwissAirDry und entfernt alle Volumes

# Zum aktuellen Verzeichnis wechseln
cd "$(dirname "$0")"

# Farbdefinitionen
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}SwissAirDry Docker Reset-Skript${NC}"
echo "==================================="

# Überprüfen, ob Docker läuft
echo -e "${YELLOW}Überprüfe Docker-Status...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Docker ist nicht gestartet.${NC}"
    exit 1
fi
echo -e "${GREEN}Docker läuft!${NC}"

# Warnung anzeigen
echo -e "${RED}ACHTUNG: Dieses Skript stoppt alle SwissAirDry-Container und löscht ALLE Daten!${NC}"
echo -e "${RED}         Alle Datenbanken, Dateien und Konfigurationen gehen verloren!${NC}"
echo

# Bestätigung anfordern
read -p "Bist du sicher, dass du fortfahren möchtest? (j/N) " confirmation
if [ "$confirmation" != "j" ]; then
    echo -e "${YELLOW}Reset abgebrochen.${NC}"
    exit 0
fi

# Container und Volumes entfernen
echo -e "${YELLOW}Stoppe und entferne SwissAirDry-Container und Volumes...${NC}"
docker-compose down -v

echo -e "\n${GREEN}SwissAirDry wurde zurückgesetzt!${NC}"
echo -e "${YELLOW}Um SwissAirDry neu zu starten, führe ./start.sh aus.${NC}"