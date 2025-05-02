#!/bin/bash

# SwissAirDry STM32-Unterstützung einrichten
# Dieses Skript richtet die erforderlichen Komponenten für STM32-Unterstützung ein

# Farbige Ausgabe
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Funktion zum Anzeigen von Informationen
function info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Funktion zum Anzeigen von Erfolgen
function success() {
    echo -e "${GREEN}[ERFOLG]${NC} $1"
}

# Funktion zum Anzeigen von Warnungen
function warning() {
    echo -e "${YELLOW}[WARNUNG]${NC} $1"
}

# Funktion zum Anzeigen von Fehlern
function error() {
    echo -e "${RED}[FEHLER]${NC} $1"
}

echo -e "${BLUE}===========================================================${NC}"
echo -e "${BLUE}     SwissAirDry STM32-Unterstützung Einrichtung           ${NC}"
echo -e "${BLUE}===========================================================${NC}"
echo ""

# Erstelle Verzeichnisse für STM32-Support
info "Erstelle Verzeichnisse für STM32-Support..."
mkdir -p swissairdry/api/app/routes/stm32
mkdir -p swissairdry/api/app/models/stm32
mkdir -p swissairdry/api/app/schemas/stm32
mkdir -p swissairdry/api/app/utils/stm32
success "Verzeichnisse erstellt."

# Erstelle Basisdateien für STM32-Unterstützung
info "Erstelle Basis-Routes für STM32..."

# Erstelle stm32/__init__.py
cat > swissairdry/api/app/routes/stm32/__init__.py << 'EOF'
# STM32 Routes Package
from fastapi import APIRouter

stm32_router = APIRouter(prefix="/api/stm32", tags=["stm32"])

from . import data, device, command

__all__ = ["stm32_router"]
EOF

# Erstelle stm32/data.py
cat > swissairdry/api/app/routes/stm32/data.py << 'EOF'
"""
STM32 Daten-Endpunkte
---------------------

Diese Endpunkte verarbeiten Sensordaten von STM32-Geräten.
"""

from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session
import logging

from ... import models, schemas
from ...database import get_db
from ...mqtt import mqtt_client
from ..stm32 import stm32_router

logger = logging.getLogger(__name__)

@stm32_router.post("/data", response_model=schemas.stm32.STM32DataResponse)
async def receive_stm32_data(
    data: schemas.stm32.STM32Data,
    db: Session = Depends(get_db)
):
    """
    Empfängt Sensordaten von STM32-Geräten und speichert sie in der Datenbank.
    
    Parameter:
    - data: Die empfangenen Sensordaten
    - db: Datenbankverbindung
    
    Returns:
    - Die Bestätigung der gespeicherten Daten
    """
    try:
        # Überprüfen, ob das Gerät registriert ist
        device = db.query(models.Device).filter(
            models.Device.id == data.device_id
        ).first()
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"STM32-Gerät mit ID {data.device_id} wurde nicht gefunden."
            )
        
        # Speichern der Daten in der Datenbank
        db_data = models.stm32.STM32Data(
            device_id=data.device_id,
            temperature=data.temperature,
            humidity=data.humidity,
            pressure=data.pressure if hasattr(data, 'pressure') else None,
            voltage=data.voltage if hasattr(data, 'voltage') else None,
            status=data.status,
            timestamp=data.timestamp
        )
        
        db.add(db_data)
        db.commit()
        db.refresh(db_data)
        
        # MQTT-Veröffentlichung der Daten
        if mqtt_client:
            try:
                topic = f"swissairdry/stm32/{data.device_id}/data"
                payload = data.json()
                mqtt_client.publish(topic, payload)
                logger.info(f"Daten an MQTT-Topic {topic} gesendet")
            except Exception as mqtt_error:
                logger.error(f"Fehler bei MQTT-Veröffentlichung: {str(mqtt_error)}")
        
        return {
            "success": True,
            "message": "STM32-Daten erfolgreich gespeichert",
            "data_id": db_data.id
        }
    
    except ValidationError as validation_error:
        logger.error(f"Validierungsfehler: {str(validation_error)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validierungsfehler: {str(validation_error)}"
        )
    
    except Exception as e:
        logger.error(f"Fehler beim Speichern der STM32-Daten: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Speichern der STM32-Daten: {str(e)}"
        )

