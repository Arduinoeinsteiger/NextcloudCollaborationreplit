"""
SwissAirDry API Server - Hauptmodul mit korrigierten Imports

Hauptmodul zum Starten des SwissAirDry API-Servers mit korrigierten Importpfaden.

@author Swiss Air Dry Team <info@swissairdry.com>
@copyright 2023-2025 Swiss Air Dry Team
"""

import os
import sys
import asyncio
import time
import logging
import contextlib
from datetime import datetime
from typing import Dict, Optional, List, Any, Union, AsyncIterator

# Füge das aktuelle Verzeichnis zum Python-Pfad hinzu
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from swissairdry.api.app import database
from swissairdry.api.app import models
from swissairdry import schemas
from swissairdry import crud
from swissairdry.api.app import mqtt
from swissairdry.api.app import utils

# API-Routen importieren
from swissairdry.api.app.routes import location
from swissairdry.api.app.routes import deck  # Alte Deck-Integration (wird durch ExApp ersetzt)
from swissairdry.api.app.routes import exapp  # Neue ExApp-Integration
from swissairdry.api.app.routes import dashboard  # Anpassbares Dashboard mit Drag-and-Drop

# Logging einrichten
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("api_server.log")
    ]
)
logger = logging.getLogger("swissairdry_api")

# Zugriffspfad zu den Dokumentationen konfigurieren
sys.path.append(os.path.join(os.path.dirname(current_dir), "docs"))
try:
    from serve_docs import register_docs_routes
    DOCS_AVAILABLE = True
except ImportError:
    DOCS_AVAILABLE = False
    logger.warning("API-Dokumentationsmodul nicht gefunden. Dokumentationsrouten deaktiviert.")

# MQTT-Client initialisieren
mqtt_client = None

# Status-Variablen
server_start_time = datetime.now()
api_stats = {
    "request_count": 0,
    "error_count": 0,
    "last_request": None,
}


async def check_primary_server_availability():
    """
    Hintergrundaufgabe, die regelmäßig prüft, ob der primäre API-Server 
    verfügbar ist, und bei Bedarf automatisch umschaltet.
    """
    while True:
        # Hier Code zur Überprüfung des primären Servers implementieren
        # Bei Ausfall zum Backup-Server wechseln
        await asyncio.sleep(60)  # Alle 60 Sekunden prüfen
        
