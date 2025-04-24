"""
SwissAirDry BLE Scanner Modul
----------------------------

Dieses Modul nutzt Bluetooth Low Energy (BLE), um SwissAirDry-Geräte in der Nähe zu erkennen
und deren Standort basierend auf der Signalstärke zu bestimmen.
"""

import os
import asyncio
import logging
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Set

from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

# Logger konfigurieren
logger = logging.getLogger("swissairdry_ble")

# Konstanten
DEVICE_PREFIX = "SAD_"  # Präfix für SwissAirDry-Geräte
SCAN_INTERVAL = 60  # Scan-Intervall in Sekunden
RSSI_THRESHOLD = -85  # RSSI-Schwellenwert für die Nähe (-85 dBm)
MIN_DISCOVERY_COUNT = 2  # Minimale Anzahl an Entdeckungen für valide Geräteerkennung

# Standortdaten
locations = {}  # Speichert Infos über Standorte: {"location_id": {"name": "Name", "description": "..."}}

# Gerätestandorte
device_locations = {}  # Speichert den aktuellen Standort von Geräten: {"device_id": "location_id"}

# Gerätedaten
discovered_devices = {}  # Speichert entdeckte Geräte mit RSSI: {"device_id": {"rssi": -70, "last_seen": timestamp, "count": 5}}

# MQTT-Client für die Veröffentlichung von Standortänderungen
mqtt_client = None


def set_mqtt_client(client):
    """MQTT-Client für Standort-Updates setzen"""
    global mqtt_client
    mqtt_client = client


def load_locations(file_path: str = "locations.json") -> bool:
    """Standortdaten aus Datei laden"""
    global locations
    
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                locations = json.load(f)
            logger.info(f"{len(locations)} Standorte geladen")
            return True
        else:
            logger.warning(f"Standortdatei {file_path} nicht gefunden")
            return False
    except Exception as e:
        logger.error(f"Fehler beim Laden der Standorte: {e}")
        return False