@stm32_router.get("/data/{device_id}", response_model=schemas.stm32.STM32DataList)
async def get_stm32_data(
    device_id: str,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Ruft die letzten Sensordaten für ein STM32-Gerät ab.
    
    Parameter:
    - device_id: Die ID des STM32-Geräts
    - limit: Die maximale Anzahl der zurückzugebenden Datensätze
    - db: Datenbankverbindung
    
    Returns:
    - Eine Liste der Sensordaten
    """
    try:
        # Überprüfen, ob das Gerät registriert ist
        device = db.query(models.Device).filter(
            models.Device.id == device_id
        ).first()
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"STM32-Gerät mit ID {device_id} wurde nicht gefunden."
            )
        
        # Abfrage der Daten
        data = db.query(models.stm32.STM32Data).filter(
            models.stm32.STM32Data.device_id == device_id
        ).order_by(
            models.stm32.STM32Data.timestamp.desc()
        ).limit(limit).all()
        
        return {
            "device_id": device_id,
            "count": len(data),
            "data": data
        }
    
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der STM32-Daten: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen der STM32-Daten: {str(e)}"
        )
EOF

# Erstelle stm32/device.py
cat > swissairdry/api/app/routes/stm32/device.py << 'EOF'
"""
STM32 Geräte-Endpunkte
----------------------

Diese Endpunkte verwalten STM32-Geräte.
"""

from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session
import logging

from ... import models, schemas
from ...database import get_db
from ..stm32 import stm32_router

logger = logging.getLogger(__name__)

@stm32_router.post("/register", response_model=schemas.DeviceResponse)
async def register_stm32_device(
    device: schemas.stm32.STM32DeviceCreate,
    db: Session = Depends(get_db)
):
    """
    Registriert ein neues STM32-Gerät im System.
    
    Parameter:
    - device: Die Gerätedaten
    - db: Datenbankverbindung
    
    Returns:
    - Die Bestätigung der Registrierung
    """
    try:
        # Überprüfen, ob Gerät bereits existiert
        existing_device = db.query(models.Device).filter(
            models.Device.id == device.id
        ).first()
        
        if existing_device:
            # Gerätedetails aktualisieren
            existing_device.name = device.name
            existing_device.location = device.location if device.location else existing_device.location
            existing_device.firmware_version = device.firmware_version if device.firmware_version else existing_device.firmware_version
            
            db.commit()
            db.refresh(existing_device)
            
            return {
                "success": True,
                "message": f"STM32-Gerät mit ID {device.id} wurde aktualisiert",
                "device_id": existing_device.id,
                "updated": True
            }
        
        # Neues Gerät erstellen
        new_device = models.Device(
            id=device.id,
            name=device.name,
            device_type="STM32",
            communication_type="MQTT",
            location=device.location or "Unbekannt",
            firmware_version=device.firmware_version or "0.0.1",
        )
        
        db.add(new_device)
        db.commit()
        db.refresh(new_device)
        
        # STM32-spezifische Konfiguration erstellen
        stm32_config = models.stm32.STM32Config(
            device_id=new_device.id,
            sensor_type=device.sensor_type,
            sampling_rate=device.sampling_rate or 60,
            power_mode=device.power_mode or "Normal"
        )
        
        db.add(stm32_config)
        db.commit()
        
        return {
            "success": True,
            "message": f"STM32-Gerät mit ID {device.id} wurde erfolgreich registriert",
            "device_id": new_device.id,
            "updated": False
        }
    
    except ValidationError as validation_error:
        logger.error(f"Validierungsfehler: {str(validation_error)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validierungsfehler: {str(validation_error)}"
        )
    
    except Exception as e:
        logger.error(f"Fehler bei der Registrierung des STM32-Geräts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler bei der Registrierung des STM32-Geräts: {str(e)}"
        )

@stm32_router.get("/devices", response_model=schemas.DeviceList)
async def list_stm32_devices(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Listet alle registrierten STM32-Geräte auf.
    
    Parameter:
    - skip: Die Anzahl der zu überspringenden Datensätze
    - limit: Die maximale Anzahl der zurückzugebenden Datensätze
    - db: Datenbankverbindung
    
    Returns:
    - Eine Liste von STM32-Geräten
    """
    try:
        devices = db.query(models.Device).filter(
            models.Device.device_type == "STM32"
        ).offset(skip).limit(limit).all()
        
        return {
            "count": len(devices),
            "devices": devices
        }
    
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der STM32-Geräte: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen der STM32-Geräte: {str(e)}"
        )