async def check_mqtt_connection():
    """
    Hintergrundaufgabe, die regelmäßig den MQTT-Verbindungsstatus überprüft
    und bei Bedarf eine Wiederverbindung initiiert.
    """
    global mqtt_client
    
    while True:
        try:
            # Alle 30 Sekunden prüfen
            await asyncio.sleep(30)
            
            # MQTT-Verbindungsstatus überprüfen und ggf. wiederherstellen
            if mqtt_client:
                await mqtt_client.check_connection()
                
        except Exception as e:
            logger.error(f"Fehler bei Überprüfung der MQTT-Verbindung: {e}")
            await asyncio.sleep(10)  # Bei Fehler 10 Sekunden warten


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Lifespan-Handler für FastAPI.
    
    Diese Funktion übernimmt die Startup- und Shutdown-Logik in einem einzigen
    asynchronen Kontextmanager gemäß der modernen FastAPI-Lifespan-API.
    Siehe: https://fastapi.tiangolo.com/advanced/events/
    """
    global mqtt_client
    background_tasks = []
    
    # --- Startup-Logik ---
    logger.info("API-Server wird gestartet...")
    
    # MQTT-Client initialisieren
    mqtt_host = os.getenv("MQTT_HOST", "127.0.0.1") # Nutze lokale IP statt Hostname
    mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
    mqtt_user = os.getenv("MQTT_USER", "")
    mqtt_password = os.getenv("MQTT_PASSWORD", "")
    
    try:
        from swissairdry.api.app.mqtt import MQTTClient
        mqtt_client = MQTTClient(mqtt_host, mqtt_port, mqtt_user, mqtt_password)
        await mqtt_client.connect()
        logger.info(f"MQTT-Client verbunden mit {mqtt_host}:{mqtt_port}")
        
        # BLE-Scanner mit MQTT-Client initialisieren, wenn BLE aktiviert ist
        if os.getenv("BLE_ENABLED", "").lower() == "true":
            # Importiere hier, um Zirkelimporte zu vermeiden
            import ble_scanner
            from swissairdry.api.app.routes.location import get_ble_manager
            
            # BLE-Scanner initialisieren
            ble_manager = get_ble_manager()
            if hasattr(ble_manager, 'start_background_scan'):
                # BLE-Scanner im Hintergrund starten
                logger.info("BLE-Scanner wird gestartet...")
                await ble_manager.start_background_scan()
                logger.info("BLE-Scanner gestartet")
            else:
                logger.warning("BLE-Scanner konnte nicht initialisiert werden")
    except Exception as e:
        logger.error(f"Fehler bei der MQTT-Verbindung: {e}")
        logger.warning("MQTT-Verbindung fehlgeschlagen, Server läuft ohne MQTT-Unterstützung")
    
    # Hintergrundaufgaben starten
    background_tasks.append(asyncio.create_task(check_primary_server_availability()))
    background_tasks.append(asyncio.create_task(check_mqtt_connection()))
    
    logger.info("API-Server erfolgreich gestartet")
    
    # Kontrolle an FastAPI zurückgeben (yield anstelle von return in Kontextmanagern)
    yield
    
    # --- Shutdown-Logik ---
    logger.info("API-Server wird heruntergefahren...")
    
    # Hintergrundaufgaben abbrechen
    for task in background_tasks:
        if not task.done():
            task.cancel()
    
    # BLE-Scanner stoppen, wenn er läuft
    if os.getenv("BLE_ENABLED", "").lower() == "true":
        try:
            # Importiere hier, um Zirkelimporte zu vermeiden
            from routes.location import get_ble_manager
            
            ble_manager = get_ble_manager()
            if hasattr(ble_manager, 'stop_background_scan'):
                logger.info("BLE-Scanner wird gestoppt...")
                await ble_manager.stop_background_scan()
                logger.info("BLE-Scanner gestoppt")
        except Exception as e:
            logger.error(f"Fehler beim Stoppen des BLE-Scanners: {e}")
    
    # MQTT-Verbindung trennen
    if mqtt_client:
        await mqtt_client.disconnect()
        logger.info("MQTT-Client getrennt")


# Datenbank initialisieren
database.Base.metadata.create_all(bind=database.engine)

# FastAPI-App erstellen
app = FastAPI(
    title="SwissAirDry API",
    description="API für die Verwaltung von SwissAirDry-Geräten und -Daten",
    version="1.0.0",
    lifespan=lifespan,  # Verwende den modernen Lifespan-Handler
)

# API-Router registrieren
app.include_router(deck.router)
app.include_router(location.router)
app.include_router(exapp.router)

# Dokumentationsrouten registrieren, wenn verfügbar
if DOCS_AVAILABLE:
    try:
        register_docs_routes(app)
        logger.info("API-Dokumentationsrouten erfolgreich registriert")
    except Exception as e:
        logger.error(f"Fehler beim Registrieren der API-Dokumentationsrouten: {e}")
        DOCS_AVAILABLE = False

# CORS Middleware hinzufügen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In Produktion einschränken
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates und statische Dateien einrichten
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
static_dir = os.path.join(os.path.dirname(__file__), "static")

templates = Jinja2Templates(directory=templates_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# API-Endpunkte
@app.get("/api/devices", response_model=List[schemas.Device])
async def get_devices(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(database.get_db)
):
    """Gibt eine Liste aller Geräte zurück."""
    devices = crud.get_devices(db, skip=skip, limit=limit)
    return devices


@app.post("/api/devices", response_model=schemas.Device)
async def create_device(
    device: schemas.DeviceCreate, 
    db: Session = Depends(database.get_db)
):
    """Erstellt ein neues Gerät."""
    db_device = crud.get_device_by_device_id(db, device_id=device.device_id)
    if db_device:
        raise HTTPException(
            status_code=400, 
            detail="Gerät mit dieser ID existiert bereits"
        )
    return crud.create_device(db=db, device=device)


@app.get("/api/devices/{device_id}", response_model=schemas.Device)
async def get_device(device_id: str, db: Session = Depends(database.get_db)):
    """Gibt ein Gerät anhand seiner ID zurück."""
    db_device = crud.get_device_by_device_id(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Gerät nicht gefunden")
    return db_device


@app.put("/api/devices/{device_id}", response_model=schemas.Device)
async def update_device(
    device_id: str, 
    device: schemas.DeviceUpdate, 
    db: Session = Depends(database.get_db)
):
    """Aktualisiert ein Gerät."""
    db_device = crud.get_device_by_device_id(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Gerät nicht gefunden")
    return crud.update_device(db=db, device_id=device_id, device=device)


@app.delete("/api/devices/{device_id}", response_model=Dict[str, Any])
async def delete_device(device_id: str, db: Session = Depends(database.get_db)):
    """Löscht ein Gerät."""
    db_device = crud.get_device_by_device_id(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Gerät nicht gefunden")
    crud.delete_device(db=db, device_id=device_id)
    return {"status": "success", "message": f"Gerät {device_id} wurde gelöscht"}


@app.post("/api/devices/{device_id}/data", response_model=schemas.SensorData)
async def create_sensor_data(
    device_id: str, 
    data: schemas.SensorDataCreate, 
    db: Session = Depends(database.get_db)
):
    """Speichert neue Sensordaten für ein Gerät."""
    db_device = crud.get_device_by_device_id(db, device_id=device_id)
    if db_device is None:
        # Kein Fehler zurückgeben, stattdessen nur speichern
        logger.warning(f"Sensordaten für unbekanntes Gerät {device_id} empfangen")
        # Gerät automatisch erstellen
        device = schemas.DeviceCreate(
            device_id=device_id,
            name=f"Auto: {device_id}",
            type="unknown",
            status="online"
        )
        db_device = crud.create_device(db=db, device=device)
        logger.info(f"Gerät {device_id} automatisch erstellt")
    
    return crud.create_sensor_data(db=db, device_id=device_id, data=data)


@app.get("/api/devices/{device_id}/data", response_model=List[schemas.SensorData])
async def get_sensor_data(
    device_id: str, 
    limit: int = 100, 
    db: Session = Depends(database.get_db)
):
    """Gibt die Sensordaten eines Geräts zurück."""
    db_device = crud.get_device_by_device_id(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Gerät nicht gefunden")
    
    return crud.get_sensor_data_by_device_id(db, device_id=device_id, limit=limit)


@app.post("/api/devices/{device_id}/command", response_model=Dict[str, Any])
async def send_device_command(
    device_id: str, 
    command: schemas.DeviceCommand, 
    db: Session = Depends(database.get_db)
):
    """Sendet einen Befehl an ein Gerät über MQTT."""
    global mqtt_client
    
    # Prüfen, ob das Gerät existiert
    db_device = crud.get_device_by_device_id(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Gerät nicht gefunden")
    
    # Befehl über MQTT senden
    if mqtt_client and mqtt_client.is_connected():
        # Topic-Format: swissairdry/DEVICE_ID/command
        topic = f"swissairdry/{device_id}/command"
        # Payload als JSON
        payload = {
            "command": command.command,
            "value": command.value,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Nachricht senden
            success = await mqtt_client.publish(topic, payload)
            if success:
                logger.info(f"Befehl an {device_id} gesendet: {command.command}")
                return {"status": "success", "message": f"Befehl {command.command} an Gerät {device_id} gesendet"}
            else:
                logger.error(f"Fehler beim Senden des Befehls an {device_id}")
                raise HTTPException(status_code=500, detail="Fehler beim Senden des Befehls")
        except Exception as e:
            logger.error(f"Exception beim Senden des Befehls an {device_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Fehler: {str(e)}")
    else:
        # MQTT-Client nicht verbunden
        logger.error("MQTT-Client nicht verbunden, Befehl kann nicht gesendet werden")
        raise HTTPException(
            status_code=503, 
            detail="MQTT-Verbindung nicht verfügbar, Befehl kann nicht gesendet werden"
        )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware zum Loggen aller Anfragen"""
    start_time = time.time()
    
    # Request-Statistik aktualisieren
    api_stats["request_count"] += 1
    api_stats["last_request"] = datetime.now()
    
    response = await call_next(request)
    
    # Bei Fehler die Fehlerstatistik erhöhen
    if response.status_code >= 400:
        api_stats["error_count"] += 1
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    logger.info(
        f"{request.client.host}:{request.client.port} - "
        f"{request.method} {request.url.path} - "
        f"{response.status_code} - {process_time:.4f}s"
    )
    
    return response


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root-Endpoint, liefert eine einfache HTML-Seite zurück."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/jobs-preview", response_class=HTMLResponse)
async def jobs_preview(request: Request):
    """Zeigt eine Vorschau der Job-Management-API."""
    return templates.TemplateResponse("jobs_preview.html", {"request": request})


