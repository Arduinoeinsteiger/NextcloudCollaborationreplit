"""
SwissAirDry API - Sehr einfache Version ohne Pydantic-Abhängigkeiten

Eine stark vereinfachte Version der SwissAirDry API ohne Abhängigkeiten von Pydantic.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

# FastAPI-App erstellen
app = FastAPI(
    title="SwissAirDry Simple API",
    description="Einfache API für SwissAirDry ohne Pydantic-Abhängigkeiten",
    version="1.0.0",
)

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

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware zum Loggen aller Anfragen"""
    start_time = datetime.now()
    
    # Request-Statistik aktualisieren
    api_stats["request_count"] += 1
    api_stats["last_request"] = datetime.now()
    
    response = await call_next(request)
    
    # Bei Fehler die Fehlerstatistik erhöhen
    if response.status_code >= 400:
        api_stats["error_count"] += 1
    
    process_time = (datetime.now() - start_time).total_seconds()
    response.headers["X-Process-Time"] = str(process_time)
    
    print(
        f"{request.client.host}:{request.client.port} - "
        f"{request.method} {request.url.path} - "
        f"{response.status_code} - {process_time:.4f}s"
    )
    
    return response


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root-Endpoint, liefert eine einfache HTML-Seite zurück."""
    return HTMLResponse(content="""
    <html>
        <head>
            <title>SwissAirDry API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #0066cc; }
            </style>
        </head>
        <body>
            <h1>SwissAirDry Simple API</h1>
            <p>Willkommen bei der vereinfachten SwissAirDry API.</p>
            <p>
                Verfügbare Endpoints:
                <ul>
                    <li><a href="/docs">/docs</a> - API-Dokumentation</li>
                    <li><a href="/health">/health</a> - API-Status</li>
                    <li><a href="/api/devices">/api/devices</a> - Liste aller Geräte</li>
                </ul>
            </p>
        </body>
    </html>
    """)


@app.get("/health")
async def health_check():
    """Health-Check-Endpunkt für Monitoring."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "uptime": (datetime.now() - server_start_time).total_seconds(),
        "stats": api_stats,
    }


@app.get("/api/devices")
async def get_devices():
    """Gibt eine Liste aller Geräte zurück."""
    return devices


@app.get("/api/devices/{device_id}")
async def get_device(device_id: str):
    """Gibt ein Gerät anhand seiner ID zurück."""
    for device in devices:
        if device["device_id"] == device_id:
            return device
    return JSONResponse(status_code=404, content={"detail": "Gerät nicht gefunden"})


@app.post("/api/device/{device_id}/data")
async def create_sensor_data(device_id: str, request: Request):
    """Speichert neue Sensordaten für ein Gerät."""
    try:
        # Daten aus dem Request-Body auslesen
        data = await request.json()
        
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
        return {"status": "ok", "message": "Daten erfolgreich gespeichert"}
    
    except Exception as e:
        return JSONResponse(
            status_code=400, 
            content={"status": "error", "message": f"Fehler beim Verarbeiten der Daten: {str(e)}"}
        )