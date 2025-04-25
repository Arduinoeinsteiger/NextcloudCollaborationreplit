#!/bin/bash

# SwissAirDry Docker Startup Script
# Dieses Skript startet alle Docker-Container für SwissAirDry

# Zum aktuellen Verzeichnis wechseln
cd "$(dirname "$0")"

# Farbdefinitionen
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}SwissAirDry Docker Start-Skript${NC}"
echo "===================================="

# Überprüfen, ob Docker läuft
echo -e "${YELLOW}Überprüfe Docker-Status...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Docker ist nicht gestartet. Bitte starte Docker Desktop und versuche es erneut.${NC}"
    exit 1
fi
echo -e "${GREEN}Docker läuft!${NC}"

# Überprüfen, ob die .env-Datei existiert
if [ ! -f .env ]; then
    echo -e "${YELLOW}Keine .env-Datei gefunden. Erstelle eine aus .env.example...${NC}"
    cp .env.example .env 2>/dev/null || cp .env .env.example
    echo -e "${GREEN}.env-Datei bereit.${NC}"
fi

# Container starten
echo -e "${YELLOW}Starte SwissAirDry-Container...${NC}"
docker-compose up -d

# Status überprüfen
echo -e "${YELLOW}Container-Status:${NC}"
docker-compose ps

echo -e "\n${GREEN}SwissAirDry wurde gestartet!${NC}"
echo -e "${BLUE}Zugriff auf SwissAirDry:${NC}"
echo -e "- Nextcloud: ${GREEN}http://localhost:8080${NC}"
echo -e "- SwissAirDry API: ${GREEN}http://localhost:5000${NC}"
echo -e "- SwissAirDry Simple API: ${GREEN}http://localhost:5001${NC}"
echo -e "- MQTT Broker: ${GREEN}localhost:1883${NC} (MQTT) und ${GREEN}localhost:9001${NC} (WebSocket)"
echo
echo -e "${YELLOW}Hinweis: Die erste Initialisierung kann einige Minuten dauern.${NC}"