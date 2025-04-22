"""
SwissAirDry API - Dokumentationsrouten

Dieses Modul bietet Funktionen zum Bereitstellen der API-Dokumentation über HTTP.

@author Swiss Air Dry Team <info@swissairdry.com>
@copyright 2023-2025 Swiss Air Dry Team
"""

import os
import importlib.resources as pkg_resources
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

# Router für Dokumentationsrouten erstellen
docs_router = APIRouter(prefix="/api/docs", tags=["Dokumentation"])

# Pfad zum Dokumentationsverzeichnis bestimmen
docs_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(docs_dir, "templates")

# Prüfen, ob Templates-Verzeichnis existiert
if os.path.exists(templates_dir):
    templates = Jinja2Templates(directory=templates_dir)
else:
    templates = None
    print(f"Warnung: Verzeichnis {templates_dir} nicht gefunden")


@docs_router.get("/", response_class=HTMLResponse)
async def api_docs(request: Request):
    """Zeigt die API-Dokumentations-Startseite an."""
    if not templates:
        raise HTTPException(status_code=500, detail="Templates-Verzeichnis nicht gefunden")
    
    return templates.TemplateResponse("api_docs.html", {"request": request})


@docs_router.get("/API_DOCUMENTATION.md", response_class=FileResponse)
async def api_documentation_md():
    """Liefert die Markdown-API-Dokumentation."""
    file_path = os.path.join(docs_dir, "API_DOCUMENTATION.md")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="API-Dokumentationsdatei nicht gefunden")
    
    return FileResponse(file_path)


@docs_router.get("/docs_redirect")
async def docs_redirect():
    """Leitet zur Swagger-UI-Dokumentation weiter."""
    return RedirectResponse(url="/docs")


@docs_router.get("/openapi_redirect")
async def openapi_redirect():
    """Leitet zur OpenAPI-Spezifikation weiter."""
    return RedirectResponse(url="/openapi.json")


# Funktion zum Registrieren der Dokumentationsrouten bei einer FastAPI-App
def register_docs_routes(app):
    """
    Registriert die Dokumentationsrouten bei einer FastAPI-App.
    
    Args:
        app: FastAPI-App-Instanz
    """
    app.include_router(docs_router)


# Beispiel zur Integration in die FastAPI-App
"""
from fastapi import FastAPI
from swissairdry.api.docs.serve_docs import register_docs_routes

app = FastAPI()

# Dokumentationsrouten registrieren
register_docs_routes(app)
"""