EOF

# Erstelle stm32/command.py
cat > swissairdry/api/app/routes/stm32/command.py << 'EOF'
"""
STM32 Befehls-Endpunkte
----------------------

Diese Endpunkte senden Befehle an STM32-Geräte.
"""

from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session
import logging
import json

from ... import models, schemas
from ...database import get_db
from ...mqtt import mqtt_client
from ..stm32 import stm32_router

logger = logging.getLogger(__name__)

@stm32_router.post("/command/{device_id}", response_model=schemas.CommandResponse)
async def send_command_to_stm32(
    device_id: str,
    command: schemas.stm32.STM32Command,
    db: Session = Depends(get_db)
):
    """
    Sendet einen Befehl an ein STM32-Gerät über MQTT.
    
    Parameter:
    - device_id: Die ID des STM32-Geräts
    - command: Der zu sendende Befehl
    - db: Datenbankverbindung
    
    Returns:
    - Die Bestätigung des gesendeten Befehls
    """
    try:
        # Überprüfen, ob das Gerät registriert ist
        device = db.query(models.Device).filter(
            models.Device.id == device_id,
            models.Device.device_type == "STM32"
        ).first()
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"STM32-Gerät mit ID {device_id} wurde nicht gefunden."
            )
        
        # Überprüfen, ob MQTT-Client initialisiert wurde
        if not mqtt_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MQTT-Client ist nicht verfügbar. Befehl kann nicht gesendet werden."
            )
        
        # Befehl als MQTT-Nachricht senden
        topic = f"swissairdry/stm32/{device_id}/command"
        payload = json.dumps({
            "command": command.command,
            "parameters": command.parameters
        })
        
        result = mqtt_client.publish(topic, payload)
        
        # Befehl in Datenbank speichern
        db_command = models.Command(
            device_id=device_id,
            command_type=command.command,
            parameters=str(command.parameters),
            sent=True
        )
        
        db.add(db_command)
        db.commit()
        
        if result.rc == 0:
            return {
                "success": True,
                "message": f"Befehl '{command.command}' erfolgreich an {device_id} gesendet",
                "command_id": db_command.id
            }
        else:
            logger.error(f"MQTT-Fehler: {result.rc}")
            return {
                "success": False,
                "message": f"Fehler beim Senden des Befehls: MQTT-Fehler {result.rc}",
                "command_id": db_command.id
            }
    
    except ValidationError as validation_error:
        logger.error(f"Validierungsfehler: {str(validation_error)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validierungsfehler: {str(validation_error)}"
        )
    
    except Exception as e:
        logger.error(f"Fehler beim Senden des Befehls an das STM32-Gerät: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Senden des Befehls: {str(e)}"
        )
EOF

# Erstelle STM32 Models
info "Erstelle STM32-Modelle..."

# Erstelle models/stm32/__init__.py
mkdir -p swissairdry/api/app/models/stm32
cat > swissairdry/api/app/models/stm32/__init__.py << 'EOF'
# STM32 Models Package
from .data import STM32Data
from .config import STM32Config

__all__ = ["STM32Data", "STM32Config"]
EOF

