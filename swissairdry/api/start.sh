#!/bin/bash
set -e

# Warten auf verfügbare Datenbankverbindung
echo "Warte auf Datenbankverbindung..."
until python -c "import psycopg2; psycopg2.connect('${DATABASE_URL}')" 2>/dev/null; do
  echo "Datenbank ist noch nicht verfügbar - warte..."
  sleep 1
done

echo "Datenbankverbindung hergestellt!"

# Datenbank-Migrationen durchführen
echo "Führe Datenbank-Migrationen durch..."
# Hier könnten alembic oder andere Migrations-Tools verwendet werden
# alembic upgrade head

# API-Server starten
echo "Starte API-Server..."
if [ "${APP_DEBUG}" = "true" ]; then
  echo "Debug-Modus aktiviert"
  exec uvicorn app.run:app --host 0.0.0.0 --port 5000 --reload
else
  exec uvicorn app.run:app --host 0.0.0.0 --port 5000 --workers 4
fi