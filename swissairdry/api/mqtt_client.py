"""
SwissAirDry API - MQTT Client

MQTT-Client für die Kommunikation mit SwissAirDry-Geräten.

@author Swiss Air Dry Team <info@swissairdry.com>
@copyright 2023-2025 Swiss Air Dry Team
"""

import os
import json
import asyncio
import logging
import uuid
import time
import random
import string
from typing import Dict, Any, Callable, Optional, List

# Verwende die MQTT-Bibliothek, die mit den meisten Python-Versionen funktioniert
try:
    import paho.mqtt.client as mqtt
    # Definiere Konstanten, die in allen paho-mqtt-Versionen verfügbar sein sollten
    MQTT_ERR_SUCCESS = 0
    # Wenn MQTT-Konstanten nicht definiert sind, definieren wir sie selbst
    if not hasattr(mqtt, 'MQTT_ERR_SUCCESS'):
        mqtt.MQTT_ERR_SUCCESS = MQTT_ERR_SUCCESS
except ImportError:
    # Wenn die Bibliothek nicht installiert ist, ein Mock-Objekt erstellen
    mqtt = None
    print("MQTT-Bibliothek nicht gefunden. MQTT-Funktionalität deaktiviert.")


class MQTTClient:
    """
    MQTT-Client für die Kommunikation mit SwissAirDry-Geräten.
    """
    
    def __init__(
        self, 
        host: str = "localhost", 
        port: int = 1883, 
        username: str = "", 
        password: str = "",
        client_id: Optional[str] = None
    ):
        """
        Initialisiert den MQTT-Client.
        
        Args:
            host: MQTT-Broker-Host
            port: MQTT-Broker-Port
            username: MQTT-Benutzername (optional)
            password: MQTT-Passwort (optional)
            client_id: MQTT-Client-ID (optional, wird automatisch generiert wenn nicht angegeben)
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self.connected = False
        self.message_callbacks: Dict[str, List[Callable]] = {}
        self.logger = logging.getLogger("mqtt_client")
        self.user_client_id = client_id  # Speichere die übergebene Client-ID
    
    async def connect(self) -> bool:
        """
        Verbindet den Client mit dem MQTT-Broker.
        
        Returns:
            bool: True, wenn die Verbindung erfolgreich hergestellt wurde, sonst False.
        """
        if mqtt is None:
            self.logger.error("MQTT-Bibliothek nicht verfügbar")
            return False
        
        try:
            # Einzigartige Client-ID generieren, die zu 100% keine Konflikte verursacht
            if self.user_client_id:
                # Nutze die übergebene Client-ID und füge einen Zufallswert hinzu
                unique_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
                timestamp = int(time.time())
                self.client_id = f"{self.user_client_id}-{unique_suffix}-{timestamp}"
            else:
                # Generiere eine vollständig zufällige Client-ID
                unique_id = str(uuid.uuid4()).replace('-', '')[:8]
                timestamp = int(time.time() * 1000)  # Millisekunden für noch mehr Einzigartigkeit
                random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
                self.client_id = f"sard-{unique_id}-{timestamp}-{random_suffix}"
            
            self.logger.info(f"Sichere MQTT-Client-ID generiert: {self.client_id}")
            
            # Client sicher initialisieren - mit Fallbacks für alle paho-mqtt-Versionen
            try:
                # Neuer Stil mit API-Version (paho-mqtt >= 2.0.0)
                if hasattr(mqtt, 'CallbackAPIVersion'):
                    self.client = mqtt.Client(client_id=self.client_id, callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
                    self.logger.debug("MQTT-Client mit CallbackAPIVersion.VERSION1 erstellt")
                # Alter Stil ohne API-Version (paho-mqtt < 2.0.0) 
                else:
                    self.client = mqtt.Client(client_id=self.client_id)
                    self.logger.debug("MQTT-Client mit Standard-API erstellt")
            except (TypeError, AttributeError) as e:
                self.logger.warning(f"Fehler bei API-Version, verwende Fallback: {e}")
                try:
                    # Fallback ohne API-Version
                    self.client = mqtt.Client(client_id=self.client_id)
                    self.logger.debug("MQTT-Client mit Fallback erstellt")
                except Exception as e2:
                    # Letzter Ausweg: Client ohne Parameter
                    self.logger.error(f"Fallback fehlgeschlagen: {e2}, letzter Versuch ohne Parameter")
                    self.client = mqtt.Client()
            
            # Callbacks setzen
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            # Authentifizierung, falls erforderlich
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            
            # Verbindung herstellen
            self.logger.info(f"MQTT-Verbindung wird hergestellt mit {self.host}:{self.port}")
            self.client.connect_async(self.host, self.port, 60)
            
            # Client in eigener Thread starten
            self.client.loop_start()
            
            # Warte auf Verbindung mit exponentieller Backoff-Strategie
            # für robustere Verbindungsaufnahme
            wait_time = 0.5  # Start mit 500ms
            total_wait = 0
            max_wait = 15  # Maximal 15 Sekunden warten
            
            while total_wait < max_wait:
                if self.connected:
                    self.logger.info(f"MQTT-Client verbunden mit {self.host}:{self.port}")
                    return True
                
                await asyncio.sleep(wait_time)
                total_wait += wait_time
                wait_time = min(wait_time * 1.5, 2.0)  # Exponentiell erhöhen, max 2s
            
            # Wenn wir hierher gelangen, ist die Verbindung fehlgeschlagen
            self.client.loop_stop()
            self.logger.error(f"Zeitüberschreitung bei der MQTT-Verbindung nach {total_wait:.1f}s")
            return False
            
        except Exception as e:
            self.logger.error(f"Kritischer Fehler bei der MQTT-Verbindung: {str(e)}")
            return False
    
    async def disconnect(self) -> None:
        """
        Trennt die Verbindung zum MQTT-Broker.
        """
        if self.client and self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            self.logger.info("Vom MQTT-Broker getrennt")
    
    def is_connected(self) -> bool:
        """
        Prüft, ob der Client mit dem MQTT-Broker verbunden ist.
        
        Returns:
            bool: True, wenn verbunden, sonst False.
        """
        return self.connected
    
    async def subscribe(self, topic: str) -> bool:
        """
        Abonniert ein MQTT-Thema.
        
        Args:
            topic: MQTT-Thema
        
        Returns:
            bool: True, wenn das Abonnement erfolgreich war, sonst False.
        """
        if not self.is_connected():
            self.logger.error("Nicht mit MQTT-Broker verbunden")
            return False
        
        try:
            result, _ = self.client.subscribe(topic)
            success = result == mqtt.MQTT_ERR_SUCCESS
            if success:
                self.logger.info(f"Abonniert: {topic}")
            else:
                self.logger.error(f"Fehler beim Abonnieren von {topic}")
            return success
        except Exception as e:
            self.logger.error(f"Fehler beim Abonnieren von {topic}: {e}")
            return False
    
    async def unsubscribe(self, topic: str) -> bool:
        """
        Kündigt ein MQTT-Themen-Abonnement.
        
        Args:
            topic: MQTT-Thema
        
        Returns:
            bool: True, wenn die Kündigung erfolgreich war, sonst False.
        """
        if not self.is_connected():
            return False
        
        try:
            result, _ = self.client.unsubscribe(topic)
            success = result == mqtt.MQTT_ERR_SUCCESS
            if success:
                self.logger.info(f"Abonnement gekündigt: {topic}")
            return success
        except Exception as e:
            self.logger.error(f"Fehler beim Kündigen des Abonnements von {topic}: {e}")
            return False
    
    async def publish(self, topic: str, payload: Any, qos: int = 0, retain: bool = False) -> bool:
        """
        Veröffentlicht eine Nachricht zu einem MQTT-Thema.
        
        Args:
            topic: MQTT-Thema
            payload: Nachrichteninhalt (wird zu JSON konvertiert, wenn es kein String ist)
            qos: Quality of Service (0, 1 oder 2)
            retain: Ob die Nachricht vom Broker aufbewahrt werden soll
        
        Returns:
            bool: True, wenn die Veröffentlichung erfolgreich war, sonst False.
        """
        if not self.is_connected():
            self.logger.error("Nicht mit MQTT-Broker verbunden")
            return False
        
        try:
            # Konvertiere Payload zu JSON, wenn es kein String ist
            if not isinstance(payload, (str, bytes)):
                payload = json.dumps(payload)
            
            result = self.client.publish(topic, payload, qos, retain)
            success = result.rc == mqtt.MQTT_ERR_SUCCESS
            if success:
                self.logger.debug(f"Veröffentlicht: {topic}")
            else:
                self.logger.error(f"Fehler beim Veröffentlichen zu {topic}")
            return success
        except Exception as e:
            self.logger.error(f"Fehler beim Veröffentlichen zu {topic}: {e}")
            return False
    
    def add_message_callback(self, topic: str, callback: Callable) -> None:
        """
        Fügt einen Callback für ein bestimmtes MQTT-Thema hinzu.
        
        Args:
            topic: MQTT-Thema (kann Wildcards enthalten)
            callback: Callback-Funktion, die aufgerufen wird, wenn eine Nachricht empfangen wird
        """
        if topic not in self.message_callbacks:
            self.message_callbacks[topic] = []
        self.message_callbacks[topic].append(callback)
    
    def remove_message_callback(self, topic: str, callback: Callable) -> bool:
        """
        Entfernt einen Callback für ein bestimmtes MQTT-Thema.
        
        Args:
            topic: MQTT-Thema
            callback: Callback-Funktion
        
        Returns:
            bool: True, wenn der Callback entfernt wurde, sonst False.
        """
        if topic in self.message_callbacks and callback in self.message_callbacks[topic]:
            self.message_callbacks[topic].remove(callback)
            return True
        return False
    
    def _on_connect(self, client, userdata, flags, rc):
        """
        Wird aufgerufen, wenn der Client eine Verbindung zum Broker hergestellt hat.
        """
        if rc == 0:
            self.connected = True
            self.logger.info("Verbunden mit MQTT-Broker")
            
            # Standard-Themen abonnieren
            self.client.subscribe("swissairdry/#")
        else:
            self.logger.error(f"Verbindung zum MQTT-Broker fehlgeschlagen mit Code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """
        Wird aufgerufen, wenn der Client die Verbindung zum Broker verliert.
        """
        self.connected = False
        
        if rc == 0:
            self.logger.info("MQTT-Verbindung normal getrennt")
        elif rc == 7:  # Client-ID wird bereits verwendet
            self.logger.warning(f"MQTT-Verbindung nicht autorisiert (Code {rc}), Client-ID-Konflikt möglich")
            # Könnte hier automatische Wiederverbindung mit neuer ID implementieren
        else:
            self.logger.warning(f"Unerwartete Trennung vom MQTT-Broker mit Code {rc}")
            
        self.logger.info("MQTT-Client getrennt")
    
    def _on_message(self, client, userdata, msg):
        """
        Wird aufgerufen, wenn der Client eine Nachricht empfängt.
        """
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        
        self.logger.debug(f"Nachricht empfangen: {topic} {payload}")
        
        # Versuche, JSON zu parsen
        try:
            payload_json = json.loads(payload)
        except json.JSONDecodeError:
            payload_json = None
        
        # Rufe alle passenden Callbacks auf
        for callback_topic, callbacks in self.message_callbacks.items():
            if self._topic_matches(callback_topic, topic):
                for callback in callbacks:
                    try:
                        # Übergebe entweder JSON oder Rohtext, je nach Verfügbarkeit
                        callback_payload = payload_json if payload_json is not None else payload
                        callback(topic, callback_payload)
                    except Exception as e:
                        self.logger.error(f"Fehler in MQTT-Callback: {e}")
    
    @staticmethod
    def _topic_matches(pattern: str, topic: str) -> bool:
        """
        Prüft, ob ein Thema einem Muster entspricht (mit Wildcard-Unterstützung).
        
        Args:
            pattern: Muster (kann # oder + enthalten)
            topic: Zu prüfendes Thema
        
        Returns:
            bool: True, wenn das Thema dem Muster entspricht, sonst False.
        """
        if pattern == topic:
            return True
        
        pattern_parts = pattern.split('/')
        topic_parts = topic.split('/')
        
        if len(pattern_parts) > len(topic_parts) and '#' not in pattern_parts:
            return False
        
        for i, pattern_part in enumerate(pattern_parts):
            if pattern_part == '#':
                return True
            if pattern_part != '+' and (i >= len(topic_parts) or pattern_part != topic_parts[i]):
                return False
        
        return len(topic_parts) == len(pattern_parts)