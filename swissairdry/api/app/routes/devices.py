"""
SwissAirDry - Geräte-Routen
---------------------------

API-Endpunkte zur Verwaltung von Geräten, einschließlich ESP8266, ESP32 und STM32.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from swissairdry.api.app.database import get_db
from swissairdry.api.app.device_manager import DeviceManager, DeviceType, CommunicationType
from swissairdry.api.app.mqtt import get_mqtt_client
from swissairdry.api.app.models.device import Device, SensorData, DeviceConfiguration, DeviceCommand
from swissairdry.api.app.schemas.device import (
    DeviceCreate, DeviceUpdate, DeviceResponse, SensorDataCreate,
    SensorDataResponse, DeviceConfigurationCreate, DeviceCommandCreate, DeviceCommandResponse,
    STM32DeviceRegister, STM32DeviceData
)


# Router erstellen
router = APIRouter(
    prefix="/api/devices",
    tags=["devices"],
    responses={404: {"description": "Not found"}},
)

# Device Manager initialisieren
device_manager = DeviceManager(get_mqtt_client())


@router.get("/", response_model=List[DeviceResponse])
def get_all_devices(
    skip: int = 0,
    limit: int = 100,
    device_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Gibt eine Liste aller registrierten Geräte zurück.
    
    Optionale Filter:
    - device_type: Filtert nach Gerätetyp (esp8266, esp32, stm32, other)
    - status: Filtert nach Gerätestatus (online, offline, maintenance, error, unknown)
    """
    query = db.query(Device)
    
    if device_type:
        query = query.filter(Device.device_type == device_type)
    
    if status:
        query = query.filter(Device.status == status)
    
    devices = query.offset(skip).limit(limit).all()
    return devices


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(device_id: str = Path(..., description="Die eindeutige ID des Geräts"),
              db: Session = Depends(get_db)):
    """
    Gibt detaillierte Informationen zu einem bestimmten Gerät zurück.
    """
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail=f"Gerät mit ID {device_id} nicht gefunden")
    
    return device


@router.post("/", response_model=DeviceResponse, status_code=201)
def create_device(device: DeviceCreate, db: Session = Depends(get_db)):
    """
    Registriert ein neues Gerät im System.
    """
    # Prüfen, ob Gerät bereits existiert
    existing_device = db.query(Device).filter(Device.device_id == device.device_id).first()
    if existing_device:
        raise HTTPException(status_code=400, detail=f"Gerät mit ID {device.device_id} existiert bereits")
    
    # Neues Gerät erstellen
    db_device = Device(
        device_id=device.device_id,
        name=device.name,
        device_type=device.device_type,
        communication_type=device.communication_type,
        location=device.location,
        firmware_version=device.firmware_version,
        ip_address=device.ip_address,
        device_metadata=device.metadata or {},
        is_active=True
    )
    
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    
    # Gerät im Device Manager registrieren
    device_manager.register_device(
        device_id=device.device_id,
        device_type=device.device_type,
        communication_type=device.communication_type,
        name=device.name,
        location=device.location,
        metadata=device.metadata
    )
    
    return db_device


@router.put("/{device_id}", response_model=DeviceResponse)
def update_device(
    device_id: str = Path(..., description="Die eindeutige ID des Geräts"),
    device_update: DeviceUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """
    Aktualisiert die Informationen eines vorhandenen Geräts.
    """
    db_device = db.query(Device).filter(Device.device_id == device_id).first()
    if not db_device:
        raise HTTPException(status_code=404, detail=f"Gerät mit ID {device_id} nicht gefunden")
    
    # Aktualisierbare Felder
    update_data = device_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_device, key, value)
    
    db_device.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_device)
    
    return db_device


@router.delete("/{device_id}", status_code=204)
def delete_device(
    device_id: str = Path(..., description="Die eindeutige ID des Geräts"),
    db: Session = Depends(get_db)
):
    """
    Löscht ein Gerät aus dem System.
    """
    db_device = db.query(Device).filter(Device.device_id == device_id).first()
    if not db_device:
        raise HTTPException(status_code=404, detail=f"Gerät mit ID {device_id} nicht gefunden")
    
    db.delete(db_device)
    db.commit()
    
    return None


@router.post("/{device_id}/data", response_model=SensorDataResponse)
def add_sensor_data(
    device_id: str = Path(..., description="Die eindeutige ID des Geräts"),
    data: SensorDataCreate = Body(...),
    db: Session = Depends(get_db)
):
    """
    Fügt neue Sensordaten für ein bestimmtes Gerät hinzu.
    """
    db_device = db.query(Device).filter(Device.device_id == device_id).first()
    if not db_device:
        raise HTTPException(status_code=404, detail=f"Gerät mit ID {device_id} nicht gefunden")
    
    # Neue Sensordaten erstellen
    sensor_data = SensorData(
        device_id=db_device.id,
        temperature=data.temperature,
        humidity=data.humidity,
        pressure=data.pressure,
        air_quality=data.air_quality,
        voltage=data.voltage,
        current=data.current,
        power=data.power,
        energy=data.energy,
        rssi=data.rssi,
        raw_data=data.raw_data or {},
        timestamp=datetime.utcnow()
    )
    
    db.add(sensor_data)
    
    # Gerätestatus und letzte Sichtung aktualisieren
    db_device.status = "online"
    db_device.last_seen = datetime.utcnow()
    
    db.commit()
    db.refresh(sensor_data)
    
    # Gerätedaten im Device Manager aktualisieren
    device_type = DeviceType(db_device.device_type)
    source = CommunicationType(db_device.communication_type)
    
    device_manager.update_device_data(
        device_id=device_id,
        data=data.dict(),
        source=source
    )
    
    return sensor_data


