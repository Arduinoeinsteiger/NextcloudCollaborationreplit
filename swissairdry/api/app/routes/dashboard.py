#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SwissAirDry Dashboard API Routes
--------------------------------

Diese Datei enthält alle API-Routen für das Dashboard mit anpassbaren
Widgets und Drag-and-Drop-Funktionalität.

Das Dashboard ermöglicht:
- Anzeige von Geräte- und Systemstatus
- Diagramme für Temperatur, Luftfeuchtigkeit und Energieverbrauch
- Aufgaben-Listen aus der ExApp
- Anpassbare Anordnung durch Drag-and-Drop
- Speichern individueller Dashboard-Konfigurationen
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import random  # Nur für Beispieldaten, in der Produktion entfernen

from fastapi import APIRouter, Depends, HTTPException, Request, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict

from swissairdry.api.app import database
from swissairdry.api.app.routes import exapp
from sqlalchemy.orm import Session

# Router erstellen
router = APIRouter(
    prefix="/api/dashboard",
    tags=["dashboard"],
    responses={404: {"description": "Not found"}},
)

# Logger konfigurieren
logger = logging.getLogger("swissairdry_api")

# Pfad zu den Dashboard-Konfigurationsdateien
DASHBOARD_CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "dashboard")
os.makedirs(DASHBOARD_CONFIG_DIR, exist_ok=True)

# Templates-Verzeichnis für HTML-Responses
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)


