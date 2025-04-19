#!/bin/sh

# Prüfen, ob der SwissAirDry-Service auf dem angegebenen Port antwortet
wget -q --spider http://localhost:$PORT/health && exit 0 || exit 1