@router.get("/{device_id}/data", response_model=List[SensorDataResponse])
def get_sensor_data(
    device_id: str = Path(..., description="Die eindeutige ID des Geräts"),
    limit: int = Query(24, description="Maximale Anzahl an Datenpunkten"),
    hours: int = Query(24, description="Zeitraum in Stunden für die Daten"),
    db: Session = Depends(get_db)
):
    """
    Gibt die Sensordaten eines Geräts für einen bestimmten Zeitraum zurück.
    """
    db_device = db.query(Device).filter(Device.device_id == device_id).first()
    if not db_device:
        raise HTTPException(status_code=404, detail=f"Gerät mit ID {device_id} nicht gefunden")
    
    # Zeitraum berechnen
    time_limit = datetime.utcnow() - timedelta(hours=hours)
    
    # Daten abfragen
    sensor_data = (
        db.query(SensorData)
        .filter(SensorData.device_id == db_device.id, SensorData.timestamp >= time_limit)
        .order_by(SensorData.timestamp.desc())
        .limit(limit)
        .all()
    )
    
    return sensor_data


@router.post("/{device_id}/command", response_model=DeviceCommandResponse)
def send_command(
    device_id: str = Path(..., description="Die eindeutige ID des Geräts"),
    command: DeviceCommandCreate = Body(...),
    db: Session = Depends(get_db)
):
    """
    Sendet einen Befehl an ein Gerät.
    """
    db_device = db.query(Device).filter(Device.device_id == device_id).first()
    if not db_device:
        raise HTTPException(status_code=404, detail=f"Gerät mit ID {device_id} nicht gefunden")
    
    # Neuen Befehl in der Datenbank speichern
    db_command = DeviceCommand(
        device_id=db_device.id,
        command=command.command,
        parameters=command.parameters or {},
        created_at=datetime.utcnow()
    )
    
    db.add(db_command)
    db.commit()
    db.refresh(db_command)
    
    # Befehl über den Device Manager senden
    success = device_manager.send_command(
        device_id=device_id,
        command=command.command,
        params=command.parameters or {}
    )
    
    if success:
        db_command.executed = True
        db_command.executed_at = datetime.utcnow()
        db_command.result = "Befehl erfolgreich gesendet"
    else:
        db_command.result = "Fehler beim Senden des Befehls"
    
    db.commit()
    db.refresh(db_command)
    
    return db_command


@router.post("/stm32/register", response_model=DeviceResponse)
def register_stm32_device(device: STM32DeviceRegister, db: Session = Depends(get_db)):
    """
    Registriert ein neues STM32-Gerät im System.
    Diese Route ist speziell für STM32-Geräte optimiert und unterstützt deren
    spezifische Anforderungen.
    """
    # Prüfen, ob Gerät bereits existiert
    existing_device = db.query(Device).filter(Device.device_id == device.device_id).first()
    if existing_device:
        # Für STM32-Geräte aktualisieren wir die bestehenden Daten
        existing_device.name = device.name
        existing_device.location = device.location
        existing_device.firmware_version = device.firmware_version
        existing_device.ip_address = device.ip_address
        existing_device.updated_at = datetime.utcnow()
        existing_device.last_seen = datetime.utcnow()
        existing_device.status = "online"
        
        db.commit()
        db.refresh(existing_device)
        
        # Auch im Device Manager aktualisieren
        device_manager.register_device(
            device_id=device.device_id,
            device_type=DeviceType.STM32,
            communication_type=CommunicationType.MQTT,
            name=device.name,
            location=device.location
        )
        
        return existing_device
    
    # Neues STM32-Gerät erstellen
    db_device = Device(
        device_id=device.device_id,
        name=device.name,
        device_type=DeviceType.STM32,
        communication_type=device.communication_type or CommunicationType.MQTT,
        location=device.location,
        firmware_version=device.firmware_version,
        ip_address=device.ip_address,
        device_metadata=device.metadata or {},
        is_active=True
    )
    
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    
    # Gerät im Device Manager registrieren
    device_manager.register_device(
        device_id=device.device_id,
        device_type=DeviceType.STM32,
        communication_type=device.communication_type or CommunicationType.MQTT,
        name=device.name,
        location=device.location,
        metadata=device.metadata
    )
    
    return db_device


@router.post("/stm32/{device_id}/data", response_model=SensorDataResponse)
def add_stm32_sensor_data(
    device_id: str = Path(..., description="Die eindeutige ID des STM32-Geräts"),
    data: STM32DeviceData = Body(...),
    db: Session = Depends(get_db)
):
    """
    Fügt neue Sensordaten für ein STM32-Gerät hinzu.
    Diese Route berücksichtigt das spezielle Datenformat der STM32-Geräte.
    """
    db_device = db.query(Device).filter(Device.device_id == device_id).first()
    if not db_device:
        raise HTTPException(status_code=404, detail=f"STM32-Gerät mit ID {device_id} nicht gefunden")
    
    # STM32-spezifische Datenkonvertierung
    sensor_data = SensorData(
        device_id=db_device.id,
        temperature=data.temp,
        humidity=data.hum,
        pressure=data.pres,
        voltage=data.volt,
        raw_data=data.dict(),
        timestamp=datetime.utcnow()
    )
    
    db.add(sensor_data)
    
    # Gerätestatus und letzte Sichtung aktualisieren
    db_device.status = "online"
    db_device.last_seen = datetime.utcnow()
    
    db.commit()
    db.refresh(sensor_data)
    
    # Gerätedaten im Device Manager aktualisieren
    source = CommunicationType(db_device.communication_type)
    
    device_manager.update_device_data(
        device_id=device_id,
        data=data.dict(),
        source=source
    )
    
    return sensor_data