# Erstelle models/stm32/data.py
cat > swissairdry/api/app/models/stm32/data.py << 'EOF'
"""
STM32 Datenmodell
---------------

Dieses Modell definiert die Struktur der Sensordaten von STM32-Geräten in der Datenbank.
"""

from sqlalchemy import Column, Float, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from ...database import Base

class STM32Data(Base):
    """Modell für STM32 Sensordaten."""
    
    __tablename__ = "stm32_data"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, ForeignKey("devices.id"))
    temperature = Column(Float)
    humidity = Column(Float)
    pressure = Column(Float, nullable=True)
    voltage = Column(Float, nullable=True)
    status = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Beziehung zum Gerät
    device = relationship("Device", back_populates="stm32_data")
EOF

# Erstelle models/stm32/config.py
cat > swissairdry/api/app/models/stm32/config.py << 'EOF'
"""
STM32 Konfigurationsmodell
------------------------

Dieses Modell definiert die Struktur der Konfigurationsdaten für STM32-Geräte.
"""

from sqlalchemy import Column, Float, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from ...database import Base

class STM32Config(Base):
    """Modell für STM32-Konfiguration."""
    
    __tablename__ = "stm32_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, ForeignKey("devices.id"), unique=True)
    sensor_type = Column(String) # z.B. "BME280", "DHT22"
    sampling_rate = Column(Integer, default=60) # Abtastrate in Sekunden
    power_mode = Column(String, default="Normal") # z.B. "Normal", "LowPower"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Beziehung zum Gerät
    device = relationship("Device", back_populates="stm32_config")
EOF

# Erstelle STM32 Schemas
info "Erstelle STM32-Schemas..."

# Erstelle schemas/stm32/__init__.py
mkdir -p swissairdry/api/app/schemas/stm32
cat > swissairdry/api/app/schemas/stm32/__init__.py << 'EOF'
# STM32 Schemas Package
from .data import STM32Data, STM32DataResponse, STM32DataList
from .device import STM32DeviceCreate
from .command import STM32Command

__all__ = [
    "STM32Data", 
    "STM32DataResponse", 
    "STM32DataList", 
    "STM32DeviceCreate", 
    "STM32Command"
]
EOF

# Erstelle schemas/stm32/data.py
cat > swissairdry/api/app/schemas/stm32/data.py << 'EOF'
"""
STM32 Daten-Schemas
-----------------

Diese Schemas definieren die API-Datenstrukturen für STM32-Geräte.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class STM32Data(BaseModel):
    """Schema für eingehende STM32-Sensordaten."""
    
    device_id: str
    temperature: float
    humidity: float
    pressure: Optional[float] = None
    voltage: Optional[float] = None
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True

class STM32DataResponse(BaseModel):
    """Antwortschema für gespeicherte STM32-Daten."""
    
    success: bool
    message: str
    data_id: int

class STM32DataItem(BaseModel):
    """Schema für ein einzelnes STM32-Datenelement in Listen."""
    
    id: int
    temperature: float
    humidity: float
    pressure: Optional[float] = None
    voltage: Optional[float] = None
    status: str
    timestamp: datetime
    
    class Config:
        from_attributes = True

class STM32DataList(BaseModel):
    """Schema für eine Liste von STM32-Daten."""
    
    device_id: str
    count: int
    data: List[STM32DataItem]
EOF

# Erstelle schemas/stm32/device.py
cat > swissairdry/api/app/schemas/stm32/device.py << 'EOF'
"""
STM32 Geräte-Schemas
-----------------

Diese Schemas definieren die API-Datenstrukturen für STM32-Geräte.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class STM32DeviceCreate(BaseModel):
    """Schema für die Registrierung eines STM32-Geräts."""
    
    id: str
    name: str
    location: Optional[str] = None
    firmware_version: Optional[str] = None
    sensor_type: str
    sampling_rate: Optional[int] = 60
    power_mode: Optional[str] = "Normal"
    
    class Config:
        from_attributes = True
EOF

