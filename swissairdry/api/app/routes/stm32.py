"""
SwissAirDry - STM32 Geräte-Routen
---------------------------------

Spezielle API-Endpunkte für STM32-Geräte mit optimierter Datenverarbeitung.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta

from swissairdry.api.app.device_manager import DeviceManager, DeviceType, CommunicationType
from swissairdry.utils import parse_stm32_data, format_stm32_response
from swissairdry.api.app.schemas.device import STM32DeviceRegister, STM32DeviceData

# Router erstellen
router = APIRouter(
    prefix="/api/stm32",
    tags=["stm32"],
    responses={404: {"description": "Not found"}},
)

# Globale Device Manager Instanz verwenden
from swissairdry.api.app.routes.devices import device_manager


@router.post("/register", status_code=201)
def register_stm32_device(device: STM32DeviceRegister):
    """
    Registriert ein neues STM32-Gerät im System.
    Diese Route ist für einfache Clients und speziell für STM32-Geräte optimiert.
    
    Die Registrierung erfolgt nur im Device Manager, nicht in der Datenbank,
    um den Ressourcenverbrauch zu minimieren.
    """
    # Gerät im Device Manager registrieren
    success = device_manager.register_device(
        device_id=device.device_id,
        device_type=DeviceType.STM32,
        communication_type=CommunicationType.MQTT if device.communication_type == "mqtt" else 
                          CommunicationType.HTTP if device.communication_type == "http" else 
                          CommunicationType.BLE,
        name=device.name,
        location=device.location or "Unknown",
        metadata=device.metadata or {}
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Fehler bei der Registrierung des STM32-Geräts")
    
    return {
        "success": True,
        "device_id": device.device_id,
        "message": f"STM32-Gerät {device.name} erfolgreich registriert"
    }


@router.post("/{device_id}/data")
def update_stm32_data(
    device_id: str = Path(..., description="Die ID des STM32-Geräts"),
    data: STM32DeviceData = Body(..., description="Die zu aktualisierenden Daten")
):
    """
    Aktualisiert die Daten eines STM32-Geräts.
    Optimiert für STM32-Geräte mit eingeschränkten Ressourcen.
    
    Die Daten werden im kompakten STM32-Format übertragen und dann in das
    standardisierte Format umgewandelt.
    """
    # STM32-Daten in standardisiertes Format umwandeln
    parsed_data = parse_stm32_data(data.dict())
    
    # Daten an den Device Manager senden
    success = device_manager.update_device_data(
        device_id=device_id,
        data=parsed_data,
        source=CommunicationType.MQTT
    )
    
    if not success:
        raise HTTPException(status_code=404, detail=f"STM32-Gerät mit ID {device_id} nicht gefunden")
    
    return {
        "success": True,
        "device_id": device_id,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/{device_id}/status")
def get_stm32_status(device_id: str = Path(..., description="Die ID des STM32-Geräts")):
    """
    Gibt den aktuellen Status eines STM32-Geräts zurück.
    Das Antwortformat ist für STM32-Geräte optimiert.
    """
    device = device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"STM32-Gerät mit ID {device_id} nicht gefunden")
    
    # Antwort für STM32-Geräte optimieren
    response = {
        "id": device_id,
        "status": device.get("status", "unknown"),
        "last_seen": device.get("last_seen", 0),
        "data": device.get("data", {})
    }
    
    return format_stm32_response(response)


@router.post("/{device_id}/command")
def send_stm32_command(
    device_id: str = Path(..., description="Die ID des STM32-Geräts"),
    command: str = Query(..., description="Der zu sendende Befehl"),
    params: Optional[Dict[str, Any]] = Body({}, description="Die Parameter des Befehls")
):
    """
    Sendet einen Befehl an ein STM32-Gerät.
    Die Befehle sind für STM32-Geräte optimiert und ressourcenschonend.
    """
    success = device_manager.send_command(
        device_id=device_id,
        command=command,
        params=params
    )
    
    if not success:
        raise HTTPException(status_code=404, detail=f"STM32-Gerät mit ID {device_id} nicht gefunden oder Befehl konnte nicht gesendet werden")
    
    return {
        "success": True,
        "device_id": device_id,
        "command": command,
        "timestamp": datetime.now().isoformat()
    }