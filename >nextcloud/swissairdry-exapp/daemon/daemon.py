#!/usr/bin/env python3
"""
SwissAirDry ExApp Daemon
------------------------

Diese Datei ist der Haupteinstiegspunkt für den Daemon der SwissAirDry ExApp.
Der Daemon läuft im Hintergrund und kommuniziert sowohl mit dem Nextcloud ExApp-Framework
als auch mit externen IoT-Geräten über MQTT.
"""

import os
import sys
import json
import time
import asyncio
import logging
import argparse
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

# Für Flask-basierte API
from flask import Flask, request, jsonify, Response
from werkzeug.serving import run_simple
from werkzeug.middleware.proxy_fix import ProxyFix

# MQTT-Client
import paho.mqtt.client as mqtt

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("swissairdry_daemon.log")
    ]
)
logger = logging.getLogger("swissairdry_daemon")

# Standardwerte
DEFAULT_PORT = 8701
DEFAULT_HOST = "localhost"
DEFAULT_MQTT_BROKER = "localhost"
DEFAULT_MQTT_PORT = 1883

# Flask-App erstellen
app = Flask("swissairdry")
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

# MQTT-Client
mqtt_client = None
mqtt_connected = False

# Status-Informationen
status = {
    "mqtt_connected": False,
    "devices": {},
    "alarms": [],
    "last_update": time.time()
}


