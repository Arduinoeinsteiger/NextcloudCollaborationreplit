#!/bin/bash
# Healthcheck script für SwissAirDry Nextcloud ExApp

# Überprüfen, ob der Server antwortet
HEALTH_ENDPOINT="http://localhost:8000/health"

response=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_ENDPOINT)

if [ "$response" = "200" ]; then
    exit 0
else
    echo "Healthcheck failed with status $response"
    exit 1
fi