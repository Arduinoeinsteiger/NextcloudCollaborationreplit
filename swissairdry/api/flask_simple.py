"""
SwissAirDry API - Flask-basierte einfache API

Eine extrem vereinfachte Version der SwissAirDry API mit Flask.
"""

import os
import json
from datetime import datetime
from flask import Flask, jsonify, request

# Flask-App erstellen
app = Flask(__name__)

# Status-Variablen
server_start_time = datetime.now()
api_stats = {
    "request_count": 0,
    "error_count": 0,
    "last_request": None,
}

# Simulierte Geräte-Daten
devices = [
    {
        "id": 1,
        "device_id": "device001",
        "name": "Luftentfeuchter 1",
        "type": "standard",
        "status": "online",
        "last_seen": datetime.now().isoformat(),
        "created_at": datetime.now().isoformat(),
    },
    {
        "id": 2,
        "device_id": "device002",
        "name": "Luftentfeuchter 2",
        "type": "premium",
        "status": "offline",
        "last_seen": datetime.now().isoformat(),
        "created_at": datetime.now().isoformat(),
    }
]

@app.before_request
def log_request():
    """Logging für alle Anfragen"""
    api_stats["request_count"] += 1
    api_stats["last_request"] = datetime.now().isoformat()
    return None

@app.route('/')
def root():
    """Root-Endpoint, liefert eine einfache HTML-Seite zurück."""
    return """
    <html>
        <head>
            <title>SwissAirDry API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #0066cc; }
            </style>
        </head>
        <body>
            <h1>SwissAirDry Flask Simple API</h1>
            <p>Willkommen bei der einfachen SwissAirDry API (Flask-basiert).</p>
            <p>
                Verfügbare Endpoints:
                <ul>
                    <li><a href="/health">/health</a> - API-Status</li>
                    <li><a href="/api/devices">/api/devices</a> - Liste aller Geräte</li>
                </ul>
            </p>
        </body>
    </html>
    """

@app.route('/health')
def health_check():
    """Health-Check-Endpunkt für Monitoring."""
    return jsonify({
        "status": "ok",
        "version": "1.0.0",
        "uptime": (datetime.now() - server_start_time).total_seconds(),
        "stats": api_stats,
    })

@app.route('/api/devices')
def get_devices():
    """Gibt eine Liste aller Geräte zurück."""
    return jsonify(devices)

@app.route('/api/devices/<device_id>')
def get_device(device_id):
    """Gibt ein Gerät anhand seiner ID zurück."""
    for device in devices:
        if device["device_id"] == device_id:
            return jsonify(device)
    return jsonify({"detail": "Gerät nicht gefunden"}), 404

@app.route('/api/device/<device_id>/data', methods=['POST'])
def create_sensor_data(device_id):
    """Speichert neue Sensordaten für ein Gerät."""
    try:
        # Daten aus dem Request-Body auslesen
        data = request.get_json()
        
        # Prüfen, ob das Gerät existiert
        device_exists = False
        for device in devices:
            if device["device_id"] == device_id:
                device_exists = True
                device["status"] = "online"
                device["last_seen"] = datetime.now().isoformat()
                break
        
        # Wenn das Gerät nicht existiert, automatisch erstellen
        if not device_exists:
            new_device = {
                "id": len(devices) + 1,
                "device_id": device_id,
                "name": f"Automatisch erstellt: {device_id}",
                "type": "standard",
                "status": "online",
                "last_seen": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat(),
            }
            devices.append(new_device)
        
        # Erfolgsantwort zurückgeben
        return jsonify({"status": "ok", "message": "Daten erfolgreich gespeichert"})
    
    except Exception as e:
        return jsonify({"status": "error", "message": f"Fehler beim Verarbeiten der Daten: {str(e)}"}), 400

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5001))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"SwissAirDry Flask Simple API startet auf Port {port}...")
    app.run(host=host, port=port, debug=True)