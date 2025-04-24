"""
SwissAirDry MicroPython MQTT-Client für ESP32-S6
-------------------------------------------------

Dieses Modul implementiert einen MQTT-Client für die Kommunikation
mit dem SwissAirDry-Backend.
"""

import json
import time
import machine
import ubinascii
from umqtt.simple import MQTTClient


class SwissAirDryMQTTClient:
    """
    MQTT-Client für die Kommunikation mit dem SwissAirDry-Backend.
    Implementiert Senden von Telemetriedaten, Empfangen von Kommandos
    und Verarbeitung von Konfigurationsänderungen.
    """
    
    def __init__(self, config, callback_handler=None):
        """
        Initialisiert den MQTT-Client.
        
        Args:
            config: Konfigurationsdictionary oder Pfad zur Konfigurationsdatei
            callback_handler: Optionale Callback-Funktion für empfangene Nachrichten
        """
        if isinstance(config, str):
            with open(config, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = config
        
        self.device_id = self.config.get("device", {}).get("id", 
                                                           "ESP32S6_" + ubinascii.hexlify(machine.unique_id()).decode())
        self.mqtt_config = self.config.get("mqtt", {})
        self.topic_prefix = self.mqtt_config.get("topic_prefix", "swissairdry")
        
        # MQTT-Topics
        self.topic_status = f"{self.topic_prefix}/{self.device_id}/status"
        self.topic_telemetry = f"{self.topic_prefix}/{self.device_id}/telemetry"
        self.topic_command = f"{self.topic_prefix}/{self.device_id}/command"
        self.topic_config = f"{self.topic_prefix}/{self.device_id}/config"
        
        # Client-ID generieren
        client_id_base = "sard_" + ubinascii.hexlify(machine.unique_id()).decode()
        self.client_id = f"{client_id_base}_{int(time.time())}"
        
        # MQTT-Client erstellen (wird später verbunden)
        self.client = None
        self.connected = False
        self.last_reconnect_attempt = 0
        self.reconnect_interval = 30  # Sekunden zwischen Wiederverbindungsversuchen
        
        # Callback-Handler
        self.callback_handler = callback_handler
        
        print(f"MQTT-Client initialisiert: {self.client_id}")
        print(f"Status-Topic: {self.topic_status}")
    
    def connect(self):
        """Verbindet mit dem MQTT-Broker."""
        if self.connected and self.client:
            return True
        
        broker = self.mqtt_config.get("broker", "localhost")
        port = self.mqtt_config.get("port", 1883)
        username = self.mqtt_config.get("username", "")
        password = self.mqtt_config.get("password", "")
        keepalive = self.mqtt_config.get("keepalive", 30)
        
        print(f"Verbinde mit MQTT-Broker: {broker}:{port}")
        
        try:
            self.client = MQTTClient(
                self.client_id,
                broker,
                port=port,
                user=username,
                password=password,
                keepalive=keepalive
            )
            
            # Callback für empfangene Nachrichten
            self.client.set_callback(self._on_message)
            
            # Verbindung herstellen
            self.client.connect()
            
            # Auf Kommando- und Konfigurations-Topic subscriben
            self.client.subscribe(self.topic_command)
            self.client.subscribe(self.topic_config)
            
            # Online-Status senden
            self.publish_status("online")
            
            self.connected = True
            self.last_reconnect_attempt = time.time()
            
            print(f"MQTT-Verbindung hergestellt mit {broker}:{port}")
            return True
            
        except Exception as e:
            print(f"MQTT-Verbindungsfehler: {e}")
            self.connected = False
            self.last_reconnect_attempt = time.time()
            return False
    
    def disconnect(self):
        """Trennt die Verbindung zum MQTT-Broker."""
        if self.connected and self.client:
            try:
                # Offline-Status senden
                self.publish_status("offline")
                # Verbindung trennen
                self.client.disconnect()
                self.connected = False
                print("MQTT-Verbindung getrennt")
                return True
            except Exception as e:
                print(f"Fehler beim Trennen der MQTT-Verbindung: {e}")
                return False
        return True
    
    def reconnect(self):
        """Stellt die Verbindung zum MQTT-Broker wieder her, wenn nötig."""
        current_time = time.time()
        
        # Wenn die letzte Wiederverbindung noch nicht lange her ist, warten
        if current_time - self.last_reconnect_attempt < self.reconnect_interval:
            return False
        
        print("Versuche MQTT-Wiederverbindung...")
        
        # Wenn noch verbunden, zuerst trennen
        if self.client:
            try:
                self.client.disconnect()
            except:
                pass
        
        self.connected = False
        return self.connect()
    
    def check_connection(self):
        """Prüft die MQTT-Verbindung und stellt sie ggf. wieder her."""
        if not self.connected:
            return self.reconnect()
        return True
    
    def _on_message(self, topic, msg):
        """Callback-Funktion für empfangene MQTT-Nachrichten."""
        topic = topic.decode('utf-8')
        msg = msg.decode('utf-8')
        
        print(f"MQTT-Nachricht empfangen: {topic} = {msg}")
        
        # An eigenen Callback-Handler weiterleiten, falls vorhanden
        if self.callback_handler:
            self.callback_handler(topic, msg)
    
    def publish_status(self, status):
        """Veröffentlicht eine Statusnachricht."""
        if not self.check_connection():
            print("Kann Status nicht senden: Keine MQTT-Verbindung")
            return False
        
        try:
            # Statusdaten erstellen
            status_data = {
                "device_id": self.device_id,
                "status": status,
                "timestamp": time.time(),
                "firmware": self.config.get("device", {}).get("firmware_version", "1.0.0"),
                "uptime": time.ticks_ms() // 1000  # Sekunden seit dem letzten Neustart
            }
            
            # Als JSON-String veröffentlichen
            self.client.publish(self.topic_status, json.dumps(status_data))
            print(f"Status '{status}' gesendet")
            return True
        
        except Exception as e:
            print(f"Fehler beim Senden des Status: {e}")
            self.connected = False
            return False
    
    def publish_telemetry(self, data):
        """Veröffentlicht Telemetriedaten."""
        if not self.check_connection():
            print("Kann Telemetrie nicht senden: Keine MQTT-Verbindung")
            return False
        
        try:
            # Telemetriedaten erstellen
            telemetry_data = {
                "device_id": self.device_id,
                "timestamp": time.time(),
                "sensors": data
            }
            
            # Als JSON-String veröffentlichen
            self.client.publish(self.topic_telemetry, json.dumps(telemetry_data))
            print(f"Telemetriedaten gesendet: {data}")
            return True
        
        except Exception as e:
            print(f"Fehler beim Senden der Telemetriedaten: {e}")
            self.connected = False
            return False
    
    def check_messages(self):
        """Prüft auf neue Nachrichten und ruft Callbacks auf."""
        if not self.check_connection():
            return False
        
        try:
            self.client.check_msg()
            return True
        except Exception as e:
            print(f"Fehler beim Prüfen auf Nachrichten: {e}")
            self.connected = False
            return False