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
        
        # Noch eindeutigere Client-ID für verbesserte Stabilität
        import uuid
        import random
        import socket
        import os
        
        # Garantiert eindeutige Identifier mit mehreren Faktoren:
        # - Kompakte UUID (ohne Bindestriche)
        # - Präziser Timestamp (Millisekunden)
        # - Process-ID (PID) für Multi-Prozess-Umgebungen
        # - Zufällige Komponente größerer Bereich
        uid = str(uuid.uuid4()).replace('-', '')[:16]  # Kompakt aber eindeutig
        timestamp = int(time.time() * 10000)  # 10000tel Sekunden
        pid = os.getpid()
        random_suffix = random.randint(10000, 99999)
        
        # In Docker/Container-Umgebungen hat jeder Container eine eigene ID
        try:
            # Verwende Docker Container ID falls verfügbar (nur ersten 8 Zeichen)
            with open('/proc/self/cgroup', 'r') as f:
                for line in f:
                    if '/docker/' in line:
                        docker_id = line.split('/docker/')[1].strip()[:8]
                        break
                else:
                    docker_id = None
        except:
            docker_id = None
            
        # Hostname für weitere Eindeutigkeit
        try:
            hostname = socket.gethostname()[:6]
        except:
            hostname = "nohost"
        
        # Sicheren Client Identifier bauen
        context = docker_id[:6] if docker_id else "std"
        client_id = f"sard-{uid}-{timestamp}-{pid}-{random_suffix}-{hostname}-{context}"
        
        # MQTT-Standard: Maximal 23 Bytes
        if len(client_id) > 23:
            # Begrenzen aber Eindeutigkeit bewahren (UUID + Timestamp bleiben)
            client_id = f"sard-{uid[:8]}-{timestamp}-{random_suffix}"
                    
        logger.info(f"Sichere MQTT-Client-ID generiert: {client_id}")
        
        # clean_session auf True setzen, um alte Sessions zu vermeiden
        # Dies ist wichtig, um Probleme bei der Wiederverbindung zu vermeiden
        self.client = mqtt.Client(client_id=client_id, clean_session=True)
        self.is_connected_flag = False
        self.needs_reconnect = False  # Flag für Thread-sichere Wiederverbindung
        
        # Verbindungsstabilität optimieren
        # Benutze längere Verzögerungen, um aggressives Wiederverbinden zu vermeiden,
        # was zu weiteren Problemen führen kann (Broker-Überlastung, Bannung, etc.)
        self.client.reconnect_delay_set(min_delay=3, max_delay=120)
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
        
    async def check_connection(self) -> None:
        """
        Überprüft den Verbindungsstatus und initiiert bei Bedarf eine Wiederverbindung.
        Diese Methode sollte regelmäßig aus dem Hauptthread aufgerufen werden.
        """
        # Wenn ein Wiederverbindungsversuch angefordert wurde
        if self.needs_reconnect:
            logger.info("Ausstehendes Wiederverbindungs-Flag erkannt, starte Wiederverbindung...")
            self.needs_reconnect = False  # Flag zurücksetzen
            asyncio.create_task(self._reconnect_background())
            
        # Wenn keine Verbindung besteht, aber kein spezieller Wiederverbindungsversuch läuft
        elif not self.is_connected_flag and not self.needs_reconnect:
            logger.info("Keine MQTT-Verbindung aktiv, versuche Verbindung herzustellen...")
            asyncio.create_task(self.connect())
    
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
        prev_state = self.is_connected_flag
        self.is_connected_flag = False
        
        if rc != 0:
            # Fehlercode-spezifische Behandlung
            if rc == 7:
                # Code 7: Nicht autorisiert - möglicherweise ein Problem mit Client-ID oder Berechtigungen
                logger.warning(f"MQTT-Verbindung nicht autorisiert (Code 7), Client-ID-Konflikt möglich")
                # In diesem Fall sollte keine automatische Wiederverbindung erfolgen
                # um zu verhindern, dass weitere Fehler auftreten
                client.loop_stop()
                
                # Wir erstellen eine komplett neue Client-Instanz, da der alte möglicherweise
                # Probleme mit der Client-ID hat
                import uuid
                import random
                import socket
                import os
                
                # Komplett neue Client ID generieren (sehr kurz für MQTT-Standard)
                uid = str(uuid.uuid4()).replace('-', '')[:8]
                timestamp = int(time.time() * 1000) % 10000000  # Gekürzt: letzte 7 Ziffern
                random_suffix = random.randint(1000, 9999)
                new_client_id = f"sard-{uid}-{timestamp}-{random_suffix}"
                
                # MQTT-Standard: Maximal 23 Bytes/Zeichen für Client-ID
                if len(new_client_id) > 23:
                    new_client_id = f"sard-{uid[:6]}-{timestamp}"
                    
                logger.info(f"Erstelle neuen MQTT-Client mit ID: {new_client_id}")
                
                # Neuen Client erstellen
                self.client = mqtt.Client(client_id=new_client_id, clean_session=True)
                
                # Callbacks registrieren
                self.client.on_connect = self._on_connect
                self.client.on_disconnect = self._on_disconnect
                self.client.on_message = self._on_message
                
                # Verbindungsstabilität optimieren
                self.client.reconnect_delay_set(min_delay=2, max_delay=120)  # Längere Wartezeiten
                self.client.max_inflight_messages_set(20)
                self.client.max_queued_messages_set(100)
                
                # Authentifizierung einrichten
                if self.username and self.password:
                    self.client.username_pw_set(self.username, self.password)
                
                # Starte eine separate asynchrone Wiederverbindung mit dem neuen Client
                if prev_state:  # Nur wenn vorher verbunden, um Mehrfachaufrufe zu vermeiden
                    logger.info("Starte asynchrone Wiederverbindung mit neuem Client...")
                    # Warten Sie länger vor dem erneuten Verbindungsversuch
                    time.sleep(1)  # Kurze Pause im Thread 
                    # Wir können nicht direkt aus einem Thread asyncio.create_task aufrufen
                    # Stattdessen legen wir ein Flag fest, das in der Hauptschleife überprüft wird
                    self.needs_reconnect = True
            else:
                logger.warning(f"Unerwartete MQTT-Trennung mit Code {rc}")
                # Bei anderen unerwarteten Trennungen versucht der Client automatisch,
                # sich wieder zu verbinden, da wir reconnect_delay_set verwenden
                
                # Zusätzlich setzen wir ein Flag für eine manuelle Wiederverbindung nach einer Verzögerung
                # Falls die automatische Wiederverbindung nicht funktioniert
                if prev_state:  # Nur wenn vorher verbunden, um Mehrfachaufrufe zu vermeiden
                    logger.info("Plane zusätzliche Wiederverbindung als Fallback...")
                    time.sleep(0.5)  # Kurze Pause, damit die automatische Wiederverbindung zuerst versuchen kann
                    self.needs_reconnect = True  # Flag für manuelle Wiederverbindung
        else:
            logger.info("MQTT-Verbindung normal getrennt")
    
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