# Erstelle schemas/stm32/command.py
cat > swissairdry/api/app/schemas/stm32/command.py << 'EOF'
"""
STM32 Befehls-Schemas
------------------

Diese Schemas definieren die API-Datenstrukturen für Befehle an STM32-Geräte.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

class STM32Command(BaseModel):
    """Schema für einen Befehl an ein STM32-Gerät."""
    
    command: str  # z.B. "restart", "update", "set_config"
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True
EOF

# Aktualisiere Device-Modelle für STM32-Beziehungen
info "Aktualisiere Device-Modelle für STM32-Beziehungen..."

# Erstelle ein temporäres Patch-Skript für device.py
cat > patch_device.py << 'EOF'
import os

device_file = "swissairdry/api/app/models/device.py"

# Überprüfen, ob die Datei existiert
if os.path.exists(device_file):
    # Datei öffnen und Inhalt lesen
    with open(device_file, "r") as f:
        content = f.read()
    
    # Überprüfen, ob already_patched erscheint
    if "stm32_data = relationship" in content:
        print("Datei wurde bereits gepatcht. Keine Änderungen vorgenommen.")
        exit(0)
    
    # Finde die richtige Stelle für die Beziehungen
    if "relationships" in content:
        # Füge STM32-Beziehungen hinzu
        content = content.replace(
            "# relationships",
            "# relationships\n    stm32_data = relationship(\"STM32Data\", back_populates=\"device\")\n    stm32_config = relationship(\"STM32Config\", back_populates=\"device\", uselist=False)"
        )
        
        # Schreibe die geänderte Datei zurück
        with open(device_file, "w") as f:
            f.write(content)
        
        print(f"{device_file} erfolgreich aktualisiert.")
    else:
        print(f"Konnte den Einstiegspunkt für Beziehungen in {device_file} nicht finden.")
        exit(1)
else:
    # Erstelle eine neue Device-Datei mit STM32-Unterstützung
    os.makedirs(os.path.dirname(device_file), exist_ok=True)
    
    with open(device_file, "w") as f:
        f.write("""
\"\"\"
Gerätemodell
----------

Dieses Modell definiert die Struktur der Gerätedaten in der Datenbank.
\"\"\"

from sqlalchemy import Column, String, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from datetime import datetime

from ..database import Base

class DeviceType(str, PyEnum):
    \"\"\"Aufzählung der unterstützten Gerätetypen.\"\"\"
    ESP8266 = "ESP8266"
    ESP32 = "ESP32"
    STM32 = "STM32"
    RASPBERRY_PI = "RASPBERRY_PI"

class CommunicationType(str, PyEnum):
    \"\"\"Aufzählung der unterstützten Kommunikationstypen.\"\"\"
    MQTT = "MQTT"
    HTTP = "HTTP"
    BLUETOOTH = "BLUETOOTH"

class Device(Base):
    \"\"\"Modell für Geräte.\"\"\"
    
    __tablename__ = "devices"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    device_type = Column(String)
    communication_type = Column(String)
    location = Column(String, nullable=True)
    firmware_version = Column(String, nullable=True)
    last_seen = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    config = Column(Text, nullable=True)
    
    # relationships
    stm32_data = relationship("STM32Data", back_populates="device")
    stm32_config = relationship("STM32Config", back_populates="device", uselist=False)