class MQTTManager:
    """MQTT-Client-Manager für die Kommunikation mit IoT-Geräten"""
    
    def __init__(self, broker: str = DEFAULT_MQTT_BROKER, port: int = DEFAULT_MQTT_PORT, 
                 username: Optional[str] = None, password: Optional[str] = None,
                 client_id: Optional[str] = None):
        """Initialisiert den MQTT-Manager."""
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.client_id = client_id or f"swissairdry-daemon-{os.getpid()}"
        self.client = None
        self.connected = False
        self.subscriptions = []
        self.message_handlers = {}
        self.on_connect_callbacks = []
        
        logger.info(f"MQTT-Manager initialisiert für {broker}:{port}")
    
    def connect(self) -> bool:
        """Verbindet mit dem MQTT-Broker."""
        try:
            # Client erstellen
            self.client = mqtt.Client(client_id=self.client_id)
            
            # Callbacks registrieren
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            # Authentifizierung, falls nötig
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            
            # Connect
            self.client.connect(self.broker, self.port, keepalive=60)
            
            # Start loop in einem separaten Thread
            self.client.loop_start()
            
            logger.info(f"MQTT-Client verbunden mit {self.broker}:{self.port}")
            return True
        
        except Exception as e:
            logger.error(f"MQTT-Verbindungsfehler: {e}")
            self.connected = False
            return False
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback für erfolgreiche Verbindung."""
        if rc == 0:
            logger.info("MQTT-Verbindung hergestellt")
            self.connected = True
            
            # Erneut auf Topics subscriben
            for topic, qos in self.subscriptions:
                client.subscribe(topic, qos)
                logger.info(f"Erneut subscribed auf: {topic}")
            
            # On-Connect-Callbacks ausführen
            for callback in self.on_connect_callbacks:
                callback()
        else:
            logger.error(f"MQTT-Verbindung fehlgeschlagen mit Code {rc}")
            self.connected = False
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback für Verbindungsabbruch."""
        logger.warning(f"MQTT-Verbindung getrennt mit Code {rc}")
        self.connected = False
    
    def _on_message(self, client, userdata, msg):
        """Callback für eingehende Nachrichten."""
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        
        logger.debug(f"MQTT-Nachricht empfangen: {topic} = {payload}")
        
        # Spezifische Handler für dieses Topic ausführen
        if topic in self.message_handlers:
            for handler in self.message_handlers[topic]:
                try:
                    handler(topic, payload)
                except Exception as e:
                    logger.error(f"Fehler im Message-Handler für {topic}: {e}")
        
        # Globale Handler ausführen (für '#' oder '+' Subscriptions)
        for subscription_topic, handlers in self.message_handlers.items():
            if mqtt.topic_matches_sub(subscription_topic, topic):
                for handler in handlers:
                    try:
                        handler(topic, payload)
                    except Exception as e:
                        logger.error(f"Fehler im globalen Message-Handler für {subscription_topic} (Nachricht: {topic}): {e}")
    
    def subscribe(self, topic: str, qos: int = 0) -> bool:
        """Abonniert ein MQTT-Topic."""
        if not self.client or not self.connected:
            logger.warning(f"Kann nicht auf {topic} subscriben: Nicht verbunden")
            # Topic für späteren Resubscribe speichern
            self.subscriptions.append((topic, qos))
            return False
        
        result, _ = self.client.subscribe(topic, qos)
        if result == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"Subscribed auf: {topic}")
            # Topic für späteren Resubscribe speichern, falls noch nicht vorhanden
            if (topic, qos) not in self.subscriptions:
                self.subscriptions.append((topic, qos))
            return True
        else:
            logger.error(f"Fehler beim Subscriben auf {topic}: {result}")
            return False
    
    def unsubscribe(self, topic: str) -> bool:
        """Kündigt ein MQTT-Topic-Abonnement."""
        if not self.client or not self.connected:
            logger.warning(f"Kann nicht von {topic} unsubscriben: Nicht verbunden")
            return False
        
        result, _ = self.client.unsubscribe(topic)
        if result == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"Unsubscribed von: {topic}")
            # Topic aus der Subscriptions-Liste entfernen
            self.subscriptions = [(t, q) for (t, q) in self.subscriptions if t != topic]
            return True
        else:
            logger.error(f"Fehler beim Unsubscriben von {topic}: {result}")
            return False
    
    def publish(self, topic: str, payload: Union[str, dict, bytes], qos: int = 0, retain: bool = False) -> bool:
        """Veröffentlicht eine Nachricht auf einem MQTT-Topic."""
        if not self.client or not self.connected:
            logger.warning(f"Kann nicht auf {topic} publishen: Nicht verbunden")
            return False
        
        # Payload in den richtigen Typ konvertieren
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        if isinstance(payload, str):
            payload = payload.encode('utf-8')
        
        result, _ = self.client.publish(topic, payload, qos, retain)
        if result == mqtt.MQTT_ERR_SUCCESS:
            logger.debug(f"Published auf {topic}: {payload}")
            return True
        else:
            logger.error(f"Fehler beim Publishen auf {topic}: {result}")
            return False
    
    def add_message_handler(self, topic: str, handler) -> bool:
        """Fügt einen Handler für ein bestimmtes Topic hinzu."""
        if topic not in self.message_handlers:
            self.message_handlers[topic] = []
        
        if handler not in self.message_handlers[topic]:
            self.message_handlers[topic].append(handler)
            logger.debug(f"Message-Handler für {topic} hinzugefügt")
            return True
        
        return False
    
    def add_connect_callback(self, callback) -> bool:
        """Fügt einen Callback hinzu, der bei erfolgreicher Verbindung ausgeführt wird."""
        if callback not in self.on_connect_callbacks:
            self.on_connect_callbacks.append(callback)
            logger.debug("Connect-Callback hinzugefügt")
            return True
        
        return False
    
    def disconnect(self) -> bool:
        """Trennt die Verbindung zum MQTT-Broker."""
        if not self.client:
            return True
        
        try:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT-Client getrennt")
            self.connected = False
            return True
        except Exception as e:
            logger.error(f"Fehler beim Trennen der MQTT-Verbindung: {e}")
            return False


