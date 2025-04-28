"""
SwissAirDry - Utilities-Modul
-----------------------------

Dieses Modul enthält Hilfsfunktionen, die im gesamten SwissAirDry-Projekt verwendet werden.
"""

import os
import uuid
import time
import random
import string
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# Konfigurieren des Loggings
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_id(prefix="sard"):
    """Generiert eine eindeutige ID mit Präfix"""
    random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}-{uuid.uuid4().hex[:8]}-{int(time.time() * 1000)}-{os.getpid()}-{random_part}"


def timestamp():
    """Gibt den aktuellen Zeitstempel im ISO-Format zurück"""
    return datetime.now().isoformat()


def create_mqtt_client_id(prefix="client"):
    """Erstellt eine eindeutige MQTT-Client-ID"""
    timestamp = int(time.time() * 1000)
    random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"sard-{prefix}-{timestamp}-{random_part}"


def get_config_path(config_name):
    """Gibt den Pfad zu einer Konfigurationsdatei zurück"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "config", f"{config_name}.json")


def load_json_file(file_path):
    """Lädt eine JSON-Datei"""
    import json
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"Fehler beim Laden der JSON-Datei {file_path}: {str(e)}")
        return {}


def save_json_file(file_path, data):
    """Speichert Daten in einer JSON-Datei"""
    import json
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Fehler beim Speichern der JSON-Datei {file_path}: {str(e)}")
        return False


def parse_stm32_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parst und normalisiert Daten, die von STM32-Geräten gesendet werden.
    
    Diese Funktion übersetzt STM32-spezifische Feldnamen in standardisierte Namen,
    die vom SwissAirDry-System verwendet werden.
    """
    parsed_data = {}
    
    # Mapping von STM32-Feldnamen zu standardisierten Namen
    field_mapping = {
        "temp": "temperature",
        "hum": "humidity", 
        "pres": "pressure",
        "volt": "voltage",
        "curr": "current",
        "pwr": "power",
        "e": "energy",
        "rssi": "rssi",
        "status": "device_status"
    }
    
    # Übersetzung der Felder
    for stm_field, std_field in field_mapping.items():
        if stm_field in raw_data:
            parsed_data[std_field] = raw_data[stm_field]
    
    # Alle anderen Felder unverändert übernehmen
    for key, value in raw_data.items():
        if key not in field_mapping:
            parsed_data[key] = value
    
    return parsed_data


def format_stm32_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formatiert Antwortdaten, die an STM32-Geräte gesendet werden sollen.
    
    STM32-Geräte erwarten oft kompaktere Datenformate, um den Speicherverbrauch
    zu minimieren. Diese Funktion konvertiert standardisierte SwissAirDry-Daten
    in ein STM32-kompatibles Format.
    """
    formatted_data = {}
    
    # Kompaktere Feldnamen für STM32-Geräte
    field_mapping = {
        "temperature": "t",
        "humidity": "h", 
        "pressure": "p",
        "voltage": "v",
        "current": "c",
        "power": "pw",
        "energy": "e",
        "rssi": "rs",
        "device_status": "s",
        "command": "cmd",
        "config": "cfg"
    }
    
    # Übersetzung der Felder
    for std_field, stm_field in field_mapping.items():
        if std_field in data:
            formatted_data[stm_field] = data[std_field]
    
    # Essentielle Felder, die immer enthalten sein sollten
    if "timestamp" not in formatted_data and "timestamp" in data:
        formatted_data["ts"] = data["timestamp"]
    
    if "id" not in formatted_data and "id" in data:
        formatted_data["id"] = data["id"]
    
    return formatted_data