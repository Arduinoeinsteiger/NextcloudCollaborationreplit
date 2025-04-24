#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SwissAirDry API - Deck BLE Standort API Routes
----------------------------------------------

Diese Datei enthält die API-Routen für die Integration von BLE-Standortdaten
mit der Nextcloud Deck App.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ..dependencies import get_deck_location_integration

router = APIRouter(
    prefix="/api/deck/location",
    tags=["deck-location"],
    responses={404: {"description": "Not found"}},
)

# Logger konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("swissairdry_api")


# Datenmodelle für die API-Anfragen und -Antworten

class LocationUpdate(BaseModel):
    """Modell für Standortaktualisierungen"""
    device_id: str
    device_name: str
    location_name: str
    location_description: Optional[str] = None
    rssi: Optional[int] = None
    coordinates: Optional[Dict[str, float]] = None


class DeviceOfflineUpdate(BaseModel):
    """Modell für Offline-Statusaktualisierungen"""
    device_id: str
    device_name: str
    last_seen: Optional[datetime] = None


class ApiResponse(BaseModel):
    """Standard-API-Antwortmodell"""
    success: bool
    message: str
    data: Optional[Any] = None


# API-Routen für die BLE-Standortintegration

@router.post("/update", response_model=ApiResponse)
async def update_device_location(
    location_data: LocationUpdate,
    deck_location = Depends(get_deck_location_integration)
):
    """
    Aktualisiere den Standort eines Geräts in der Nextcloud Deck-Integration

    Args:
        location_data: Standortdaten des Geräts

    Returns:
        ApiResponse: Bestätigung der Aktualisierung
    """
    try:
        # Standortinformationen in Deck aktualisieren
        deck_location.update_device_location(
            device_id=location_data.device_id,
            device_name=location_data.device_name,
            new_location=location_data.location_name,
            location_description=location_data.location_description,
            rssi=location_data.rssi,
            coordinates=location_data.coordinates
        )
        
        return ApiResponse(
            success=True,
            message=f"Standort für {location_data.device_name} auf {location_data.location_name} aktualisiert",
            data={"device_id": location_data.device_id, "updated_at": datetime.now().isoformat()}
        )
    
    except Exception as e:
        logger.error(f"Fehler bei der Standortaktualisierung: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler bei der Standortaktualisierung: {str(e)}")


@router.post("/offline", response_model=ApiResponse)
async def mark_device_offline(
    offline_data: DeviceOfflineUpdate,
    deck_location = Depends(get_deck_location_integration)
):
    """
    Markiere ein Gerät als offline in der Nextcloud Deck-Integration

    Args:
        offline_data: Informationen zum Offline-Status des Geräts

    Returns:
        ApiResponse: Bestätigung der Aktualisierung
    """
    try:
        # Gerät als offline markieren
        deck_location.mark_device_offline(
            device_id=offline_data.device_id,
            device_name=offline_data.device_name,
            last_seen=offline_data.last_seen
        )
        
        return ApiResponse(
            success=True,
            message=f"Gerät {offline_data.device_name} als offline markiert",
            data={"device_id": offline_data.device_id, "updated_at": datetime.now().isoformat()}
        )
    
    except Exception as e:
        logger.error(f"Fehler beim Markieren des Geräts als offline: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Markieren als offline: {str(e)}")