#!/usr/bin/env python3
"""
SwissAirDry ExApp Daemon

Dieser Daemon überwacht die Kommunikation zwischen der API und der Nextcloud ExApp.
Er stellt sicher, dass die Nextcloud-Integration funktioniert und synchronisiert Daten.
"""

import os
import time
import json
import logging
import threading
import traceback
import requests
from datetime import datetime, timedelta
import signal
import sys

# Logging-Konfiguration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/app/logs/exapp_daemon.log", mode='a')
    ]
)

logger = logging.getLogger("exapp_daemon")

# Umgebungsvariablen
NEXTCLOUD_URL = os.environ.get("NEXTCLOUD_URL", "https://localhost")
API_URL = os.environ.get("API_URL", "http://localhost:5000")
EXAPP_URL = os.environ.get("EXAPP_URL", "https://exapp.localhost")
SYNC_INTERVAL = int(os.environ.get("SYNC_INTERVAL", 300))  # 5 Minuten

# Status-Flags
running = True
last_sync = None
status = "Initialisierung..."

def signal_handler(sig, frame):
    """Handle SIGTERM and SIGINT für graceful shutdown"""
    global running
    logger.info("Signal erhalten, beende Daemon...")
    running = False
    sys.exit(0)

# Signal-Handler registrieren
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

class ExAppConnectionError(Exception):
    """Fehler bei der Verbindung zur ExApp"""
    pass

class NextcloudConnectionError(Exception):
    """Fehler bei der Verbindung zu Nextcloud"""
    pass

def check_exapp_health():
    """Prüft, ob die ExApp erreichbar ist"""
    try:
        response = requests.get(f"{EXAPP_URL}/health", timeout=10)
        if response.status_code != 200:
            raise ExAppConnectionError(f"ExApp Gesundheitscheck fehlgeschlagen: HTTP {response.status_code}")
        return True
    except requests.RequestException as e:
        logger.warning(f"ExApp nicht erreichbar: {str(e)}")
        return False

def check_nextcloud_status():
    """Prüft, ob Nextcloud erreichbar ist"""
    try:
        response = requests.get(f"{NEXTCLOUD_URL}/status.php", timeout=10)
        if response.status_code != 200:
            raise NextcloudConnectionError(f"Nextcloud Status fehlgeschlagen: HTTP {response.status_code}")
        status_data = response.json()
        return status_data.get("installed", False)
    except (requests.RequestException, json.JSONDecodeError) as e:
        logger.warning(f"Nextcloud nicht erreichbar: {str(e)}")
        return False

def check_exapp_installed():
    """Prüft, ob die SwissAirDry ExApp in Nextcloud installiert ist"""
    try:
        response = requests.get(
            f"{NEXTCLOUD_URL}/ocs/v2.php/cloud/apps",
            headers={"OCS-APIRequest": "true"},
            timeout=10
        )
        if response.status_code != 200:
            logger.warning(f"Konnte App-Liste nicht abrufen: HTTP {response.status_code}")
            return False
            
        try:
            apps_data = response.json()
            apps = apps_data.get("ocs", {}).get("data", {}).get("apps", [])
            return "swissairdry" in apps
        except (KeyError, json.JSONDecodeError) as e:
            logger.warning(f"Fehler beim Parsen der App-Liste: {str(e)}")
            return False
    except requests.RequestException as e:
        logger.warning(f"Fehler bei der Abfrage der installierten Apps: {str(e)}")
        return False

def sync_data():
    """Synchronisiert Daten zwischen API und ExApp"""
    global last_sync, status
    
    try:
        logger.info("Starte Datensynchronisation...")
        
        # Hier können verschiedene Synchronisationsaufgaben ausgeführt werden:
        # 1. Gerätestatus von der API zur ExApp senden
        # 2. Benutzereinstellungen synchronisieren
        # 3. Alarme und Benachrichtigungen verarbeiten
        
        # Simulierte Synchronisation (In der Produktion durch echte Synchronisation ersetzen)
        time.sleep(2)
        
        # Erfolgreich abgeschlossen
        last_sync = datetime.now()
        status = f"Letzte Synchronisation: {last_sync.strftime('%Y-%m-%d %H:%M:%S')}"
        logger.info(f"Datensynchronisation abgeschlossen: {status}")
        return True
    except Exception as e:
        error_msg = f"Fehler bei der Datensynchronisation: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        status = error_msg
        return False

def setup_required_directories():
    """Erstellt benötigte Verzeichnisse, falls nicht vorhanden"""
    os.makedirs("/app/logs", exist_ok=True)

def main():
    """Hauptfunktion des Daemons"""
    global status
    
    logger.info("SwissAirDry ExApp Daemon wird gestartet...")
    setup_required_directories()
    
    # Warten auf Verfügbarkeit der Dienste
    startup_delay = 10
    logger.info(f"Warte {startup_delay} Sekunden auf Verfügbarkeit der Dienste...")
    time.sleep(startup_delay)
    
    # Initialer Check der Verbindungen
    nc_available = check_nextcloud_status()
    exapp_available = check_exapp_health()
    exapp_installed = check_exapp_installed() if nc_available else False
    
    logger.info(f"Nextcloud Status: {'Verfügbar' if nc_available else 'Nicht verfügbar'}")
    logger.info(f"ExApp Status: {'Verfügbar' if exapp_available else 'Nicht verfügbar'}")
    logger.info(f"ExApp installiert: {'Ja' if exapp_installed else 'Nein'}")
    
    if not nc_available:
        status = "Warte auf Nextcloud..."
    elif not exapp_installed:
        status = "SwissAirDry App ist nicht in Nextcloud installiert."
    elif not exapp_available:
        status = "ExApp-Dienst ist nicht erreichbar."
    else:
        status = "Bereit für Synchronisation."
        # Initiale Synchronisation
        sync_data()
    
    # Hauptschleife des Daemons
    retry_count = 0
    while running:
        try:
            current_time = datetime.now()
            
            # Wenn wir noch nicht synchronisieren können, regelmäßig den Status prüfen
            if not nc_available or not exapp_installed or not exapp_available:
                if retry_count % 12 == 0:  # Status alle 60 Sekunden prüfen (5s * 12)
                    nc_available = check_nextcloud_status()
                    exapp_available = check_exapp_health()
                    exapp_installed = check_exapp_installed() if nc_available else False
                    
                    if not nc_available:
                        status = "Warte auf Nextcloud..."
                    elif not exapp_installed:
                        status = "SwissAirDry App ist nicht in Nextcloud installiert."
                    elif not exapp_available:
                        status = "ExApp-Dienst ist nicht erreichbar."
                    else:
                        status = "Bereit für Synchronisation."
                        # Erste Synchronisation nach Wiederherstellung der Verbindung
                        sync_data()
                
                retry_count += 1
                time.sleep(5)
                continue
            
            # Regelmäßige Synchronisation, wenn alle Komponenten verfügbar sind
            if last_sync is None or (current_time - last_sync).total_seconds() >= SYNC_INTERVAL:
                sync_data()
            
            # Kurze Wartezeit zur Reduzierung der CPU-Last
            time.sleep(5)
            
        except KeyboardInterrupt:
            logger.info("Daemon durch Benutzer beendet.")
            break
        except Exception as e:
            logger.error(f"Unerwarteter Fehler im Daemon: {str(e)}")
            logger.error(traceback.format_exc())
            status = f"Fehler: {str(e)}"
            time.sleep(30)  # Pause nach einem Fehler
    
    logger.info("SwissAirDry ExApp Daemon beendet.")

if __name__ == "__main__":
    main()