@app.get("/integration-options", response_class=HTMLResponse)
async def integration_options(request: Request):
    """Zeigt die Integrationsoptionen für SwissAirDry."""
    return templates.TemplateResponse("integration_options.html", {"request": request})


@app.get("/map-view", response_class=HTMLResponse)
async def map_view(request: Request, lat: float = None, lon: float = None, device: str = None):
    """Zeigt eine eingebettete Kartenansicht für Gerätestandorte."""
    return templates.TemplateResponse("map_view.html", {
        "request": request,
        "lat": lat,
        "lon": lon,
        "device": device
    })


@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health-Check-Endpunkt für Monitoring."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "uptime": (datetime.now() - server_start_time).total_seconds(),
        "stats": api_stats,
    }


@app.get("/admin", response_class=HTMLResponse)
async def admin_placeholder():
    """Platzhalter für den Admin-Bereich."""
    return """
    <html>
        <head>
            <title>SwissAirDry Admin</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #0066cc; }
            </style>
        </head>
        <body>
            <h1>SwissAirDry Admin-Bereich</h1>
            <p>Dieser Bereich ist noch in Entwicklung.</p>
            <p><a href="/">Zurück zur Startseite</a></p>
        </body>
    </html>
    """

@app.get("/api-documentation", response_class=HTMLResponse)
async def api_documentation():
    """Zeigt die API-Dokumentation an."""
    return """
    <html>
        <head>
            <title>SwissAirDry API-Dokumentation</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #0066cc; }
                .container { display: flex; flex-wrap: wrap; }
                .sidebar { width: 250px; padding-right: 20px; }
                .content { flex: 1; min-width: 300px; }
                .card { border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin-bottom: 15px; }
                code { background-color: #f5f5f5; padding: 2px 4px; border-radius: 3px; }
                pre { background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow: auto; }
                a { color: #0066cc; text-decoration: none; }
                a:hover { text-decoration: underline; }
                .badge { display: inline-block; padding: 3px 6px; border-radius: 3px; font-size: 12px; font-weight: bold; color: white; background-color: #0066cc; margin-right: 5px; }
            </style>
        </head>
        <body>
            <h1>SwissAirDry API-Dokumentation</h1>
            
            <div class="container">
                <div class="content">
                    <div class="card">
                        <h2>Übersicht</h2>
                        <p>Willkommen bei der SwissAirDry API. Diese API ermöglicht die Verwaltung und Überwachung von SwissAirDry-Geräten, sowie die Steuerung von Luftentfeuchtern in Echtzeit.</p>
                        <p>Die API ist RESTful und nutzt JSON für Anfragen und Antworten. Sie unterstützt Standard-HTTP-Methoden wie GET, POST, PUT und DELETE.</p>
                    </div>
                    
                    <div class="card">
                        <h2>Verfügbare Ressourcen</h2>
                        <ul>
                            <li><a href="/static/docs/API_DOCUMENTATION.md">Ausführliche API-Dokumentation (Markdown)</a></li>
                            <li><a href="/docs">Interaktive API-Dokumentation (Swagger UI)</a></li>
                            <li><a href="/openapi.json">OpenAPI-Spezifikation (JSON)</a></li>
                            <li><a href="/api/docs">API-Dokumentationsübersicht</a></li>
                        </ul>
                    </div>
                    
                    <div class="card">
                        <h2>Beispielanfrage</h2>
                        <p>Hier ist ein einfaches Beispiel für eine API-Anfrage mit curl:</p>
                        <pre><code>curl -X GET "https://api.vgnc.org/v1/api/devices" -H "X-API-Key: ihr_api_schlüssel"</code></pre>
                    </div>
                </div>
                
                <div class="sidebar">
                    <div class="card">
                        <h3>API-Endpunkte</h3>
                        <ul>
                            <li><a href="/api/devices">Geräte</a></li>
                            <li><a href="/api/customers">Kunden</a></li>
                            <li><a href="/api/jobs">Aufträge</a></li>
                        </ul>
                    </div>
                    
                    <div class="card">
                        <h3>Status</h3>
                        <p><span class="badge">Online</span></p>
                        <p><a href="/health">API-Status prüfen</a></p>
                    </div>
                    
                    <div class="card">
                        <h3>Support</h3>
                        <p>Bei Fragen wenden Sie sich bitte an:</p>
                        <p><a href="mailto:info@swissairdry.com">info@swissairdry.com</a></p>
                    </div>
                </div>
            </div>
            
            <p style="margin-top: 40px; text-align: center; color: #666;">
                &copy; 2023-2025 Swiss Air Dry Team. Alle Rechte vorbehalten.
            </p>
        </body>
    </html>
    """


