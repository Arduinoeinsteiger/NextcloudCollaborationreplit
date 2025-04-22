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
        # Längere Client-ID mit Zeitstempel für bessere Eindeutigkeit
        client_id = f"swissairdry-api-{uuid.uuid4().hex[:8]}-{int(time.time())}"
        # clean_session auf False setzen für stabilere Verbindungen
        self.client = mqtt.Client(client_id=client_id, clean_session=False)
        self.is_connected_flag = False
        
        # Verbindungsstabilität optimieren
        self.client.reconnect_delay_set(min_delay=1, max_delay=60)
        self.client.max_inflight_messages_set(20)  # Default ist 20
        self.client.max_queued_messages_set(100)   # Mehr Nachrichten in der Queue
        # Anmerkung: connect_timeout ist leider kein direkt zugängliches Attribut
        # in dieser Version von paho-mqtt
        
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
                # keep_alive=60 bedeutet, dass der Client jede Minute ein PING sendet
                # Dies hilft, die Verbindung aktiv zu halten und schlechte Netzwerke zu erkennen
                self.client.connect(self.host, self.port, keepalive=60)
                
                # Client-Loop in eigenem Thread starten
                self.client.loop_start()
                
                # Warten, bis die Verbindung hergestellt ist oder ein Fehler auftritt
                # Längere Timeout-Zeit für langsame Netzwerke
                for _ in range(100):  # 10 Sekunden Timeout (erhöht von 3 Sekunden)
                    if self.is_connected_flag:
                        # Abonniere Standardtopics zusätzlich zum on_connect Callback
                        # (für mehr Robustheit)
                        self.client.subscribe("swissairdry/+/status")
                        return True
                    time.sleep(0.1)
                
                logger.warning("MQTT-Verbindungs-Timeout nach 10 Sekunden ohne Erfolg")
                return False
            except Exception as e:
                logger.error(f"MQTT-Verbindungsfehler: {e}")
                # Keine Exception werfen, stattdessen False zurückgeben
                return False
        
        result = await loop.run_in_executor(None, _connect)
        
        if not result:
            # Verbindung fehlgeschlagen, aber Client läuft noch für spätere Wiederverbindungsversuche
            logger.warning("MQTT-Verbindung nicht hergestellt, Client versucht Wiederverbindung im Hintergrund")
            # Starte automatischen Wiederverbindungsversuch
            asyncio.create_task(self._reconnect_background())
            # Keine Exception werfen, damit die API trotzdem funktioniert
    
    async def _reconnect_background(self):
        """Hintergrundaufgabe, die versucht, die MQTT-Verbindung wiederherzustellen."""
        logger.info("MQTT-Wiederverbindungsversuch gestartet")
        # 10 Sekunden warten, bevor der erste Wiederverbindungsversuch startet
        await asyncio.sleep(10)
        
        # Solange keine Verbindung besteht, alle 30 Sekunden einen neuen Versuch starten
        attempt = 1
        while not self.is_connected_flag and attempt <= 5:  # Maximal 5 Versuche
            logger.info(f"MQTT-Wiederverbindungsversuch {attempt}/5")
            await self.connect()
            if self.is_connected_flag:
                logger.info("MQTT-Wiederverbindung erfolgreich")
                return
            
            # Exponentielles Backoff: 10, 20, 40, 80, 160 Sekunden
            wait_time = 10 * (2 ** (attempt - 1))
            logger.info(f"MQTT-Wiederverbindung fehlgeschlagen, nächster Versuch in {wait_time} Sekunden")
            await asyncio.sleep(wait_time)
            attempt += 1
        
        if not self.is_connected_flag:
            logger.warning("MQTT-Wiederverbindung nach 5 Versuchen aufgegeben")
    
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
        # Wenn nicht verbunden, nur Warnung
        if not self.is_connected_flag:
            logger.warning(f"MQTT-Client ist nicht verbunden, Topic {topic} kann nicht abonniert werden")
            return
        
        loop = asyncio.get_event_loop()
        
        def _subscribe():
            try:
                result, _ = self.client.subscribe(topic, qos)
                if result != mqtt.MQTT_ERR_SUCCESS:
                    logger.warning(f"MQTT-Abonnementfehler: {result}")
                    return False
                return True
            except Exception as e:
                logger.error(f"Fehler beim Abonnieren des MQTT-Topics {topic}: {e}")
                return False
        
        # Fehler werden abgefangen und geloggt, aber nicht weitergegeben
        await loop.run_in_executor(None, _subscribe)
    
    async def unsubscribe(self, topic: str) -> None:
        """
        Kündigt ein MQTT-Topic-Abonnement.
        
        Args:
            topic: MQTT-Topic
        
        Raises:
            Exception: Wenn die Kündigung fehlschlägt
        """
        # Wenn nicht verbunden, nur Warnung
        if not self.is_connected_flag:
            logger.warning(f"MQTT-Client ist nicht verbunden, Abonnement für {topic} kann nicht gekündigt werden")
            return
        
        loop = asyncio.get_event_loop()
        
        def _unsubscribe():
            try:
                result, _ = self.client.unsubscribe(topic)
                if result != mqtt.MQTT_ERR_SUCCESS:
                    logger.warning(f"MQTT-Abonnementkündigungsfehler: {result}")
                    return False
                return True
            except Exception as e:
                logger.error(f"Fehler beim Kündigen des MQTT-Abonnements für {topic}: {e}")
                return False
        
        # Fehler werden abgefangen und geloggt, aber nicht weitergegeben
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
            # Bei unerwarteter Trennung versucht der Client automatisch,
            # sich wieder zu verbinden, da wir reconnect_delay_set verwenden
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