# MQTT-Nachrichtenhandler
def handle_device_status(topic, payload):
    """Verarbeitet Statusnachrichten von Geräten."""
    try:
        data = json.loads(payload)
        device_id = data.get('device_id')
        
        if not device_id:
            logger.warning(f"Gerät-ID fehlt in der Statusnachricht: {payload}")
            return
        
        # Status aktualisieren
        status["devices"][device_id] = {
            "status": data.get('status', 'unknown'),
            "last_update": time.time(),
            "data": data
        }
        
        logger.info(f"Gerätestatus aktualisiert: {device_id}")
        
        # Status global aktualisieren
        status["last_update"] = time.time()
    
    except json.JSONDecodeError:
        logger.error(f"Ungültiges JSON in der Statusnachricht: {payload}")
    except Exception as e:
        logger.error(f"Fehler bei der Verarbeitung der Statusnachricht: {e}")


def handle_device_telemetry(topic, payload):
    """Verarbeitet Telemetrienachrichten von Geräten."""
    try:
        data = json.loads(payload)
        device_id = data.get('device_id')
        
        if not device_id:
            logger.warning(f"Gerät-ID fehlt in der Telemetrienachricht: {payload}")
            return
        
        # Telemetriedaten aktualisieren, falls das Gerät bereits existiert
        if device_id in status["devices"]:
            status["devices"][device_id]["telemetry"] = data.get('sensors', {})
            status["devices"][device_id]["last_telemetry"] = time.time()
            
            logger.info(f"Gerät-Telemetrie aktualisiert: {device_id}")
        else:
            # Neues Gerät anlegen
            status["devices"][device_id] = {
                "status": "active",  # Annehmen, dass das Gerät aktiv ist, wenn es Telemetrie sendet
                "last_update": time.time(),
                "telemetry": data.get('sensors', {}),
                "last_telemetry": time.time(),
                "data": {"device_id": device_id}
            }
            
            logger.info(f"Neues Gerät hinzugefügt: {device_id}")
        
        # Status global aktualisieren
        status["last_update"] = time.time()
    
    except json.JSONDecodeError:
        logger.error(f"Ungültiges JSON in der Telemetrienachricht: {payload}")
    except Exception as e:
        logger.error(f"Fehler bei der Verarbeitung der Telemetrienachricht: {e}")


def handle_alarm(topic, payload):
    """Verarbeitet Alarmnachrichten."""
    try:
        data = json.loads(payload)
        alarm_id = data.get('id')
        device_id = data.get('device_id')
        
        if not alarm_id:
            logger.warning(f"Alarm-ID fehlt in der Alarmnachricht: {payload}")
            return
        
        # Existierenden Alarm finden und aktualisieren oder neuen Alarm hinzufügen
        existing_alarm = next((a for a in status["alarms"] if a.get('id') == alarm_id), None)
        
        if existing_alarm:
            # Alarm aktualisieren
            existing_alarm.update(data)
            existing_alarm["last_update"] = time.time()
            logger.info(f"Alarm aktualisiert: {alarm_id}")
        else:
            # Neuen Alarm hinzufügen
            data["received_at"] = time.time()
            data["last_update"] = time.time()
            status["alarms"].append(data)
            logger.info(f"Neuer Alarm hinzugefügt: {alarm_id}")
        
        # Status global aktualisieren
        status["last_update"] = time.time()
        
        # Wenn der Alarm zu einem Gerät gehört, den Alarmstatus des Geräts aktualisieren
        if device_id and device_id in status["devices"]:
            status["devices"][device_id]["has_alarm"] = True
            logger.info(f"Alarmstatus für Gerät {device_id} gesetzt")
    
    except json.JSONDecodeError:
        logger.error(f"Ungültiges JSON in der Alarmnachricht: {payload}")
    except Exception as e:
        logger.error(f"Fehler bei der Verarbeitung der Alarmnachricht: {e}")


