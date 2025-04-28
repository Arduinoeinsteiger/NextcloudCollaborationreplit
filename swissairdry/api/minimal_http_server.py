"""
Minimaler HTTP-Server für SwissAirDry ohne externe Abhängigkeiten

Diese Version der API verwendet nur die Python-Standardbibliothek und vermeidet
alle externen Abhängigkeiten wie Flask, FastAPI oder Werkzeug.
"""

import os
import json
import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Konfiguration
PORT = int(os.getenv("PORT", 5001))
HOST = os.getenv("HOST", "0.0.0.0")

# Status-Variablen
server_start_time = datetime.datetime.now()
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
        "last_seen": datetime.datetime.now().isoformat(),
        "created_at": datetime.datetime.now().isoformat(),
    },
    {
        "id": 2,
        "device_id": "device002",
        "name": "Luftentfeuchter 2",
        "type": "premium",
        "status": "offline",
        "last_seen": datetime.datetime.now().isoformat(),
        "created_at": datetime.datetime.now().isoformat(),
    }
]


class SwissAirDryHTTPHandler(BaseHTTPRequestHandler):
    """HTTP-Handler für die SwissAirDry API"""
    
    def do_GET(self):
        """Behandelt GET-Anfragen"""
        # Stats aktualisieren
        global api_stats
        api_stats["request_count"] += 1
        api_stats["last_request"] = datetime.datetime.now().isoformat()
        
        # URL parsen
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        try:
            # Root-Pfad
            if path == "/":
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(self._get_html_page().encode())
                
            # Health-Check
            elif path == "/health":
                uptime = (datetime.datetime.now() - server_start_time).total_seconds()
                data = {
                    "status": "ok",
                    "version": "1.0.0",
                    "uptime": uptime,
                    "stats": api_stats,
                }
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())
                
            # Alle Geräte
            elif path == "/api/devices":
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(devices).encode())
                
            # Einzelnes Gerät
            elif path.startswith("/api/devices/"):
                device_id = path.split("/")[-1]
                device = self._find_device(device_id)
                
                if device:
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(device).encode())
                else:
                    self.send_response(404)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"detail": "Gerät nicht gefunden"}).encode())
                    
            # Unbekannter Pfad
            else:
                self.send_response(404)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"detail": "Pfad nicht gefunden"}).encode())
        
        except Exception as e:
            api_stats["error_count"] += 1
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "detail": "Interner Serverfehler",
                "error": str(e)
            }).encode())
    
    def do_POST(self):
        """Behandelt POST-Anfragen"""
        # Stats aktualisieren
        global api_stats
        api_stats["request_count"] += 1
        api_stats["last_request"] = datetime.datetime.now().isoformat()
        
        # URL parsen
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        # Content-Length aus Header lesen
        content_length = int(self.headers.get('Content-Length', 0))
        
        try:
            # Sensordaten empfangen
            if path.startswith("/api/device/") and path.endswith("/data"):
                # Device-ID aus Pfad extrahieren
                parts = path.split("/")
                if len(parts) >= 4:
                    device_id = parts[3]
                    
                    # Request-Body lesen
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    
                    # Gerät suchen oder erstellen
                    device = self._find_device(device_id)
                    if not device:
                        # Gerät automatisch erstellen
                        new_device = {
                            "id": len(devices) + 1,
                            "device_id": device_id,
                            "name": f"Automatisch erstellt: {device_id}",
                            "type": "standard",
                            "status": "online",
                            "last_seen": datetime.datetime.now().isoformat(),
                            "created_at": datetime.datetime.now().isoformat(),
                        }
                        devices.append(new_device)
                    else:
                        # Gerät aktualisieren
                        device["status"] = "online"
                        device["last_seen"] = datetime.datetime.now().isoformat()
                    
                    # Antwort senden
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "status": "ok",
                        "message": "Daten erfolgreich gespeichert"
                    }).encode())
                else:
                    self.send_response(400)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "detail": "Ungültiger Pfad"
                    }).encode())
            
            # Unbekannter Pfad
            else:
                self.send_response(404)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"detail": "Pfad nicht gefunden"}).encode())
        
        except Exception as e:
            api_stats["error_count"] += 1
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "detail": "Interner Serverfehler",
                "error": str(e)
            }).encode())
    
    def _find_device(self, device_id):
        """Sucht ein Gerät anhand seiner ID"""
        for device in devices:
            if device["device_id"] == device_id:
                return device
        return None
    
    def _get_html_page(self):
        """Gibt die HTML-Startseite zurück"""
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
                <h1>SwissAirDry Minimal HTTP Server</h1>
                <p>Willkommen bei der minimalen SwissAirDry API.</p>
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


def run_server():
    """Startet den HTTP-Server"""
    print(f"SwissAirDry Minimal HTTP Server startet auf {HOST}:{PORT}...")
    server = HTTPServer((HOST, PORT), SwissAirDryHTTPHandler)
    print(f"Server läuft auf http://{HOST}:{PORT}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server wird gestoppt...")
    finally:
        server.server_close()
        print("Server gestoppt.")


if __name__ == "__main__":
    run_server()