# Datenmodelle
class DashboardWidget(BaseModel):
    """Konfiguration eines Dashboard-Widgets"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    position: int
    visible: bool = True
    size: Optional[str] = None
    refresh_interval: Optional[int] = None
    settings: Optional[Dict[str, Any]] = None


class DashboardConfig(BaseModel):
    """Konfiguration des Dashboards"""
    model_config = ConfigDict(from_attributes=True)
    
    widgets: List[DashboardWidget]
    layout: str = "grid"
    theme: str = "light"
    auto_refresh: bool = True
    refresh_interval: int = 60


# Beispiel-Konfiguration für neue Benutzer
DEFAULT_CONFIG = DashboardConfig(
    widgets=[
        DashboardWidget(id="device-status", position=0, visible=True),
        DashboardWidget(id="temperature-chart", position=1, visible=True),
        DashboardWidget(id="system-status", position=2, visible=True)
    ],
    layout="grid",
    theme="light",
    auto_refresh=True,
    refresh_interval=60
)


# Hilfsfunktionen
def get_user_config_path(user_id: str = "default") -> str:
    """
    Gibt den Pfad zur Konfigurationsdatei eines Benutzers zurück
    
    Args:
        user_id: ID des Benutzers (default für nicht-angemeldete Benutzer)
        
    Returns:
        str: Pfad zur Konfigurationsdatei
    """
    return os.path.join(DASHBOARD_CONFIG_DIR, f"{user_id}.json")


def load_user_config(user_id: str = "default") -> DashboardConfig:
    """
    Lädt die Dashboard-Konfiguration eines Benutzers
    
    Args:
        user_id: ID des Benutzers (default für nicht-angemeldete Benutzer)
        
    Returns:
        DashboardConfig: Dashboard-Konfiguration
    """
    config_path = get_user_config_path(user_id)
    
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            
            return DashboardConfig(**config_data)
        except Exception as e:
            logger.error(f"Fehler beim Laden der Dashboard-Konfiguration: {e}")
            return DEFAULT_CONFIG
    else:
        # Neue Konfiguration für den Benutzer erstellen
        save_user_config(DEFAULT_CONFIG, user_id)
        return DEFAULT_CONFIG


def save_user_config(config: DashboardConfig, user_id: str = "default") -> bool:
    """
    Speichert die Dashboard-Konfiguration eines Benutzers
    
    Args:
        config: Dashboard-Konfiguration
        user_id: ID des Benutzers (default für nicht-angemeldete Benutzer)
        
    Returns:
        bool: True, wenn das Speichern erfolgreich war
    """
    config_path = get_user_config_path(user_id)
    
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config.model_dump(), f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Fehler beim Speichern der Dashboard-Konfiguration: {e}")
        return False


def get_current_user_id(request: Request) -> str:
    """
    Gibt die ID des aktuellen Benutzers zurück
    
    In einer richtigen Implementierung würde diese Funktion die User-ID
    aus der Session oder dem Token lesen.
    
    Args:
        request: FastAPI Request-Objekt
        
    Returns:
        str: Benutzer-ID oder "default" für nicht-angemeldete Benutzer
    """
    # TODO: Implementierung der Benutzerauthentifizierung
    # In einer realen Anwendung würde hier die Benutzer-ID aus dem Token extrahiert werden
    return "default"


# API-Endpunkte
@router.get("/config", response_model=DashboardConfig)
async def get_dashboard_config(request: Request):
    """
    Gibt die Dashboard-Konfiguration des aktuellen Benutzers zurück
    
    Returns:
        DashboardConfig: Dashboard-Konfiguration
    """
    user_id = get_current_user_id(request)
    return load_user_config(user_id)


@router.post("/config", response_model=Dict[str, Any])
async def save_dashboard_config(
    request: Request,
    config: DashboardConfig = Body(...)
):
    """
    Speichert die Dashboard-Konfiguration des aktuellen Benutzers
    
    Args:
        config: Neue Dashboard-Konfiguration
        
    Returns:
        Dict: Status der Operation
    """
    user_id = get_current_user_id(request)
    success = save_user_config(config, user_id)
    
    if success:
        return {
            "status": "success",
            "message": "Konfiguration erfolgreich gespeichert"
        }
    else:
        raise HTTPException(
            status_code=500,
            detail="Fehler beim Speichern der Konfiguration"
        )


@router.get("/widget/{widget_id}/data")
async def get_widget_data(widget_id: str, request: Request):
    """
    Gibt die Daten für ein Widget zurück
    
    Args:
        widget_id: ID des Widgets
        
    Returns:
        Dict: Widget-Daten
    """
    # In einer realen Anwendung würden hier Daten aus der Datenbank oder anderen Quellen geladen
    
    # Beispieldaten für verschiedene Widget-Typen
    if widget_id == "device-status":
        # Gerätestatus-Widget
        return {
            "devices": [
                {"id": "device-1", "name": "Trockner 1", "status": "online", "last_active": datetime.now().isoformat()},
                {"id": "device-2", "name": "Trockner 2", "status": "offline", "last_active": (datetime.now() - timedelta(days=1)).isoformat()},
                {"id": "device-3", "name": "Trockner 3", "status": "warning", "last_active": datetime.now().isoformat()},
                {"id": "device-4", "name": "Trockner 4", "status": "online", "last_active": datetime.now().isoformat()},
                {"id": "device-5", "name": "Trockner 5", "status": "online", "last_active": datetime.now().isoformat()}
            ]
        }
    
    elif widget_id == "system-status":
        # Systemstatus-Widget
        return {
            "api": True,
            "mqtt": True,
            "exapp": False,  # ExApp ist noch nicht gestartet
            "database": True,
            "uptime": "3 Tage, 5 Stunden",
            "last_update": datetime.now().isoformat()
        }
    
    elif widget_id == "temperature-chart":
        # Temperatur-Chart
        # In einer realen Anwendung würden hier Daten aus der Datenbank geladen
        return {
            "labels": [(datetime.now() - timedelta(hours=i)).strftime("%H:%M") for i in range(24, 0, -1)],
            "datasets": [
                {
                    "label": "Trockner 1",
                    "data": [random.uniform(20, 25) for _ in range(24)],
                    "borderColor": "rgba(255, 99, 132, 1)",
                    "backgroundColor": "rgba(255, 99, 132, 0.2)",
                    "fill": True
                },
                {
                    "label": "Trockner 2",
                    "data": [random.uniform(19, 24) for _ in range(24)],
                    "borderColor": "rgba(54, 162, 235, 1)",
                    "backgroundColor": "rgba(54, 162, 235, 0.2)",
                    "fill": True
                }
            ]
        }
    
    elif widget_id == "humidity-chart":
        # Feuchtigkeits-Chart
        return {
            "labels": [(datetime.now() - timedelta(hours=i)).strftime("%H:%M") for i in range(24, 0, -1)],
            "datasets": [
                {
                    "label": "Trockner 1",
                    "data": [random.uniform(40, 60) for _ in range(24)],
                    "borderColor": "rgba(75, 192, 192, 1)",
                    "backgroundColor": "rgba(75, 192, 192, 0.2)",
                    "fill": True
                },
                {
                    "label": "Trockner 2",
                    "data": [random.uniform(35, 55) for _ in range(24)],
                    "borderColor": "rgba(153, 102, 255, 1)",
                    "backgroundColor": "rgba(153, 102, 255, 0.2)",
                    "fill": True
                }
            ]
        }
    
    elif widget_id == "energy-chart":
        # Energieverbrauchs-Chart
        return {
            "labels": [(datetime.now() - timedelta(days=i)).strftime("%d.%m") for i in range(7, 0, -1)],
            "datasets": [
                {
                    "label": "Energieverbrauch (kWh)",
                    "data": [random.uniform(15, 25) for _ in range(7)],
                    "borderColor": "rgba(255, 159, 64, 1)",
                    "backgroundColor": "rgba(255, 159, 64, 0.2)",
                    "borderWidth": 2,
                    "fill": True
                }
            ]
        }
    
    elif widget_id == "exapp-tasks":
        # ExApp-Aufgaben
        # In einer realen Anwendung würden hier Daten aus der ExApp geladen
        return {
            "tasks": [
                {"id": 1, "title": "Trockner 2 warten", "priority": "high", "dueDate": (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y")},
                {"id": 2, "title": "Filter bestellen", "priority": "medium", "dueDate": (datetime.now() + timedelta(days=3)).strftime("%d.%m.%Y")},
                {"id": 3, "title": "Protokolle überprüfen", "priority": "low", "dueDate": (datetime.now() + timedelta(days=5)).strftime("%d.%m.%Y")},
                {"id": 4, "title": "Kundenbesuch vorbereiten", "priority": "high", "dueDate": datetime.now().strftime("%d.%m.%Y")}
            ]
        }
    
    # Widget nicht gefunden
    raise HTTPException(
        status_code=404,
        detail=f"Widget '{widget_id}' nicht gefunden"
    )


# HTML-Routen
@router.get("/", response_class=HTMLResponse)
async def get_dashboard_page(request: Request):
    """
    Gibt die Dashboard-Seite zurück
    
    Returns:
        HTMLResponse: Dashboard-Seite
    """
    return templates.TemplateResponse("dashboard.html", {"request": request})