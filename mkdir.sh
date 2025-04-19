#!/bin/bash
# Skript zum Erstellen der erforderlichen Verzeichnisstruktur für SwissAirDry

# Hauptverzeichnisse erstellen
mkdir -p swissairdry/api/app
mkdir -p swissairdry/api/simple
mkdir -p swissairdry/mqtt
mkdir -p swissairdry/db/init
mkdir -p swissairdry/nextcloud/{lib,static,templates,appinfo}
mkdir -p ssl/{certs,private}
mkdir -p nginx/conf.d

echo "Verzeichnisstruktur erfolgreich erstellt."