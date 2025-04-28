"""
SwissAirDry - MQTT-Modul
-----------------------

Konfiguration und Verwaltung der MQTT-Verbindung für die Kommunikation mit IoT-Geräten.
"""

import os
import json
import time
import logging
import paho.mqtt.client as mqtt
from typing import Dict, Any, Callable, Optional

from swissairdry.utils import create_mqtt_client_id

# Konfiguriere Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MQTT-Broker-Konfiguration
MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 1883))
MQTT_USER = os.environ.get("MQTT_USER", "")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD", "")
MQTT_CLIENT_ID = os.environ.get("MQTT_CLIENT_ID", create_mqtt_client_id("api"))

# Globaler MQTT-Client
mqtt_client = None

# Callback-Funktionen-Registry
mqtt_callbacks = {}


def on_connect(client, userdata, flags, rc):
    """Callback für erfolgreiche Verbindung"""
    if rc == 0:
        logger.info(f"MQTT-Client verbunden mit {MQTT_BROKER}:{MQTT_PORT}")
        
        # Standard-Topics abonnieren
        client.subscribe("swissairdry/#")
        client.subscribe("swissairdry/+/data")
        client.subscribe("swissairdry/+/status")
        client.subscribe("swissairdry/+/config")
    else:
        logger.warning(f"MQTT-Verbindung nicht autorisiert (Code {rc}), Client-ID-Konflikt möglich")


def on_disconnect(client, userdata, rc):
    """Callback für Verbindungsabbruch"""
    logger.warning("MQTT-Client getrennt")
    if rc != 0:
        logger.error(f"Unerwartete Trennung, Code: {rc}")


def on_message(client, userdata, msg):
    """Callback für eingehende Nachrichten"""
    try:
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        
        logger.debug(f"MQTT-Nachricht empfangen: {topic} - {payload}")
        
        # Versuche, die Nachricht als JSON zu parsen
        try:
            payload_json = json.loads(payload)
        except json.JSONDecodeError:
            payload_json = {"raw": payload}
        
        # Rufe registrierte Callbacks für dieses Topic auf
        for pattern, callback in mqtt_callbacks.items():
            if mqtt_topic_matches(pattern, topic):
                callback(topic, payload_json)
        
    except Exception as e:
        logger.error(f"Fehler bei der Verarbeitung der MQTT-Nachricht: {str(e)}")


def mqtt_topic_matches(pattern: str, topic: str) -> bool:
    """
    Prüft, ob ein Topic einem Pattern entspricht.
    Unterstützt Wildcards wie + und #.
    """
    pattern_parts = pattern.split('/')
    topic_parts = topic.split('/')
    
    if len(pattern_parts) > len(topic_parts) and pattern_parts[-1] != '#':
        return False
    
    for i, pattern_part in enumerate(pattern_parts):
        if pattern_part == '#':
            return True
        
        if i >= len(topic_parts):
            return False
        
        if pattern_part != '+' and pattern_part != topic_parts[i]:
            return False
    
    return len(pattern_parts) == len(topic_parts)


def get_mqtt_client():
    """
    Gibt den MQTT-Client zurück und initialisiert ihn, falls noch nicht geschehen.
    """
    global mqtt_client
    
    if mqtt_client is None:
        mqtt_client = mqtt.Client()
        
        # Callbacks setzen
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.on_disconnect = on_disconnect
        
        # Authentifizierung, falls konfiguriert
        if MQTT_USER and MQTT_PASSWORD:
            mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        
        # Verbinden
        try:
            logger.info(f"Verbinde mit MQTT-Broker {MQTT_BROKER}:{MQTT_PORT}...")
            logger.info(f"MQTT-Client-ID: {MQTT_CLIENT_ID}")
            mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            
            # Im Hintergrund starten
            mqtt_client.loop_start()
        except Exception as e:
            logger.error(f"Fehler bei der Verbindung zum MQTT-Broker: {str(e)}")
    
    return mqtt_client


def publish_message(topic: str, payload: Dict[str, Any], retain: bool = False, qos: int = 0) -> bool:
    """
    Veröffentlicht eine Nachricht über MQTT.
    
    Args:
        topic: Das MQTT-Topic, unter dem die Nachricht veröffentlicht werden soll
        payload: Der Nachrichteninhalt als Dictionary (wird zu JSON serialisiert)
        retain: Ob die Nachricht vom Broker behalten werden soll
        qos: Quality of Service (0, 1 oder 2)
    
    Returns:
        bool: True, wenn die Nachricht erfolgreich veröffentlicht wurde, sonst False
    """
    client = get_mqtt_client()
    
    try:
        # Payload serialisieren
        json_payload = json.dumps(payload)
        
        # Nachricht veröffentlichen
        result = client.publish(topic, json_payload, qos=qos, retain=retain)
        
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            logger.error(f"Fehler beim Veröffentlichen der MQTT-Nachricht: {result.rc}")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Fehler beim Veröffentlichen der MQTT-Nachricht: {str(e)}")
        return False


def register_callback(topic_pattern: str, callback: Callable[[str, Dict[str, Any]], None]) -> None:
    """
    Registriert einen Callback für ein bestimmtes Topic-Pattern.
    
    Args:
        topic_pattern: Das Topic-Pattern, für das der Callback registriert werden soll
                     (unterstützt Wildcards wie + und #)
        callback: Die aufzurufende Funktion, wenn eine passende Nachricht empfangen wird
                 Die Funktion muss zwei Parameter akzeptieren: topic und payload
    """
    mqtt_callbacks[topic_pattern] = callback


def unregister_callback(topic_pattern: str) -> bool:
    """
    Hebt die Registrierung eines Callbacks auf.
    
    Args:
        topic_pattern: Das Topic-Pattern, für das der Callback aufgehoben werden soll
    
    Returns:
        bool: True, wenn der Callback erfolgreich aufgehoben wurde, sonst False
    """
    if topic_pattern in mqtt_callbacks:
        del mqtt_callbacks[topic_pattern]
        return True
    
    return False