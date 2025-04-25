#!/bin/bash

# Diese Skript erstellt ein Docker-Netzwerk für SwissAirDry
# Dies ist nützlich, wenn Teile des Systems unabhängig voneinander gestartet werden

# Farbdefinitionen
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}SwissAirDry Docker Netzwerk-Setup${NC}"
echo "===================================="

# Überprüfen, ob Docker läuft
echo -e "${YELLOW}Überprüfe Docker-Status...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Docker ist nicht gestartet. Bitte starte Docker Desktop und versuche es erneut.${NC}"
    exit 1
fi
echo -e "${GREEN}Docker läuft!${NC}"

# Netzwerke erstellen
echo -e "${YELLOW}Erstelle SwissAirDry Netzwerke...${NC}"

# Frontend-Netzwerk
if ! docker network inspect frontend > /dev/null 2>&1; then
    echo -e "Erstelle ${BLUE}frontend${NC} Netzwerk..."
    docker network create frontend
    echo -e "${GREEN}frontend${NC} Netzwerk erstellt!"
else
    echo -e "${BLUE}frontend${NC} Netzwerk existiert bereits."
fi

# Backend-Netzwerk
if ! docker network inspect backend > /dev/null 2>&1; then
    echo -e "Erstelle ${BLUE}backend${NC} Netzwerk..."
    docker network create backend
    echo -e "${GREEN}backend${NC} Netzwerk erstellt!"
else
    echo -e "${BLUE}backend${NC} Netzwerk existiert bereits."
fi

# MQTT-Netzwerk
if ! docker network inspect mqtt-net > /dev/null 2>&1; then
    echo -e "Erstelle ${BLUE}mqtt-net${NC} Netzwerk..."
    docker network create mqtt-net
    echo -e "${GREEN}mqtt-net${NC} Netzwerk erstellt!"
else
    echo -e "${BLUE}mqtt-net${NC} Netzwerk existiert bereits."
fi

echo -e "\n${GREEN}Alle benötigten Docker-Netzwerke wurden erstellt!${NC}"
echo -e "Du kannst jetzt die SwissAirDry-Container mit ${YELLOW}./start.sh${NC} starten."