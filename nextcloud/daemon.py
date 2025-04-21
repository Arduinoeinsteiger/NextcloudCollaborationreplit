#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SwissAirDry ExApp Daemon
------------------------

Dieser Daemon stellt die Verbindung zwischen der Nextcloud ExApp und dem SwissAirDry API-Server her.
Er dient als Middleware zwischen Nextcloud und der SwissAirDry API.
"""

import os
import sys
import logging
import json
import signal
import time
from typing import Dict, Any

import requests
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import paho.mqtt.client as mqtt

# Konfiguration aus Umgebungsvariablen
APP_ID = os.environ.get('APP_ID', 'swissairdry')
APP_VERSION = os.environ.get('APP_VERSION', '1.0.0')
APP_HOST = os.environ.get('APP_HOST', '0.0.0.0')
APP_PORT = int(os.environ.get('APP_PORT', 8081))
APP_SECRET = os.environ.get('APP_SECRET', 'change_me_in_production')
NEXTCLOUD_URL = os.environ.get('NEXTCLOUD_URL', '')
API_URL = os.environ.get('API_URL', '')
SIMPLE_API_URL = os.environ.get('SIMPLE_API_URL', '')
MQTT_BROKER = os.environ.get('MQTT_BROKER', '')
MQTT_PORT = int(os.environ.get('MQTT_PORT', 1883))
MQTT_WS_PORT = int(os.environ.get('MQTT_WS_PORT', 9001))
MQTT_USERNAME = os.environ.get('MQTT_USERNAME', '')
MQTT_PASSWORD = os.environ.get('MQTT_PASSWORD', '')
MQTT_CLIENT_ID = f'exapp-{APP_ID}-daemon'
MQTT_TOPIC_PREFIX = os.environ.get('MQTT_TOPIC_PREFIX', 'swissairdry')

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('exapp_daemon')

# Flask-App initialisieren
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = APP_SECRET
CORS(app)

# MQTT-Client initialisieren
mqtt_client = None

def setup_mqtt():
    """MQTT-Client einrichten und verbinden"""
    global mqtt_client
    try:
        mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_ID)
        
        # Authentifizierung, falls konfiguriert
        if MQTT_USERNAME and MQTT_PASSWORD:
            mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        
        # Callbacks registrieren
        mqtt_client.on_connect = on_mqtt_connect
        mqtt_client.on_message = on_mqtt_message
        mqtt_client.on_disconnect = on_mqtt_disconnect
        
        # Verbindung herstellen
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        logger.info(f"MQTT-Client gestartet und verbunden mit {MQTT_BROKER}:{MQTT_PORT}")
    except Exception as e:
        logger.error(f"Fehler beim Starten des MQTT-Clients: {e}")

def on_mqtt_connect(client, userdata, flags, rc):
    """Callback bei erfolgreicher MQTT-Verbindung"""
    if rc == 0:
        logger.info("Verbunden mit MQTT-Broker")
        # Auf relevante Topics subscriben
        client.subscribe(f"{MQTT_TOPIC_PREFIX}/+/status")
        client.subscribe(f"{MQTT_TOPIC_PREFIX}/exapp/+")
    else:
        logger.error(f"Verbindung zum MQTT-Broker fehlgeschlagen mit Code {rc}")

def on_mqtt_message(client, userdata, msg):
    """Callback bei eingehender MQTT-Nachricht"""
    try:
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        logger.debug(f"MQTT-Nachricht empfangen: {topic} - {payload}")
        
        # Hier kann die Nachricht verarbeitet werden
        # z.B. an verbundene Clients über WebSockets weiterleiten
    except Exception as e:
        logger.error(f"Fehler bei der Verarbeitung der MQTT-Nachricht: {e}")

def on_mqtt_disconnect(client, userdata, rc):
    """Callback bei MQTT-Verbindungsabbruch"""
    if rc != 0:
        logger.warning(f"Unerwartete Trennung vom MQTT-Broker. Versuche erneute Verbindung...")
        try:
            client.reconnect()
        except Exception as e:
            logger.error(f"Reconnect-Fehler: {e}")

@app.route('/')
def index():
    """ExApp-Startseite"""
    return jsonify({
        'app': APP_ID,
        'version': APP_VERSION,
        'status': 'running',
        'api_url': API_URL,
        'simple_api_url': SIMPLE_API_URL,
        'nextcloud_url': NEXTCLOUD_URL
    })

@app.route('/status')
def status():
    """Statusprüfung für Healthchecks"""
    return jsonify({'status': 'ok'})

@app.route('/api/proxy', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_proxy():
    """Proxy-Endpunkt für API-Anfragen"""
    if not API_URL:
        return jsonify({'error': 'API_URL nicht konfiguriert'}), 500
    
    try:
        # Ziel-URL konstruieren
        path = request.args.get('path', '')
        url = f"{API_URL}/{path.lstrip('/')}"
        
        # Anfrage an API weiterleiten
        headers = {k: v for k, v in request.headers.items() if k.lower() not in ['host', 'content-length']}
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            params=request.args,
            json=request.json if request.is_json else None,
            data=request.form if request.form else request.data,
            cookies=request.cookies,
            allow_redirects=False
        )
        
        # Antwort zurückgeben
        response_headers = {k: v for k, v in resp.headers.items() if k.lower() not in ['content-encoding', 'transfer-encoding']}
        return (resp.content, resp.status_code, response_headers)
    except Exception as e:
        logger.error(f"Proxy-Fehler: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/mqtt/publish', methods=['POST'])
def mqtt_publish():
    """Endpunkt zum Veröffentlichen von MQTT-Nachrichten"""
    global mqtt_client
    if not mqtt_client:
        return jsonify({'error': 'MQTT-Client nicht verbunden'}), 500
    
    try:
        data = request.json
        if not data or 'topic' not in data or 'payload' not in data:
            return jsonify({'error': 'Ungültige Anfrage, topic und payload erforderlich'}), 400
        
        topic = data['topic']
        payload = data['payload']
        qos = data.get('qos', 0)
        retain = data.get('retain', False)
        
        # Topic-Präfix hinzufügen, falls nicht vorhanden
        if not topic.startswith(f"{MQTT_TOPIC_PREFIX}/"):
            topic = f"{MQTT_TOPIC_PREFIX}/{topic}"
        
        # Nachricht veröffentlichen
        result = mqtt_client.publish(topic, json.dumps(payload), qos=qos, retain=retain)
        if result.rc != 0:
            return jsonify({'error': f'MQTT-Fehler {result.rc}'}), 500
        
        return jsonify({'success': True, 'topic': topic})
    except Exception as e:
        logger.error(f"MQTT-Publish-Fehler: {e}")
        return jsonify({'error': str(e)}), 500

def signal_handler(sig, frame):
    """Signal-Handler für sauberes Herunterfahren"""
    logger.info("Daemon wird heruntergefahren...")
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
    sys.exit(0)

if __name__ == '__main__':
    # Signal-Handler registrieren
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # MQTT-Client starten, wenn konfiguriert
    if MQTT_BROKER:
        setup_mqtt()
    else:
        logger.warning("MQTT_BROKER nicht konfiguriert, MQTT-Funktionalität deaktiviert")
    
    # Server starten
    logger.info(f"ExApp-Daemon wird gestartet auf {APP_HOST}:{APP_PORT}")
    app.run(host=APP_HOST, port=APP_PORT, debug=False)