# MQTT initialisieren
def init_mqtt(broker=DEFAULT_MQTT_BROKER, port=DEFAULT_MQTT_PORT, 
              username=None, password=None):
    """Initialisiert den MQTT-Client und verbindet ihn mit dem Broker."""
    global mqtt_client, mqtt_connected, status
    
    mqtt_client = MQTTManager(broker, port, username, password)
    
    # Handler für Gerätestatusänderungen registrieren
    mqtt_client.add_message_handler("swissairdry/+/status", handle_device_status)
    
    # Handler für Gerät-Telemetrie registrieren
    mqtt_client.add_message_handler("swissairdry/+/telemetry", handle_device_telemetry)
    
    # Handler für Alarme registrieren
    mqtt_client.add_message_handler("swissairdry/alarms", handle_alarm)
    
    # Verbinden
    success = mqtt_client.connect()
    mqtt_connected = success
    status["mqtt_connected"] = success
    
    if success:
        # Auf Topics subscriben
        mqtt_client.subscribe("swissairdry/+/status")
        mqtt_client.subscribe("swissairdry/+/telemetry")
        mqtt_client.subscribe("swissairdry/alarms")
        
        logger.info("MQTT-Client initialisiert und verbunden")
    else:
        logger.error("MQTT-Client konnte nicht verbunden werden")
    
    return success


@app.route('/api/status', methods=['GET'])
def api_status():
    """Liefert den aktuellen Status der Anwendung."""
    global status
    
    return jsonify({
        "status": "ok",
        "mqtt_connected": mqtt_connected,
        "devices_count": len(status["devices"]),
        "alarms_count": len(status["alarms"]),
        "last_update": status["last_update"]
    })


@app.route('/api/devices', methods=['GET'])
def api_get_devices():
    """Liefert eine Liste aller bekannten Geräte."""
    global status
    
    # Optionaler Filter für den Gerätestatus
    status_filter = request.args.get('status')
    
    devices = []
    for device_id, device_data in status["devices"].items():
        # Grundlegende Geräteinformationen extrahieren
        device = {
            "id": device_id,
            "status": device_data.get("status", "unknown"),
            "last_update": device_data.get("last_update"),
            "last_telemetry": device_data.get("last_telemetry"),
            "has_alarm": device_data.get("has_alarm", False)
        }
        
        # Gerätedaten hinzufügen, wenn vorhanden
        if "data" in device_data:
            device.update(device_data["data"])
        
        # Telemetriedaten hinzufügen, wenn vorhanden
        if "telemetry" in device_data:
            device["telemetry"] = device_data["telemetry"]
        
        # Filtern, falls ein Status-Filter gesetzt ist
        if status_filter and device["status"] != status_filter:
            continue
        
        devices.append(device)
    
    return jsonify({"devices": devices})


@app.route('/api/devices/<device_id>', methods=['GET'])
def api_get_device(device_id):
    """Liefert Details zu einem bestimmten Gerät."""
    global status
    
    if device_id not in status["devices"]:
        return jsonify({"error": "Gerät nicht gefunden"}), 404
    
    device_data = status["devices"][device_id]
    
    # Geräteinformationen zusammenstellen
    device = {
        "id": device_id,
        "status": device_data.get("status", "unknown"),
        "last_update": device_data.get("last_update"),
        "last_telemetry": device_data.get("last_telemetry"),
        "has_alarm": device_data.get("has_alarm", False)
    }
    
    # Gerätedaten hinzufügen, wenn vorhanden
    if "data" in device_data:
        device.update(device_data["data"])
    
    # Telemetriedaten hinzufügen, wenn vorhanden
    if "telemetry" in device_data:
        device["telemetry"] = device_data["telemetry"]
    
    return jsonify(device)


@app.route('/api/alarms', methods=['GET'])
def api_get_alarms():
    """Liefert eine Liste aller bekannten Alarme."""
    global status
    
    # Optionaler Filter für den Alarmschweregrad
    severity_filter = request.args.get('severity')
    
    alarms = status["alarms"]
    
    # Filtern, falls ein Schweregrad-Filter gesetzt ist
    if severity_filter:
        alarms = [a for a in alarms if a.get("severity") == severity_filter]
    
    return jsonify({"alarms": alarms})