def save_locations(file_path: str = "locations.json") -> bool:
    """Standortdaten in Datei speichern"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(locations, f, indent=2, ensure_ascii=False)
        logger.info(f"{len(locations)} Standorte gespeichert")
        return True
    except Exception as e:
        logger.error(f"Fehler beim Speichern der Standorte: {e}")
        return False


def get_device_location(device_id: str) -> Optional[str]:
    """Gibt den Standort eines Geräts zurück"""
    return device_locations.get(device_id)


def set_device_location(device_id: str, location_id: str, publish: bool = True):
    """Setzt den Standort eines Geräts"""
    old_location = device_locations.get(device_id)
    
    if old_location != location_id:
        # Standort hat sich geändert
        device_locations[device_id] = location_id
        logger.info(f"Gerät {device_id} ist jetzt an Standort {location_id}")
        
        if publish and mqtt_client and hasattr(mqtt_client, 'is_connected') and mqtt_client.is_connected():
            # Standortänderung über MQTT veröffentlichen
            location_name = locations.get(location_id, {}).get("name", location_id)
            data = {
                "device_id": device_id,
                "location_id": location_id,
                "location_name": location_name,
                "timestamp": datetime.now().isoformat()
            }
            
            try:
                asyncio.create_task(
                    mqtt_client.publish(f"swissairdry/{device_id}/location", data)
                )
            except Exception as e:
                logger.error(f"Fehler beim Veröffentlichen der Standortänderung: {e}")


async def device_callback(device: BLEDevice, advertisement_data: AdvertisementData):
    """Callback für entdeckte BLE-Geräte"""
    if device.name and device.name.startswith(DEVICE_PREFIX):
        device_id = device.name.replace(DEVICE_PREFIX, "")
        rssi = device.rssi
        
        # Gerätedaten aktualisieren
        if device_id not in discovered_devices:
            discovered_devices[device_id] = {
                "rssi": rssi,
                "last_seen": time.time(),
                "count": 1
            }
        else:
            discovered_devices[device_id]["rssi"] = rssi
            discovered_devices[device_id]["last_seen"] = time.time()
            discovered_devices[device_id]["count"] += 1
        
        logger.debug(f"Gerät {device_id} entdeckt, RSSI: {rssi}, Count: {discovered_devices[device_id]['count']}")


async def start_scanning():
    """Startet den BLE-Scan in einer Endlosschleife"""
    scanner = BleakScanner(detection_callback=device_callback)
    
    while True:
        try:
            # BLE-Scan durchführen
            logger.info("Starte BLE-Scan nach SwissAirDry-Geräten...")
            await scanner.start()
            await asyncio.sleep(5)  # 5 Sekunden scannen
            await scanner.stop()
            
            # Standortzuordnung basierend auf Signalstärke durchführen
            await process_device_locations()
            
            # Veraltete Geräte entfernen (älter als 5 Minuten)
            current_time = time.time()
            to_remove = []
            
            for device_id, data in discovered_devices.items():
                if current_time - data["last_seen"] > 300:  # 5 Minuten = 300 Sekunden
                    to_remove.append(device_id)
            
            for device_id in to_remove:
                logger.info(f"Entferne veraltetes Gerät {device_id}")
                discovered_devices.pop(device_id)
            
            # Warten bis zum nächsten Scan
            await asyncio.sleep(SCAN_INTERVAL - 5)  # 5 Sekunden bereits verbraucht für den Scan
            
        except Exception as e:
            logger.error(f"Fehler beim BLE-Scanning: {e}")
            await asyncio.sleep(10)  # Bei Fehler 10 Sekunden warten


async def process_device_locations():
    """Ordnet Geräte basierend auf RSSI-Stärke Standorten zu"""
    # Simulierte Standorte für den Test
    if not locations:
        logger.warning("Keine Standorte konfiguriert, verwende Beispielstandorte")
        locations.update({
            "office": {"name": "Büro", "description": "Hauptbüro"},
            "warehouse": {"name": "Lager", "description": "Lagerraum"},
            "workshop": {"name": "Werkstatt", "description": "Werkstattbereich"}
        })
    
    # In einer echten Implementierung würden wir hier Standortbeacons verwenden
    # Die folgende Logik basiert auf RSSI-Werten und ist ein vereinfachtes Beispiel
    
    for device_id, data in discovered_devices.items():
        if data["count"] < MIN_DISCOVERY_COUNT:
            # Ignoriere Geräte mit zu wenigen Entdeckungen
            continue
        
        rssi = data["rssi"]
        
        # Sehr einfache Standortbestimmung basierend auf RSSI
        # In einer realen Implementierung würde man mehrere Beacons oder 
        # eine Trilateration verwenden
        if rssi > -60:  # Sehr nah
            set_device_location(device_id, "office")
        elif rssi > -75:  # Mittlere Entfernung
            set_device_location(device_id, "workshop")
        elif rssi > RSSI_THRESHOLD:  # Weit entfernt, aber noch erkennbar
            set_device_location(device_id, "warehouse")
        # Unterhalb des Schwellenwerts gelten Geräte als "nicht in der Nähe"


class BLEManager:
    """Verwaltet BLE-Scan und Standortverfolgung"""
    
    def __init__(self, mqtt_client=None):
        """Initialisiert den BLE-Manager"""
        if mqtt_client:
            set_mqtt_client(mqtt_client)
        
        self.scanning_task = None
        self.is_scanning = False
        
        # Lade vorhandene Standorte
        load_locations()
    
    async def start_background_scan(self):
        """Startet den BLE-Scan im Hintergrund"""
        if not self.is_scanning:
            self.is_scanning = True
            self.scanning_task = asyncio.create_task(start_scanning())
            logger.info("BLE-Scan im Hintergrund gestartet")
    
    async def stop_background_scan(self):
        """Stoppt den BLE-Scan im Hintergrund"""
        if self.is_scanning and self.scanning_task:
            self.scanning_task.cancel()
            self.is_scanning = False
            logger.info("BLE-Scan im Hintergrund gestoppt")
    
    def add_location(self, location_id: str, name: str, description: str = "") -> bool:
        """Fügt einen neuen Standort hinzu"""
        if location_id in locations:
            return False
        
        locations[location_id] = {
            "name": name,
            "description": description
        }
        
        # Speichere aktualisierte Standorte
        save_locations()
        return True
    
    def update_location(self, location_id: str, name: str = None, description: str = None) -> bool:
        """Aktualisiert einen vorhandenen Standort"""
        if location_id not in locations:
            return False
        
        if name:
            locations[location_id]["name"] = name
        
        if description:
            locations[location_id]["description"] = description
        
        # Speichere aktualisierte Standorte
        save_locations()
        return True
    
    def remove_location(self, location_id: str) -> bool:
        """Entfernt einen Standort"""
        if location_id not in locations:
            return False
        
        del locations[location_id]
        
        # Aktualisiere Geräte, die sich an diesem Standort befanden
        for device_id, loc_id in list(device_locations.items()):
            if loc_id == location_id:
                device_locations.pop(device_id)
        
        # Speichere aktualisierte Standorte
        save_locations()
        return True
    
    def get_locations(self) -> Dict[str, Dict[str, str]]:
        """Gibt alle Standorte zurück"""
        return locations
    
    def get_device_locations(self) -> Dict[str, str]:
        """Gibt alle Gerät-Standort-Zuordnungen zurück"""
        return device_locations
    
    def get_discovered_devices(self) -> Dict[str, Dict[str, Any]]:
        """Gibt alle entdeckten BLE-Geräte mit Details zurück"""
        result = {}
        for device_id, data in discovered_devices.items():
            result[device_id] = {
                "rssi": data["rssi"],
                "last_seen": datetime.fromtimestamp(data["last_seen"]).isoformat(),
                "count": data["count"],
                "location": device_locations.get(device_id, "unknown")
            }
        return result