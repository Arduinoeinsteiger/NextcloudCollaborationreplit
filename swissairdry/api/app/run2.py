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
from datetime import datetime
from typing import Dict, Optional, List, Any, Union

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

import database
import models
import schemas
import crud
import mqtt
import utils

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

# Datenbank initialisieren
database.Base.metadata.create_all(bind=database.engine)

# FastAPI-App erstellen
app = FastAPI(
    title="SwissAirDry API",
    description="API für die Verwaltung von SwissAirDry-Geräten und -Daten",
    version="1.0.0",
)

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


@app.on_event("startup")
async def startup_event():
    """Wird beim Start der Anwendung aufgerufen."""
    global mqtt_client
    
    logger.info("API-Server wird gestartet...")
    
    # MQTT-Client initialisieren
    mqtt_host = os.getenv("MQTT_HOST", "localhost")
    mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
    mqtt_user = os.getenv("MQTT_USER", "")
    mqtt_password = os.getenv("MQTT_PASSWORD", "")
    
    try:
        mqtt_client = mqtt.MQTTClient(mqtt_host, mqtt_port, mqtt_user, mqtt_password)
        await mqtt_client.connect()
        logger.info(f"MQTT-Client verbunden mit {mqtt_host}:{mqtt_port}")
    except Exception as e:
        logger.error(f"Fehler bei der MQTT-Verbindung: {e}")
    
    # Hintergrundaufgabe starten
    asyncio.create_task(check_primary_server_availability())
    
    logger.info("API-Server erfolgreich gestartet")


@app.on_event("shutdown")
async def shutdown_event():
    """Wird beim Herunterfahren der Anwendung aufgerufen."""
    global mqtt_client
    
    logger.info("API-Server wird heruntergefahren...")
    
    # MQTT-Verbindung trennen
    if mqtt_client:
        await mqtt_client.disconnect()
        logger.info("MQTT-Client getrennt")


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
    
    if not mqtt_client or not mqtt_client.is_connected():
        raise HTTPException(
            status_code=503, 
            detail="MQTT-Verbindung nicht verfügbar"
        )
    
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
    
    # MQTT-Befehl senden
    topic = f"swissairdry/{device_id}/cmd/{command.command}"
    try:
        await mqtt_client.publish(topic, command.value)
        return {"message": "Befehl gesendet"}
    except Exception as e:
        logger.error(f"Fehler beim Senden des MQTT-Befehls: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Fehler beim Senden des Befehls: {str(e)}"
        )


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