""")
        
        print(f"{device_file} erfolgreich erstellt.")
EOF

# Führe das Patch-Skript aus
python patch_device.py

# Erstelle eine Beispiel-Dokumentation für STM32-API
info "Erstelle STM32-API-Dokumentation..."

mkdir -p docs/stm32
cat > docs/stm32/api_reference.md << 'EOF'
# STM32 API-Referenz

Diese Dokumentation beschreibt die API-Endpunkte für die Kommunikation mit STM32-Geräten.

## Geräteregistrierung

### Registriere ein STM32-Gerät

`POST /api/stm32/register`

Registriert ein neues STM32-Gerät im System oder aktualisiert ein bestehendes.

**Request Body:**
```json
{
  "id": "stm32-001",
  "name": "Temperatur-Sensor Raum 1",
  "location": "Gebäude A, Raum 101",
  "firmware_version": "1.0.0",
  "sensor_type": "BME280",
  "sampling_rate": 30,
  "power_mode": "Normal"
}
```

**Response:**
```json
{
  "success": true,
  "message": "STM32-Gerät mit ID stm32-001 wurde erfolgreich registriert",
  "device_id": "stm32-001",
  "updated": false
}
```

## Datenendpunkte

### Sende Sensordaten

`POST /api/stm32/data`

Sendet Sensordaten von einem STM32-Gerät an den Server.

**Request Body:**
```json
{
  "device_id": "stm32-001",
  "temperature": 21.5,
  "humidity": 45.3,
  "pressure": 1013.2,
  "voltage": 3.3,
  "status": "online",
  "timestamp": "2024-04-28T15:30:00Z"
}
```

**Response:**
```json
{
  "success": true,
  "message": "STM32-Daten erfolgreich gespeichert",
  "data_id": 123
}
```

### Hole Gerätedaten

`GET /api/stm32/data/{device_id}?limit=100`

Ruft die letzten Sensordaten für ein bestimmtes STM32-Gerät ab.

**Response:**
```json
{
  "device_id": "stm32-001",
  "count": 2,
  "data": [
    {
      "id": 124,
      "temperature": 21.6,
      "humidity": 45.5,
      "pressure": 1013.0,
      "voltage": 3.3,
      "status": "online",
      "timestamp": "2024-04-28T15:35:00Z"
    },
    {
      "id": 123,
      "temperature": 21.5,
      "humidity": 45.3,
      "pressure": 1013.2,
      "voltage": 3.3,
      "status": "online",
      "timestamp": "2024-04-28T15:30:00Z"
    }
  ]
}
```

## Befehlsendpunkte

### Sende Befehl an Gerät

`POST /api/stm32/command/{device_id}`

Sendet einen Befehl an ein STM32-Gerät.

**Request Body:**
```json
{
  "command": "set_config",
  "parameters": {
    "sampling_rate": 60,
    "power_mode": "LowPower"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Befehl 'set_config' erfolgreich an stm32-001 gesendet",
  "command_id": 45
}
```

## Geräteverwaltung

### Liste alle STM32-Geräte

`GET /api/stm32/devices?skip=0&limit=100`

Ruft eine Liste aller registrierten STM32-Geräte ab.

**Response:**
```json
{
  "count": 2,
  "devices": [
    {
      "id": "stm32-001",
      "name": "Temperatur-Sensor Raum 1",
      "device_type": "STM32",
      "communication_type": "MQTT",
      "location": "Gebäude A, Raum 101",
      "firmware_version": "1.0.0",
      "last_seen": "2024-04-28T15:35:00Z",
      "created_at": "2024-04-20T10:00:00Z"
    },
    {
      "id": "stm32-002",
      "name": "Temperatur-Sensor Raum 2",
      "device_type": "STM32",
      "communication_type": "MQTT",
      "location": "Gebäude A, Raum 102",
      "firmware_version": "1.0.0",
      "last_seen": "2024-04-28T15:34:00Z",
      "created_at": "2024-04-20T10:15:00Z"
    }
  ]
}
```
EOF

# Erstelle eine Beispiel-Client für STM32-Geräte
info "Erstelle Beispiel-Client für STM32-Geräte..."

mkdir -p examples/stm32
cat > examples/stm32/mqtt_client.py << 'EOF'
"""
STM32 MQTT-Client Beispiel

