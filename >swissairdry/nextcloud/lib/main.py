#!/usr/bin/env python3
"""
SwissAirDry Nextcloud ExApp - Hauptmodul

Dieses Modul implementiert die Hauptfunktionalität der SwissAirDry Nextcloud ExApp.
Die ExApp dient als Brücke zwischen der Nextcloud-Oberfläche und dem SwissAirDry API-Server.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import uuid

import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from pydantic import BaseModel

# Nextcloud Python API
from nc_py_api import NextcloudApp, UserInfo
from nc_py_api.ex_app import (
    AppAPIAuthMiddleware,
    app_api_auth,
    ExAppComponent,
    EnabledInfo,
    Capabilities,
)

# Konfiguration
PORT = int(os.environ.get("PORT", 8000))
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
API_URL = os.environ.get("API_URL", "https://api.swissairdry.ch")
MQTT_BROKER = os.environ.get("MQTT_BROKER", "mqtt.swissairdry.ch")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 1883))

# Logging konfigurieren
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("swissairdry_exapp")

# FastAPI-App initialisieren
app = FastAPI(
    title="SwissAirDry ExApp",
    description="Nextcloud-Integration für SwissAirDry",
    version="2.1.0",
)

# Middlewares
app.add_middleware(
    AppAPIAuthMiddleware, 
    exempt_paths=["/health", "/api/v1/public"]
)

# Statische Dateien und Templates
try:
    app.mount("/static", StaticFiles(directory="../static"), name="static")
    templates = Jinja2Templates(directory="../templates")
except:
    # Fallback für Docker-Container
    app.mount("/static", StaticFiles(directory="/app/static"), name="static")
    templates = Jinja2Templates(directory="/app/templates")

# Nextcloud-App initialisieren
nc_app = NextcloudApp()


# Modelle
class APICredentials(BaseModel):
    """API-Zugangsdaten Modell"""
    api_url: str
    api_key: str


class MQTTSettings(BaseModel):
    """MQTT-Einstellungen Modell"""
    broker: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    topic_prefix: Optional[str] = "swissairdry/"


class UserSettings(BaseModel):
    """Benutzereinstellungen Modell"""
    api_credentials: APICredentials
    mqtt_settings: MQTTSettings
    theme: Optional[str] = "light"
    language: Optional[str] = "de"
    notifications_enabled: Optional[bool] = True


# Hilfsfunktionen
def get_user_settings(user_id: str) -> UserSettings:
    """Lädt Benutzereinstellungen aus Nextcloud"""
    try:
        # Versuche, Einstellungen aus Nextcloud zu laden
        settings_json = nc_app.user_settings.get_settings("swissairdry_settings", user_id=user_id)
        if settings_json:
            return UserSettings.parse_raw(settings_json)
    except Exception as e:
        logger.warning(f"Fehler beim Laden der Benutzereinstellungen: {e}")
    
    # Standardeinstellungen verwenden
    return UserSettings(
        api_credentials=APICredentials(
            api_url=API_URL,
            api_key="",
        ),
        mqtt_settings=MQTTSettings(
            broker=MQTT_BROKER,
            port=MQTT_PORT,
        )
    )


def save_user_settings(user_id: str, settings: UserSettings) -> bool:
    """Speichert Benutzereinstellungen in Nextcloud"""
    try:
        nc_app.user_settings.set_settings(
            "swissairdry_settings", 
            settings.json(), 
            user_id=user_id
        )
        return True
    except Exception as e:
        logger.error(f"Fehler beim Speichern der Benutzereinstellungen: {e}")
        return False


# API-Routen
@app.get("/health")
async def health_check():
    """Gesundheitscheck-Endpunkt für Container-Prüfung"""
    return {"status": "ok", "version": "2.1.0"}


@app.get("/enabled", response_model=EnabledInfo)
async def app_enabled():
    """Gibt zurück, ob die App aktiviert ist"""
    return EnabledInfo(enabled=True, error=None)


@app.get("/capabilities", response_model=Capabilities)
async def app_capabilities():
    """Gibt die Funktionen der App zurück"""
    return Capabilities(
        components=[
            ExAppComponent(
                name="swissairdry",
                display_name="SwissAirDry",
                description="Verwaltung und Überwachung von Trocknungsgeräten",
                icon_url="static/icon.svg",
                navigation_entry_url="index.html",
            )
        ]
    )


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, user_info: UserInfo = Depends(app_api_auth)):
    """Hauptseite der App"""
    # Benutzereinstellungen laden
    settings = get_user_settings(user_info.id)
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user": user_info,
            "settings": settings,
            "api_url": settings.api_credentials.api_url
        }
    )


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, user_info: UserInfo = Depends(app_api_auth)):
    """Einstellungsseite der App"""
    # Benutzereinstellungen laden
    settings = get_user_settings(user_info.id)
    
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "user": user_info,
            "settings": settings,
        }
    )


@app.post("/api/settings")
async def update_settings(
    settings: UserSettings,
    user_info: UserInfo = Depends(app_api_auth)
):
    """Aktualisiert die Benutzereinstellungen"""
    success = save_user_settings(user_info.id, settings)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Fehler beim Speichern der Einstellungen"
        )
    
    return {"status": "success"}


@app.get("/api/proxy/{path:path}")
async def proxy_api(
    path: str,
    request: Request,
    user_info: UserInfo = Depends(app_api_auth)
):
    """Proxy-Endpunkt zur Weiterleitung an die SwissAirDry API"""
    import requests
    
    # Benutzereinstellungen laden
    settings = get_user_settings(user_info.id)
    
    # API-Zugangsdaten überprüfen
    if not settings.api_credentials.api_key:
        raise HTTPException(
            status_code=401,
            detail="API-Schlüssel nicht konfiguriert"
        )
    
    # Header und Query-Parameter kopieren
    headers = dict(request.headers)
    headers["X-API-Key"] = settings.api_credentials.api_key
    
    # Cookies und User-Agent entfernen
    headers.pop("cookie", None)
    headers.pop("user-agent", None)
    
    # URL zusammensetzen
    url = f"{settings.api_credentials.api_url}/{path}"
    
    try:
        # Request an die API weiterleiten
        response = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            params=dict(request.query_params),
            json=await request.json() if request.method in ["POST", "PUT"] else None,
            timeout=10,
        )
        
        # Antwort zurücksenden
        return JSONResponse(
            content=response.json() if response.content else {},
            status_code=response.status_code,
        )
    except Exception as e:
        logger.error(f"Fehler bei API-Proxy-Anfrage: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Fehler bei der Kommunikation mit der API: {str(e)}"
        )


if __name__ == "__main__":
    # App starten, wenn direkt ausgeführt
    uvicorn.run(app, host="0.0.0.0", port=PORT)