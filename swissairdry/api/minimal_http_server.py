"""
Minimaler HTTP-Server für SwissAirDry ohne externe Abhängigkeiten

Diese Version der API verwendet nur die Python-Standardbibliothek und vermeidet
alle externen Abhängigkeiten wie Flask, FastAPI oder Werkzeug.

Enthält QR-Code-Generator für einfache Gerätekonfiguration.
"""

import os
import json
import io
import base64
import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# QR-Code-Bibliotheken
import qrcode
from PIL import Image, ImageDraw, ImageFont

# Konfiguration
PORT = int(os.getenv("PORT", 5000))
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
            
            # QR-Code Generator
            elif path.startswith("/qrcode"):
                # Query-Parameter auswerten
                query_params = parse_qs(parsed_url.query)
                
                # Default-Werte
                data = query_params.get("data", [""])[0]
                if not data:
                    # Wenn kein data-Parameter, leiten wir zur QR-Code Generator-Seite um
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(self._get_qrcode_generator_page().encode())
                    return
                
                # QR-Code-Parameter
                size = query_params.get("size", ["300"])[0]
                title = query_params.get("title", ["SwissAirDry Konfiguration"])[0]
                format_param = query_params.get("format", ["png"])[0].lower()
                
                try:
                    size = int(size)
                    if size < 100:
                        size = 100
                    elif size > 800:
                        size = 800
                except ValueError:
                    size = 300
                
                # QR-Code erstellen
                img = self._generate_qrcode(data, size, title)
                
                # Format bestimmen und Antwort senden
                if format_param == "html":
                    # HTML mit eingebettetem Bild
                    buffered = io.BytesIO()
                    img.save(buffered, format="PNG")
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    
                    html_content = f"""
                    <html>
                        <head>
                            <title>SwissAirDry QR-Code</title>
                            <style>
                                body {{ font-family: Arial, sans-serif; margin: 40px; text-align: center; }}
                                h1 {{ color: #0066cc; }}
                                .qrcode-container {{ margin: 20px auto; padding: 20px; border: 1px solid #ddd; display: inline-block; }}
                                .qrcode-info {{ margin-top: 20px; color: #666; font-size: 14px; }}
                                .download-link {{ margin-top: 20px; }}
                                .download-link a {{ background-color: #0066cc; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; }}
                            </style>
                        </head>
                        <body>
                            <h1>{title}</h1>
                            <div class="qrcode-container">
                                <img src="data:image/png;base64,{img_str}" alt="QR-Code" />
                            </div>
                            <div class="qrcode-info">
                                <p>Scannen Sie diesen QR-Code mit der SwissAirDry App, um das Gerät zu konfigurieren.</p>
                            </div>
                            <div class="download-link">
                                <a href="/qrcode?data={data}&format=png&size={size}" download="swissairdry_config.png">QR-Code herunterladen</a>
                            </div>
                        </body>
                    </html>
                    """
                    self.wfile.write(html_content.encode())
                else:
                    # Bild direkt zurückgeben
                    buffered = io.BytesIO()
                    img.save(buffered, format="PNG")
                    
                    self.send_response(200)
                    self.send_header("Content-type", "image/png")
                    self.send_header("Content-Length", str(buffered.getbuffer().nbytes))
                    self.end_headers()
                    
                    # Bild senden
                    self.wfile.write(buffered.getvalue())
                    
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
    
    def _generate_qrcode(self, data, size=300, title="SwissAirDry Konfiguration"):
        """Generiert einen QR-Code mit Logo und Titel
        
        Args:
            data (str): Der zu codierende Text
            size (int): Größe des QR-Codes in Pixeln
            title (str): Titel, der über dem QR-Code angezeigt wird
            
        Returns:
            PIL.Image: Das generierte QR-Code-Bild
        """
        # QR-Code-Einstellungen
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # QR-Code als Bild erstellen
        qr_img = qr.make_image(fill_color="#0066cc", back_color="white").convert('RGBA')
        
        # Größe anpassen
        qr_img = qr_img.resize((size, size))
        
        # Hintergrund für Titel erstellen
        if title:
            # Erstelle ein Bild mit Platz für Titel
            background = Image.new('RGBA', (size, size + 40), (255, 255, 255, 255))
            draw = ImageDraw.Draw(background)
            
            # Titel hinzufügen
            try:
                # Versuche, eine spezifische Schriftart zu laden
                font = ImageFont.truetype("Arial", 18)
            except IOError:
                # Fallback zur Standardschriftart
                font = ImageFont.load_default()
            
            # Titel zentrieren
            title_width = draw.textlength(title, font=font)
            draw.text(((size - title_width) // 2, 10), title, font=font, fill="#0066cc")
            
            # QR-Code einfügen
            background.paste(qr_img, (0, 40))
            return background
        
        return qr_img
    
    def _get_qrcode_generator_page(self):
        """Gibt die HTML-Seite für den QR-Code-Generator zurück"""
        return """
        <html>
            <head>
                <title>SwissAirDry QR-Code Generator</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    h1 { color: #0066cc; }
                    .form-container { margin: 20px 0; }
                    .form-group { margin-bottom: 15px; }
                    label { display: block; margin-bottom: 5px; font-weight: bold; }
                    input, select { width: 100%; padding: 8px; box-sizing: border-box; }
                    button { background-color: #0066cc; color: white; border: none; padding: 10px 15px; cursor: pointer; }
                    .help-text { color: #666; font-size: 0.9em; margin-top: 3px; }
                </style>
            </head>
            <body>
                <h1>SwissAirDry QR-Code Generator</h1>
                <p>Mit diesem Generator können Sie QR-Codes für die Konfiguration von SwissAirDry-Geräten erstellen.</p>
                
                <div class="form-container">
                    <form action="/qrcode" method="get">
                        <div class="form-group">
                            <label for="data">Konfigurationsdaten:</label>
                            <input type="text" id="data" name="data" placeholder="WLAN:T:WPA;S:MeinNetzwerk;P:MeinPasswort;;" required>
                            <div class="help-text">Format: WLAN:T:WPA;S:NetzwerkName;P:Passwort;; oder benutzerdefinierte JSON-Daten</div>
                        </div>
                        
                        <div class="form-group">
                            <label for="title">Titel:</label>
                            <input type="text" id="title" name="title" placeholder="SwissAirDry Konfiguration" value="SwissAirDry Konfiguration">
                        </div>
                        
                        <div class="form-group">
                            <label for="size">Größe (100-800px):</label>
                            <input type="number" id="size" name="size" min="100" max="800" value="300">
                        </div>
                        
                        <div class="form-group">
                            <label for="format">Format:</label>
                            <select id="format" name="format">
                                <option value="html">HTML (mit Download-Option)</option>
                                <option value="png">PNG (nur Bild)</option>
                            </select>
                        </div>
                        
                        <button type="submit">QR-Code generieren</button>
                    </form>
                </div>
                
                <h2>Vordefinierte Konfigurationen</h2>
                <ul>
                    <li><a href="/qrcode?data=WLAN:T:WPA;S:SwissAirDry;P:SwissAirDry2023;;&title=WLAN-Konfiguration&format=html">WLAN-Konfiguration</a></li>
                    <li><a href="/qrcode?data={"device_id":"device001","server":"192.168.1.100:5002","mode":"standard"}&title=Gerätekonfiguration&format=html">Gerätekonfiguration</a></li>
                </ul>
                
                <p><a href="/">Zurück zur Hauptseite</a></p>
            </body>
        </html>
        """

    def _get_html_page(self):
        """Gibt die HTML-Startseite zurück"""
        return """
        <html>
            <head>
                <title>SwissAirDry API</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    h1 { color: #0066cc; }
                    .btn { display: inline-block; background-color: #0066cc; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; margin-top: 20px; }
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
                        <li><a href="/qrcode">/qrcode</a> - QR-Code Generator</li>
                    </ul>
                </p>
                <a href="/qrcode" class="btn">QR-Code Generator öffnen</a>
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