#!/bin/bash

# SwissAirDry Docker Stop Script
# Dieses Skript stoppt alle Docker-Container für SwissAirDry

# Zum aktuellen Verzeichnis wechseln
cd "$(dirname "$0")"

# Farbdefinitionen
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}SwissAirDry Docker Stop-Skript${NC}"
echo "==================================="

# Überprüfen, ob Docker läuft
echo -e "${YELLOW}Überprüfe Docker-Status...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Docker ist nicht gestartet.${NC}"
    exit 1
fi
echo -e "${GREEN}Docker läuft!${NC}"

# Container beenden
echo -e "${YELLOW}Stoppe SwissAirDry-Container...${NC}"
docker-compose down

echo -e "\n${GREEN}SwissAirDry wurde gestoppt!${NC}"