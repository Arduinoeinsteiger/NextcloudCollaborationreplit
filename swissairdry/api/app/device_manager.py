"""
SwissAirDry - Gerätemanager-Modul
---------------------------------

Dieses Modul verwaltet die verschiedenen Gerätetypen und deren Kommunikationsprotokolle.
Es unterstützt ESP8266, ESP32 und STM32 Mikrocontroller und ermöglicht die einheitliche
Verarbeitung von Gerätedaten unabhängig vom verwendeten Hardware-Typ.
"""

import json
import logging
import time
from enum import Enum
from typing import Dict, List, Optional, Union, Any

# Konfigurieren des Loggings
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeviceType(str, Enum):
    """Unterstützte Gerätetypen"""
    ESP8266 = "esp8266"
    ESP32 = "esp32"
    STM32 = "stm32"
    OTHER = "other"


class CommunicationType(str, Enum):
    """Unterstützte Kommunikationstypen"""
    MQTT = "mqtt"
    HTTP = "http"
    BLE = "ble"


class DeviceManager:
    """Verwaltet Geräte verschiedener Typen und deren Kommunikation"""
    
    def __init__(self, mqtt_client=None):
        self.devices: Dict[str, Dict[str, Any]] = {}
        self.mqtt_client = mqtt_client
        self.device_handlers = {
            DeviceType.ESP8266: self._handle_esp8266_data,
            DeviceType.ESP32: self._handle_esp32_data,
            DeviceType.STM32: self._handle_stm32_data,
            DeviceType.OTHER: self._handle_generic_data
        }
        logger.info("DeviceManager initialisiert")
    
    def register_device(self, device_id: str, device_type: DeviceType, 
                        communication_type: CommunicationType, 
                        name: str = "", location: str = "", 
                        metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Registriert ein neues Gerät im System"""
        if device_id in self.devices:
            logger.warning(f"Gerät mit ID {device_id} existiert bereits und wird aktualisiert")
        
        self.devices[device_id] = {
            "id": device_id,
            "type": device_type,
            "communication_type": communication_type,
            "name": name or f"Gerät {device_id}",
            "location": location,
            "metadata": metadata or {},
            "last_seen": time.time(),
            "status": "offline",
            "data": {}
        }
        
        logger.info(f"Gerät registriert: {device_id} (Typ: {device_type}, Kommunikation: {communication_type})")
        
        # Wenn MQTT, dann die entsprechenden Topics abonnieren
        if communication_type == CommunicationType.MQTT and self.mqtt_client:
            self._subscribe_device_topics(device_id, device_type)
        
        return True
    
    def update_device_data(self, device_id: str, data: Dict[str, Any], 
                           source: CommunicationType) -> bool:
        """Aktualisiert die Daten eines Geräts"""
        if device_id not in self.devices:
            logger.warning(f"Unbekanntes Gerät: {device_id}")
            return False
        
        device = self.devices[device_id]
        device["last_seen"] = time.time()
        device["status"] = "online"
        
        # Verarbeitung je nach Gerätetyp
        handler = self.device_handlers.get(device["type"], self._handle_generic_data)
        processed_data = handler(data, source)
        
        # Daten aktualisieren
        device["data"].update(processed_data)
        
        logger.debug(f"Gerätedaten aktualisiert: {device_id}")
        return True
    
    def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Gibt die Daten eines bestimmten Geräts zurück"""
        return self.devices.get(device_id)
    
    def get_all_devices(self) -> List[Dict[str, Any]]:
        """Gibt eine Liste aller registrierten Geräte zurück"""
        return list(self.devices.values())
    
    def get_devices_by_type(self, device_type: DeviceType) -> List[Dict[str, Any]]:
        """Gibt eine Liste aller Geräte eines bestimmten Typs zurück"""
        return [device for device in self.devices.values() 
                if device["type"] == device_type]
    
    def send_command(self, device_id: str, command: str, 
                     params: Optional[Dict[str, Any]] = None) -> bool:
        """Sendet einen Befehl an ein Gerät"""
        if device_id not in self.devices:
            logger.warning(f"Unbekanntes Gerät: {device_id}")
            return False
        
        device = self.devices[device_id]
        comm_type = device["communication_type"]
        
        if comm_type == CommunicationType.MQTT and self.mqtt_client:
            return self._send_mqtt_command(device_id, command, params or {})
        elif comm_type == CommunicationType.HTTP:
            return self._send_http_command(device_id, command, params or {})
        elif comm_type == CommunicationType.BLE:
            return self._send_ble_command(device_id, command, params or {})
        else:
            logger.error(f"Nicht unterstützter Kommunikationstyp für Gerät {device_id}: {comm_type}")
            return False
    
    # Interne Methoden für die Verarbeitung verschiedener Gerätetypen
    
    def _handle_esp8266_data(self, data: Dict[str, Any], 
                             source: CommunicationType) -> Dict[str, Any]:
        """Verarbeitet Daten von ESP8266-Geräten"""
        # ESP8266-spezifische Datenverarbeitung
        processed = {}
        
        # Standardwerte extrahieren (falls vorhanden)
        for key in ["temperature", "humidity", "pressure", "voltage", "rssi"]:
            if key in data:
                processed[key] = data[key]
        
        # ESP8266-spezifische Werte
        if "heap" in data:
            processed["free_memory"] = data["heap"]
        
        return processed
    
    def _handle_esp32_data(self, data: Dict[str, Any], 
                           source: CommunicationType) -> Dict[str, Any]:
        """Verarbeitet Daten von ESP32-Geräten"""
        # ESP32-spezifische Datenverarbeitung
        processed = {}
        
        # Standardwerte extrahieren (falls vorhanden)
        for key in ["temperature", "humidity", "pressure", "voltage", "rssi"]:
            if key in data:
                processed[key] = data[key]
        
        # ESP32-spezifische Werte
        if "heap" in data:
            processed["free_memory"] = data["heap"]
        
        # BLE-spezifische Daten
        if "ble_devices" in data:
            processed["ble_devices"] = data["ble_devices"]
        
        return processed
    
    def _handle_stm32_data(self, data: Dict[str, Any], 
                           source: CommunicationType) -> Dict[str, Any]:
        """Verarbeitet Daten von STM32-Geräten"""
        # STM32-spezifische Datenverarbeitung
        processed = {}
        
        # Standardwerte extrahieren (falls vorhanden)
        for key in ["temperature", "humidity", "pressure", "voltage"]:
            if key in data:
                processed[key] = data[key]
        
        # STM32-spezifische Werte
        if "status" in data:
            processed["device_status"] = data["status"]
        
        # Übersetzung von STM32-spezifischen Namen
        name_mapping = {
            "temp": "temperature",
            "hum": "humidity",
            "pres": "pressure",
            "volt": "voltage"
        }
        
        for stm_key, std_key in name_mapping.items():
            if stm_key in data and std_key not in processed:
                processed[std_key] = data[stm_key]
        
        return processed
    
    def _handle_generic_data(self, data: Dict[str, Any], 
                             source: CommunicationType) -> Dict[str, Any]:
        """Verarbeitet Daten von generischen Geräten"""
        # Einfache Durchreichung der Daten für unbekannte Gerätetypen
        return data
    
    # Interne Kommunikationsmethoden
    
    def _subscribe_device_topics(self, device_id: str, device_type: DeviceType) -> None:
        """Abonniert MQTT-Topics für ein Gerät"""
        if not self.mqtt_client:
            return
        
        # Basis-Topic für das Gerät
        base_topic = f"swissairdry/devices/{device_id}/#"
        
        # Je nach Gerätetyp können zusätzliche Topics abonniert werden
        if device_type == DeviceType.ESP8266 or device_type == DeviceType.ESP32:
            self.mqtt_client.subscribe(base_topic)
            self.mqtt_client.subscribe(f"swissairdry/sensors/{device_id}/#")
        elif device_type == DeviceType.STM32:
            self.mqtt_client.subscribe(base_topic)
            self.mqtt_client.subscribe(f"swissairdry/stm32/{device_id}/#")
        else:
            self.mqtt_client.subscribe(base_topic)
    
    def _send_mqtt_command(self, device_id: str, command: str, 
                          params: Dict[str, Any]) -> bool:
        """Sendet einen Befehl über MQTT"""
        if not self.mqtt_client:
            return False
        
        topic = f"swissairdry/commands/{device_id}"
        payload = {
            "command": command,
            "params": params,
            "timestamp": time.time()
        }
        
        try:
            self.mqtt_client.publish(topic, json.dumps(payload))
            return True
        except Exception as e:
            logger.error(f"Fehler beim Senden des MQTT-Befehls: {str(e)}")
            return False
    
    def _send_http_command(self, device_id: str, command: str, 
                          params: Dict[str, Any]) -> bool:
        """Sendet einen Befehl über HTTP"""
        # Hier würde die Implementierung für HTTP-Befehle folgen
        # Da dies mehr Konfiguration und externe Abhängigkeiten erfordert,
        # wird dies hier nur als Platzhalter implementiert
        logger.warning("HTTP-Befehle sind noch nicht implementiert")
        return False
    
    def _send_ble_command(self, device_id: str, command: str, 
                         params: Dict[str, Any]) -> bool:
        """Sendet einen Befehl über BLE"""
        # Hier würde die Implementierung für BLE-Befehle folgen
        # Da BLE spezielle Hardware und Treiber erfordert,
        # wird dies hier nur als Platzhalter implementiert
        logger.warning("BLE-Befehle sind noch nicht implementiert")
        return False


# Beispiel für die Verwendung:
if __name__ == "__main__":
    # Nur zu Testzwecken
    import paho.mqtt.client as mqtt
    
    client = mqtt.Client()
    device_manager = DeviceManager(client)
    
    # Gerät registrieren
    device_manager.register_device(
        "esp32-test-01", 
        DeviceType.ESP32, 
        CommunicationType.MQTT,
        name="Testgerät ESP32",
        location="Serverraum"
    )
    
    # STM32 Gerät registrieren
    device_manager.register_device(
        "stm32-test-01", 
        DeviceType.STM32, 
        CommunicationType.MQTT,
        name="Testgerät STM32",
        location="Werkstatt"
    )
    
    # Testdaten aktualisieren
    device_manager.update_device_data(
        "esp32-test-01",
        {
            "temperature": 22.5,
            "humidity": 45.8,
            "pressure": 1013.2,
            "heap": 45678
        },
        CommunicationType.MQTT
    )
    
    device_manager.update_device_data(
        "stm32-test-01",
        {
            "temp": 23.1,
            "hum": 48.2,
            "status": "running"
        },
        CommunicationType.MQTT
    )
    
    # Geräte abfragen
    print(device_manager.get_device("esp32-test-01"))
    print(device_manager.get_device("stm32-test-01"))