#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SwissAirDry ExApp Integration API Routes
----------------------------------------

Diese Datei enthält alle Routen für die Integration mit der SwissAirDry ExApp.
Die ExApp ersetzt die alte Deck-Integration und bietet erweiterte Funktionen
für die Projektmanagement- und Auftragsabwicklung.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

import requests
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from pydantic import BaseModel, ConfigDict

# Router erstellen
router = APIRouter(
    prefix="/exapp",
    tags=["exapp"],
    responses={404: {"description": "Not found"}},
)

# Logger konfigurieren
logger = logging.getLogger("swissairdry_api")

# Umgebungsvariablen
EXAPP_URL = os.environ.get("EXAPP_URL", "http://localhost:8080")
EXAPP_DAEMON_URL = os.environ.get("EXAPP_DAEMON_URL", "http://localhost:8081")


# Datenmodelle
class ExAppStatusResponse(BaseModel):
    """Antwortmodell für ExApp-Status"""
    model_config = ConfigDict(from_attributes=True)
    
    status: str
    connected: bool
    exapp_url: str
    daemon_url: str
    last_sync: Optional[str] = None
    version: Optional[str] = None
    message: Optional[str] = None


# Integration-Check-Funktionen
def check_exapp_api() -> Dict[str, Any]:
    """
    Überprüft die Verbindung zur ExApp API
    
    Returns:
        Dict: Status-Informationen
    """
    try:
        response = requests.get(f"{EXAPP_URL}/api/status", timeout=5)
        if response.status_code == 200:
            return {
                "connected": True,
                "status": "ok",
                "message": "ExApp API ist erreichbar"
            }
        else:
            return {
                "connected": False,
                "status": "error",
                "message": f"ExApp API antwortet mit Status {response.status_code}"
            }
    except Exception as e:
        logger.warning(f"Fehler bei Verbindung zur ExApp API: {str(e)}")
        return {
            "connected": False,
            "status": "error",
            "message": f"Verbindungsfehler: {str(e)}"
        }


def check_exapp_daemon() -> Dict[str, Any]:
    """
    Überprüft die Verbindung zum ExApp Daemon
    
    Returns:
        Dict: Status-Informationen
    """
    try:
        response = requests.get(f"{EXAPP_DAEMON_URL}/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "connected": True,
                "status": "ok",
                "message": "ExApp Daemon ist erreichbar",
                "last_sync": data.get("last_sync"),
                "version": data.get("version")
            }
        else:
            return {
                "connected": False,
                "status": "error",
                "message": f"ExApp Daemon antwortet mit Status {response.status_code}"
            }
    except Exception as e:
        logger.warning(f"Fehler bei Verbindung zum ExApp Daemon: {str(e)}")
        return {
            "connected": False,
            "status": "error",
            "message": f"Verbindungsfehler: {str(e)}"
        }


# API-Endpunkte
@router.get("/status", response_model=ExAppStatusResponse)
async def get_exapp_status():
    """
    Prüft den Status der ExApp-Integration
    
    Returns:
        ExAppStatusResponse: Status-Informationen zur ExApp-Integration
    """
    # ExApp API prüfen
    exapp_status = check_exapp_api()
    
    # ExApp Daemon prüfen
    daemon_status = check_exapp_daemon()
    
    # Gesamtstatus ermitteln
    if exapp_status["connected"] and daemon_status["connected"]:
        overall_status = "ok"
    elif not exapp_status["connected"] and not daemon_status["connected"]:
        overall_status = "offline"
    else:
        overall_status = "partial"
    
    # Detaillierten Status zurückgeben
    return ExAppStatusResponse(
        status=overall_status,
        connected=exapp_status["connected"] or daemon_status["connected"],
        exapp_url=EXAPP_URL,
        daemon_url=EXAPP_DAEMON_URL,
        last_sync=daemon_status.get("last_sync"),
        version=daemon_status.get("version"),
        message=f"ExApp: {exapp_status['message']}; Daemon: {daemon_status['message']}"
    )