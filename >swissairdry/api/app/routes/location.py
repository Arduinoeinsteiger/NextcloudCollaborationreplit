"""
SwissAirDry API - Standortverwaltung und BLE-Scanning
--------------------------------------------------

Diese Datei enthält API-Routen für die Verwaltung von Standorten und BLE-basierte Geräteortung.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel

import ble_scanner

# API-Router erstellen
router = APIRouter(
    prefix="/api/locations",
    tags=["locations"],
    responses={404: {"description": "Not found"}},
)

# Datenmodelle
class LocationBase(BaseModel):
    name: str
    description: Optional[str] = ""

class LocationCreate(LocationBase):
    location_id: str

class LocationUpdate(LocationBase):
    pass

class LocationResponse(LocationBase):
    location_id: str

class DeviceLocationResponse(BaseModel):
    device_id: str
    location_id: str
    location_name: Optional[str] = None
    rssi: Optional[int] = None
    last_seen: Optional[str] = None

# Dependency für BLE-Manager
def get_ble_manager():
    """Erstellt und gibt eine Instanz des BLE-Managers zurück"""
    from run2 import mqtt_client  # import hier, um Zirkelimports zu vermeiden
    
    # Es wird nur eine einzige Instanz des BLE-Managers erstellt und wiederverwendet
    if not hasattr(get_ble_manager, "manager"):
        get_ble_manager.manager = ble_scanner.BLEManager(mqtt_client)
    
    return get_ble_manager.manager

# API-Endpunkte

@router.post("/scan/start", status_code=status.HTTP_202_ACCEPTED)
async def start_ble_scan(manager: ble_scanner.BLEManager = Depends(get_ble_manager)):
    """Startet den BLE-Scan im Hintergrund"""
    await manager.start_background_scan()
    return {"message": "BLE-Scan gestartet"}

@router.post("/scan/stop", status_code=status.HTTP_202_ACCEPTED)
async def stop_ble_scan(manager: ble_scanner.BLEManager = Depends(get_ble_manager)):
    """Stoppt den BLE-Scan im Hintergrund"""
    await manager.stop_background_scan()
    return {"message": "BLE-Scan gestoppt"}

@router.get("/", response_model=Dict[str, LocationResponse])
async def get_locations(manager: ble_scanner.BLEManager = Depends(get_ble_manager)):
    """Gibt alle konfigurierten Standorte zurück"""
    locations = manager.get_locations()
    result = {}
    
    for location_id, data in locations.items():
        result[location_id] = LocationResponse(
            location_id=location_id,
            name=data.get("name", ""),
            description=data.get("description", "")
        )
    
    return result

@router.post("/", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    location: LocationCreate, 
    manager: ble_scanner.BLEManager = Depends(get_ble_manager)
):
    """Erstellt einen neuen Standort"""
    success = manager.add_location(
        location.location_id, 
        location.name, 
        location.description
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Standort mit ID {location.location_id} existiert bereits"
        )
    
    return LocationResponse(
        location_id=location.location_id,
        name=location.name,
        description=location.description
    )

@router.put("/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: str,
    location: LocationUpdate,
    manager: ble_scanner.BLEManager = Depends(get_ble_manager)
):
    """Aktualisiert einen vorhandenen Standort"""
    success = manager.update_location(
        location_id,
        location.name,
        location.description
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Standort mit ID {location_id} nicht gefunden"
        )
    
    locations = manager.get_locations()
    location_data = locations.get(location_id)
    
    return LocationResponse(
        location_id=location_id,
        name=location_data.get("name", ""),
        description=location_data.get("description", "")
    )

@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: str,
    manager: ble_scanner.BLEManager = Depends(get_ble_manager)
):
    """Löscht einen Standort"""
    success = manager.remove_location(location_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Standort mit ID {location_id} nicht gefunden"
        )
    
    return None

@router.get("/devices", response_model=List[DeviceLocationResponse])
async def get_device_locations(
    manager: ble_scanner.BLEManager = Depends(get_ble_manager)
):
    """Gibt die Standorte aller entdeckten Geräte zurück"""
    device_locations = manager.get_device_locations()
    discovered_devices = manager.get_discovered_devices()
    locations = manager.get_locations()
    
    result = []
    
    for device_id, location_id in device_locations.items():
        location_name = ""
        if location_id in locations:
            location_name = locations[location_id].get("name", "")
        
        device_data = {}
        if device_id in discovered_devices:
            device_data = discovered_devices[device_id]
        
        result.append(DeviceLocationResponse(
            device_id=device_id,
            location_id=location_id,
            location_name=location_name,
            rssi=device_data.get("rssi"),
            last_seen=device_data.get("last_seen")
        ))
    
    return result

@router.get("/devices/scan", response_model=Dict[str, Any])
async def get_discovered_devices(
    manager: ble_scanner.BLEManager = Depends(get_ble_manager)
):
    """Gibt alle durch BLE-Scan entdeckten Geräte zurück"""
    return manager.get_discovered_devices()

@router.get("/device/{device_id}", response_model=DeviceLocationResponse)
async def get_device_location(
    device_id: str,
    manager: ble_scanner.BLEManager = Depends(get_ble_manager)
):
    """Gibt den Standort eines bestimmten Geräts zurück"""
    device_locations = manager.get_device_locations()
    discovered_devices = manager.get_discovered_devices()
    
    if device_id not in device_locations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gerät mit ID {device_id} nicht gefunden oder Standort unbekannt"
        )
    
    location_id = device_locations[device_id]
    locations = manager.get_locations()
    location_name = ""
    
    if location_id in locations:
        location_name = locations[location_id].get("name", "")
    
    device_data = {}
    if device_id in discovered_devices:
        device_data = discovered_devices[device_id]
    
    return DeviceLocationResponse(
        device_id=device_id,
        location_id=location_id,
        location_name=location_name,
        rssi=device_data.get("rssi"),
        last_seen=device_data.get("last_seen")
    )

@router.put("/device/{device_id}", response_model=DeviceLocationResponse)
async def set_device_location(
    device_id: str,
    location_id: str,
    manager: ble_scanner.BLEManager = Depends(get_ble_manager)
):
    """Setzt den Standort eines Geräts manuell"""
    # Prüfen, ob der Standort existiert
    locations = manager.get_locations()
    if location_id not in locations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Standort mit ID {location_id} nicht gefunden"
        )
    
    # Standort manuell setzen
    ble_scanner.set_device_location(device_id, location_id)
    
    location_name = locations[location_id].get("name", "")
    
    return DeviceLocationResponse(
        device_id=device_id,
        location_id=location_id,
        location_name=location_name
    )