"""
SwissAirDry - MQTT-Client

Enthält die MQTT-Client-Implementierung für die SwissAirDry API.

@author Swiss Air Dry Team <info@swissairdry.com>
@copyright 2023-2025 Swiss Air Dry Team
"""

import json
import logging
import asyncio
import time
from typing import Any, Dict, Optional, Union

import paho.mqtt.client as mqtt

logger = logging.getLogger("swissairdry_api")


class MQTTClient:
    """Asynchrone MQTT-Client-Implementierung für die SwissAirDry API."""
    
    def __init__(
        self, 
        host: str, 
        port: int = 1883, 
        username: Optional[str] = None, 
        password: Optional[str] = None
    ):
        """
        Initialisiert den MQTT-Client.
        
        Args:
            host: MQTT-Broker-Hostname
            port: MQTT-Broker-Port
            username: Benutzername für die Authentifizierung
            password: Passwort für die Authentifizierung
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        
        # Zufälligen Client-ID erstellen, um doppelte Verbindungen zu vermeiden
        import uuid
        client_id = f"swissairdry-api-{uuid.uuid4().hex[:8]}"
        self.client = mqtt.Client(client_id=client_id)
        self.is_connected_flag = False
        
        # Verbindungsstabilität optimieren
        self.client.reconnect_delay_set(min_delay=1, max_delay=30)
        self.client.max_inflight_messages_set(20)  # Default ist 20
        self.client.max_queued_messages_set(100)   # Mehr Nachrichten in der Queue
        
        # Callbacks registrieren
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        # Authentifizierung einrichten
        if username and password:
            self.client.username_pw_set(username, password)
    
    async def connect(self) -> None:
        """
        Verbindet sich mit dem MQTT-Broker.
        
        Raises:
            Exception: Wenn die Verbindung fehlschlägt
        """
        loop = asyncio.get_event_loop()
        
        def _connect():
            try:
                # Höhere keep-alive Zeit und automatische Wiederverbindung
                # keep_alive=120 bedeutet, dass der Client alle 2 Minuten ein PING sendet
                # clean_session=False sorgt dafür, dass Abonnements bei Wiederverbindung erhalten bleiben
                self.client.connect(self.host, self.port, keepalive=120)
                
                # Client-Loop in eigenem Thread starten
                self.client.loop_start()
                
                # Warten, bis die Verbindung hergestellt ist oder ein Fehler auftritt
                # Längere Timeout-Zeit für langsame Netzwerke
                for _ in range(30):  # 3 Sekunden Timeout
                    if self.is_connected_flag:
                        return True
                    time.sleep(0.1)
                
                return False
            except Exception as e:
                logger.error(f"MQTT-Verbindungsfehler: {e}")
                # Keine Exception werfen, stattdessen False zurückgeben
                return False
        
        result = await loop.run_in_executor(None, _connect)
        
        if not result:
            # Verbindung fehlgeschlagen, aber Client läuft noch für spätere Wiederverbindungsversuche
            logger.warning("MQTT-Verbindung nicht hergestellt, Client versucht Wiederverbindung")
            # Keine Exception werfen, damit die API trotzdem funktioniert
    
    async def disconnect(self) -> None:
        """Trennt die Verbindung zum MQTT-Broker."""
        loop = asyncio.get_event_loop()
        
        def _disconnect():
            self.client.loop_stop()
            self.client.disconnect()
        
        await loop.run_in_executor(None, _disconnect)
        self.is_connected_flag = False
    
    async def publish(self, topic: str, payload: Union[str, Dict[str, Any]], qos: int = 0, retain: bool = False) -> None:
        """
        Veröffentlicht eine Nachricht an ein MQTT-Topic.
        
        Args:
            topic: MQTT-Topic
            payload: Nachrichteninhalt (String oder JSON-serialisierbares Dictionary)
            qos: Quality of Service (0, 1 oder 2)
            retain: Ob die Nachricht vom Broker gespeichert werden soll
        
        Raises:
            Exception: Wenn die Nachricht nicht veröffentlicht werden kann
        """
        # Wenn nicht verbunden, silent fail
        if not self.is_connected_flag:
            logger.warning(f"MQTT-Client ist nicht verbunden, Nachricht an {topic} wird nicht gesendet")
            return
        
        # Payload in String umwandeln, wenn es ein Dictionary ist
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        
        loop = asyncio.get_event_loop()
        
        def _publish():
            try:
                result = self.client.publish(topic, payload, qos, retain)
                if result.rc != mqtt.MQTT_ERR_SUCCESS:
                    logger.warning(f"MQTT-Veröffentlichungsfehler: {result.rc}")
                return result.rc == mqtt.MQTT_ERR_SUCCESS
            except Exception as e:
                logger.error(f"Fehler beim Veröffentlichen der MQTT-Nachricht: {e}")
                return False
        
        # Fehler werden abgefangen und geloggt, aber nicht weitergegeben
        await loop.run_in_executor(None, _publish)
    
    async def subscribe(self, topic: str, qos: int = 0) -> None:
        """
        Abonniert ein MQTT-Topic.
        
        Args:
            topic: MQTT-Topic
            qos: Quality of Service (0, 1 oder 2)
        
        Raises:
            Exception: Wenn das Abonnement fehlschlägt
        """
        if not self.is_connected_flag:
            raise Exception("MQTT-Client ist nicht verbunden")
        
        loop = asyncio.get_event_loop()
        
        def _subscribe():
            result, _ = self.client.subscribe(topic, qos)
            if result != mqtt.MQTT_ERR_SUCCESS:
                raise Exception(f"MQTT-Abonnementfehler: {result}")
        
        await loop.run_in_executor(None, _subscribe)
    
    async def unsubscribe(self, topic: str) -> None:
        """
        Kündigt ein MQTT-Topic-Abonnement.
        
        Args:
            topic: MQTT-Topic
        
        Raises:
            Exception: Wenn die Kündigung fehlschlägt
        """
        if not self.is_connected_flag:
            raise Exception("MQTT-Client ist nicht verbunden")
        
        loop = asyncio.get_event_loop()
        
        def _unsubscribe():
            result, _ = self.client.unsubscribe(topic)
            if result != mqtt.MQTT_ERR_SUCCESS:
                raise Exception(f"MQTT-Abonnementkündigungsfehler: {result}")
        
        await loop.run_in_executor(None, _unsubscribe)
    
    def is_connected(self) -> bool:
        """Gibt zurück, ob der Client mit dem MQTT-Broker verbunden ist."""
        return self.is_connected_flag
    
    def _on_connect(self, client, userdata, flags, rc):
        """
        Callback, der bei Verbindung mit dem MQTT-Broker aufgerufen wird.
        
        Args:
            client: MQTT-Client
            userdata: Benutzerdaten
            flags: Verbindungs-Flags
            rc: Verbindungsergebnis
        """
        if rc == 0:
            self.is_connected_flag = True
            logger.info(f"MQTT-Verbindung hergestellt mit {self.host}:{self.port}")
            
            # Standardthemen abonnieren
            client.subscribe("swissairdry/+/status")
        else:
            self.is_connected_flag = False
            logger.error(f"MQTT-Verbindung fehlgeschlagen mit Code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """
        Callback, der bei Trennung der Verbindung zum MQTT-Broker aufgerufen wird.
        
        Args:
            client: MQTT-Client
            userdata: Benutzerdaten
            rc: Trennungsergebnis
        """
        self.is_connected_flag = False
        if rc != 0:
            logger.warning(f"Unerwartete MQTT-Trennung mit Code {rc}")
        else:
            logger.info("MQTT-Verbindung getrennt")
    
    def _on_message(self, client, userdata, msg):
        """
        Callback, der beim Empfang einer MQTT-Nachricht aufgerufen wird.
        
        Args:
            client: MQTT-Client
            userdata: Benutzerdaten
            msg: Empfangene Nachricht
        """
        topic = msg.topic
        payload = msg.payload.decode("utf-8")
        
        try:
            # Versuchen, die Nutzlast als JSON zu interpretieren
            payload_json = json.loads(payload)
            logger.debug(f"MQTT-Nachricht empfangen: {topic} = {payload_json}")
            
            # Hier können spezifische Topics verarbeitet werden
            if topic.startswith("swissairdry/") and topic.endswith("/status"):
                device_id = topic.split("/")[1]
                if payload_json == "online":
                    logger.info(f"Gerät {device_id} ist online")
                elif payload_json == "offline":
                    logger.info(f"Gerät {device_id} ist offline")
        except json.JSONDecodeError:
            # Wenn die Nutzlast kein JSON ist, als String behandeln
            logger.debug(f"MQTT-Nachricht empfangen: {topic} = {payload}")
        except Exception as e:
            logger.error(f"Fehler bei der Verarbeitung der MQTT-Nachricht: {e}")