Dieses Skript zeigt, wie ein STM32-Gerät mit dem MQTT-Broker kommunizieren kann.
Der Code kann als Grundlage für die Implementierung auf einem STM32-Gerät dienen.
"""

import time
import json
import random
from datetime import datetime
import paho.mqtt.client as mqtt

# Konfiguration
MQTT_BROKER = "localhost"  # Ändern Sie dies zu Ihrer MQTT-Broker-Adresse
MQTT_PORT = 1883
DEVICE_ID = "stm32-example-001"
MQTT_TOPIC_DATA = f"swissairdry/stm32/{DEVICE_ID}/data"
MQTT_TOPIC_COMMAND = f"swissairdry/stm32/{DEVICE_ID}/command"
MQTT_TOPIC_STATUS = f"swissairdry/stm32/{DEVICE_ID}/status"

# Simulierte Sensordaten
def generate_sensor_data():
    """Generiert simulierte Sensordaten."""
    return {
        "device_id": DEVICE_ID,
        "temperature": 20.0 + random.uniform(0, 5),
        "humidity": 40.0 + random.uniform(0, 10),
        "pressure": 1013.0 + random.uniform(-5, 5),
        "voltage": 3.3 - random.uniform(0, 0.3),
        "status": "online",
        "timestamp": datetime.utcnow().isoformat()
    }

# MQTT-Callbacks
def on_connect(client, userdata, flags, rc):
    """Callback für erfolgreiche Verbindung."""
    print(f"Verbunden mit MQTT-Broker: {rc}")
    # Abonniere den Befehls-Topic
    client.subscribe(MQTT_TOPIC_COMMAND)
    # Sende Online-Status
    client.publish(MQTT_TOPIC_STATUS, json.dumps({"status": "online"}))

def on_message(client, userdata, msg):
    """Callback für eingehende Nachrichten."""
    print(f"Nachricht erhalten: {msg.topic} = {msg.payload.decode()}")
    
    # Verarbeite Befehle
    if msg.topic == MQTT_TOPIC_COMMAND:
        try:
            command = json.loads(msg.payload.decode())
            print(f"Befehl erhalten: {command}")
            
            # Hier können Sie den Befehl verarbeiten
            if command.get("command") == "restart":
                print("Gerät wird neu gestartet...")
                # Implementieren Sie hier den Neustart
            
            elif command.get("command") == "set_config":
                params = command.get("parameters", {})
                print(f"Konfiguration wird geändert: {params}")
                # Implementieren Sie hier die Konfigurationsänderung
        
        except json.JSONDecodeError:
            print("Ungültiges JSON-Format in der Nachricht")
        except Exception as e:
            print(f"Fehler bei der Verarbeitung des Befehls: {str(e)}")

def on_disconnect(client, userdata, rc):
    """Callback für Verbindungsabbruch."""
    print(f"Verbindung zum MQTT-Broker getrennt: {rc}")

# Hauptprogramm
def main():
    """Hauptfunktion."""
    # MQTT-Client initialisieren
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    # Verbindung zum MQTT-Broker herstellen
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(f"Fehler beim Verbinden mit dem MQTT-Broker: {str(e)}")
        return
    
    # Client-Loop im Hintergrund starten
    client.loop_start()
    
    try:
        # Hauptschleife
        while True:
            # Sensordaten generieren und senden
            data = generate_sensor_data()
            client.publish(MQTT_TOPIC_DATA, json.dumps(data))
            print(f"Daten gesendet: {data}")
            
            # Warte 5 Sekunden
            time.sleep(5)
    
    except KeyboardInterrupt:
        print("Programm wird beendet")
    finally:
        # Offline-Status senden
        client.publish(MQTT_TOPIC_STATUS, json.dumps({"status": "offline"}))
        # Client-Loop beenden
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
EOF

# Aufräumen und Beenden
rm -f patch_device.py

echo ""
success "STM32-Unterstützung wurde erfolgreich eingerichtet!"
echo ""
info "Dateien erstellt:"
echo "  - API-Routen: swissairdry/api/app/routes/stm32/"
echo "  - Datenmodelle: swissairdry/api/app/models/stm32/"
echo "  - Schemas: swissairdry/api/app/schemas/stm32/"
echo "  - Dokumentation: docs/stm32/api_reference.md"
echo "  - Beispiel-Client: examples/stm32/mqtt_client.py"
echo ""
info "Um die STM32-Unterstützung zu nutzen, müssen Sie die API-Server neu starten."
echo ""