# --- API-Endpunkte ---

@app.get("/api/devices", response_model=List[schemas.Device])
async def get_devices(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(database.get_db)
):
    """Gibt eine Liste aller Geräte zurück."""
    devices = crud.get_devices(db, skip=skip, limit=limit)
    return devices


@app.post("/api/devices", response_model=schemas.Device)
async def create_device(
    device: schemas.DeviceCreate, 
    db: Session = Depends(database.get_db)
):
    """Erstellt ein neues Gerät."""
    db_device = crud.get_device_by_device_id(db, device_id=device.device_id)
    if db_device:
        raise HTTPException(
            status_code=400, 
            detail="Gerät mit dieser ID existiert bereits"
        )
    return crud.create_device(db=db, device=device)


@app.get("/api/devices/{device_id}", response_model=schemas.Device)
async def get_device(device_id: str, db: Session = Depends(database.get_db)):
    """Gibt ein Gerät anhand seiner ID zurück."""
    db_device = crud.get_device_by_device_id(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Gerät nicht gefunden")
    return db_device


@app.put("/api/devices/{device_id}", response_model=schemas.Device)
async def update_device(
    device_id: str, 
    device: schemas.DeviceUpdate, 
    db: Session = Depends(database.get_db)
):
    """Aktualisiert ein Gerät."""
    db_device = crud.get_device_by_device_id(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Gerät nicht gefunden")
    return crud.update_device(db=db, device_id=device_id, device=device)


@app.delete("/api/devices/{device_id}", response_model=schemas.Message)
async def delete_device(device_id: str, db: Session = Depends(database.get_db)):
    """Löscht ein Gerät."""
    db_device = crud.get_device_by_device_id(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Gerät nicht gefunden")
    crud.delete_device(db=db, device_id=device_id)
    return {"message": f"Gerät {device_id} gelöscht"}


@app.post("/api/device/{device_id}/data", response_model=schemas.SensorDataResponse)
async def create_sensor_data(
    device_id: str, 
    data: schemas.SensorDataCreate, 
    db: Session = Depends(database.get_db)
):
    """Speichert neue Sensordaten für ein Gerät."""
    db_device = crud.get_device_by_device_id(db, device_id=device_id)
    if db_device is None:
        # Automatisch Gerät erstellen, wenn es nicht existiert
        device_create = schemas.DeviceCreate(
            device_id=device_id,
            name=f"Automatisch erstellt: {device_id}",
            type="standard"
        )
        db_device = crud.create_device(db=db, device=device_create)
    
    # Sensordaten speichern
    sensor_data = crud.create_sensor_data(
        db=db, 
        sensor_data=data, 
        device_id=db_device.id
    )
    
    # MQTT-Nachricht veröffentlichen
    if mqtt_client and mqtt_client.is_connected():
        topic = f"swissairdry/{device_id}/data"
        payload = {
            "device_id": device_id,
            "timestamp": sensor_data.timestamp.isoformat(),
            "temperature": sensor_data.temperature,
            "humidity": sensor_data.humidity,
            "power": sensor_data.power,
            "energy": sensor_data.energy,
            "relay_state": sensor_data.relay_state,
            "runtime": sensor_data.runtime
        }
        try:
            await mqtt_client.publish(topic, payload)
        except Exception as e:
            logger.error(f"Fehler beim Veröffentlichen der MQTT-Nachricht: {e}")
    
    # Gerätstatus aktualisieren
    update_data = {
        "status": "online",
        "last_seen": datetime.now()
    }
    crud.update_device(db=db, device_id=device_id, device=schemas.DeviceUpdate(**update_data))
    
    # Antwort mit möglichen Steuerbefehlen
    response = {"status": "ok"}
    
    # Wenn das Gerät ferngesteuert werden soll, füge Steuerungsbefehle hinzu
    if db_device.configuration and "remote_control" in db_device.configuration:
        if db_device.configuration["remote_control"].get("enabled", False):
            response["relay_control"] = db_device.configuration["remote_control"].get("relay_state", False)
    
    return response


@app.get("/api/device/{device_id}/data", response_model=List[schemas.SensorData])
async def get_sensor_data(
    device_id: str, 
    limit: int = 100, 
    db: Session = Depends(database.get_db)
):
    """Gibt die Sensordaten eines Geräts zurück."""
    db_device = crud.get_device_by_device_id(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Gerät nicht gefunden")
    
    sensor_data = crud.get_sensor_data_by_device(
        db=db, 
        device_id=db_device.id, 
        limit=limit
    )
    return sensor_data


@app.post("/api/device/{device_id}/command", response_model=schemas.Message)
async def send_device_command(
    device_id: str, 
    command: schemas.DeviceCommand, 
    db: Session = Depends(database.get_db)
):
    """Sendet einen Befehl an ein Gerät über MQTT."""
    db_device = crud.get_device_by_device_id(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Gerät nicht gefunden")
    
    if not mqtt_client or not hasattr(mqtt_client, 'is_connected') or not mqtt_client.is_connected():
        logger.warning(f"MQTT-Verbindung nicht verfügbar, Befehl wird nur in Datenbank gespeichert: {command.command}={command.value}")
        # Kein Fehler zurückgeben, stattdessen nur speichern
    
    # Geräte-Konfiguration aktualisieren
    if not db_device.configuration:
        db_device.configuration = {}
    
    if "remote_control" not in db_device.configuration:
        db_device.configuration["remote_control"] = {}
    
    if command.command == "relay":
        db_device.configuration["remote_control"]["enabled"] = True
        db_device.configuration["remote_control"]["relay_state"] = command.value
    
    # Konfiguration speichern
    crud.update_device(
        db=db, 
        device_id=device_id, 
        device=schemas.DeviceUpdate(configuration=db_device.configuration)
    )
    
    # MQTT-Befehl senden wenn MQTT verfügbar
    if mqtt_client and hasattr(mqtt_client, 'is_connected') and mqtt_client.is_connected():
        topic = f"swissairdry/{device_id}/cmd/{command.command}"
        try:
            await mqtt_client.publish(topic, command.value)
        except Exception as e:
            logger.error(f"Fehler beim Senden des MQTT-Befehls: {e}")
            # Fehler nicht an den Client weitergeben
    
    return {"message": "Befehl gesendet"}


# --- Hauptfunktion ---

if __name__ == "__main__":
    # Server starten
    uvicorn.run(
        "run2:app",
        host="0.0.0.0",
        port=int(os.getenv("API_PORT", "5000")),
        reload=True,
        reload_dirs=[os.path.dirname(__file__)]
    )