@app.route('/api/alarms/<alarm_id>', methods=['GET'])
def api_get_alarm(alarm_id):
    """Liefert Details zu einem bestimmten Alarm."""
    global status
    
    alarm = next((a for a in status["alarms"] if a.get("id") == alarm_id), None)
    
    if not alarm:
        return jsonify({"error": "Alarm nicht gefunden"}), 404
    
    return jsonify(alarm)


@app.route('/mqtt/publish', methods=['POST'])
def mqtt_publish():
    """Veröffentlicht eine Nachricht über MQTT."""
    global mqtt_client, mqtt_connected
    
    if not mqtt_client or not mqtt_connected:
        return jsonify({"error": "MQTT-Client nicht verbunden"}), 503
    
    # Daten aus der Anfrage extrahieren
    data = request.json
    if not data:
        return jsonify({"error": "Keine Daten"}), 400
    
    topic = data.get('topic')
    payload = data.get('payload')
    qos = data.get('qos', 0)
    retain = data.get('retain', False)
    
    if not topic or payload is None:
        return jsonify({"error": "Topic und Payload sind erforderlich"}), 400
    
    # Nachricht veröffentlichen
    success = mqtt_client.publish(topic, payload, qos, retain)
    
    if success:
        return jsonify({"status": "ok", "message": f"Nachricht auf {topic} veröffentlicht"})
    else:
        return jsonify({"error": "Fehler beim Veröffentlichen der Nachricht"}), 500


@app.route('/mqtt/subscribe', methods=['POST'])
def mqtt_subscribe():
    """Abonniert ein MQTT-Topic."""
    global mqtt_client, mqtt_connected
    
    if not mqtt_client or not mqtt_connected:
        return jsonify({"error": "MQTT-Client nicht verbunden"}), 503
    
    # Daten aus der Anfrage extrahieren
    data = request.json
    if not data:
        return jsonify({"error": "Keine Daten"}), 400
    
    topic = data.get('topic')
    qos = data.get('qos', 0)
    
    if not topic:
        return jsonify({"error": "Topic ist erforderlich"}), 400
    
    # Topic abonnieren
    success = mqtt_client.subscribe(topic, qos)
    
    if success:
        return jsonify({"status": "ok", "message": f"Topic {topic} abonniert"})
    else:
        return jsonify({"error": "Fehler beim Abonnieren des Topics"}), 500


def main():
    """Hauptfunktion zum Starten des Daemons."""
    parser = argparse.ArgumentParser(description='SwissAirDry ExApp Daemon')
    parser.add_argument('--host', default=DEFAULT_HOST, help='Hostname/IP-Adresse zum Binden')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='Port zum Binden')
    parser.add_argument('--mqtt-broker', default=DEFAULT_MQTT_BROKER, help='MQTT-Broker-Hostname/IP')
    parser.add_argument('--mqtt-port', type=int, default=DEFAULT_MQTT_PORT, help='MQTT-Broker-Port')
    parser.add_argument('--mqtt-username', help='MQTT-Benutzername (optional)')
    parser.add_argument('--mqtt-password', help='MQTT-Passwort (optional)')
    parser.add_argument('--debug', action='store_true', help='Debug-Modus aktivieren')
    
    args = parser.parse_args()
    
    # Debug-Modus setzen
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    
    # MQTT initialisieren
    init_mqtt(args.mqtt_broker, args.mqtt_port, args.mqtt_username, args.mqtt_password)
    
    # Server starten
    logger.info(f"Starte SwissAirDry Daemon auf {args.host}:{args.port}")
    run_simple(args.host, args.port, app, use_reloader=args.debug, use_debugger=args.debug)


if __name__ == "__main__":
    main()