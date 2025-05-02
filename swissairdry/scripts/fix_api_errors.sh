#!/bin/bash

# Fix-Skript für API-Fehler im SwissAirDry-Projekt
# Dieses Skript behebt spezifische Fehler in der API-Implementierung

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
echo -e "${BLUE}     SwissAirDry API-Fehler Fixskript                      ${NC}"
echo -e "${BLUE}===========================================================${NC}"
echo ""

# 1. Erstelle notwendige Verzeichnisse, falls sie nicht existieren
info "Erstelle notwendige Verzeichnisse..."
mkdir -p swissairdry/api/app/{routes,models,schemas,utils,templates,static}
mkdir -p swissairdry/api/tests
success "Verzeichnisse wurden erstellt"

# 2. Behebe den 'metadata'-Namenskonflikt in device.py
info "Suche nach der Datei device.py..."
DEVICE_FILE=$(find . -name device.py | grep -i models | head -n 1)

if [ -n "$DEVICE_FILE" ]; then
    info "Datei gefunden: $DEVICE_FILE"
    
    # Erstelle ein Backup
    cp "$DEVICE_FILE" "${DEVICE_FILE}.bak"
    
    # Überprüfe, ob die Datei ein 'metadata'-Attribut enthält
    if grep -q "metadata" "$DEVICE_FILE"; then
        info "Konflikt gefunden: 'metadata' ist ein reservierter Name in SQLAlchemy"
        
        # Ersetze 'metadata' durch 'device_metadata' oder einen anderen nicht reservierten Namen
        sed -i 's/metadata/device_metadata/g' "$DEVICE_FILE"
        success "Namenskonflikt in $DEVICE_FILE behoben (metadata -> device_metadata)"
    else
        warning "Kein 'metadata'-Konflikt in $DEVICE_FILE gefunden"
    fi
else
    warning "device.py wurde nicht gefunden. Erstelle eine neue Basisdatei..."
    
    # Erstelle Verzeichnis für das neue file
    mkdir -p swissairdry/api/app/models
    
    # Erstelle eine neue device.py-Datei ohne Konflikte
    cat > swissairdry/api/app/models/device.py << 'EOF'
"""
Gerätemodell
----------

Dieses Modell definiert die Struktur der Gerätedaten in der Datenbank.
"""

from sqlalchemy import Column, String, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from datetime import datetime

from ..database import Base

class DeviceType(str, PyEnum):
    """Aufzählung der unterstützten Gerätetypen."""
    ESP8266 = "ESP8266"
    ESP32 = "ESP32"
    STM32 = "STM32"
    RASPBERRY_PI = "RASPBERRY_PI"

class CommunicationType(str, PyEnum):
    """Aufzählung der unterstützten Kommunikationstypen."""
    MQTT = "MQTT"
    HTTP = "HTTP"
    BLUETOOTH = "BLUETOOTH"

class Device(Base):
    """Modell für Geräte."""
    
    __tablename__ = "devices"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    device_type = Column(String)
    communication_type = Column(String)
    location = Column(String, nullable=True)
    firmware_version = Column(String, nullable=True)
    last_seen = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    device_metadata = Column(Text, nullable=True)  # Beachte den nicht-konfliktierenden Namen
    
    # Beziehungen
    # stm32_data = relationship("STM32Data", back_populates="device")
    # stm32_config = relationship("STM32Config", back_populates="device", uselist=False)
EOF
    success "Neue device.py-Datei ohne Konflikte erstellt"
fi

# 3. Erstelle eine korrekte database.py, falls nicht vorhanden
info "Überprüfe database.py..."
DB_FILE="swissairdry/api/app/database.py"

if [ -f "$DB_FILE" ]; then
    info "database.py gefunden. Erstelle Backup..."
    cp "$DB_FILE" "${DB_FILE}.bak"
    
    # Überprüfe auf typische Probleme und behebe sie
    if grep -q "Base = declarative_base()" "$DB_FILE"; then
        info "Aktualisiere SQLAlchemy-Implementierung auf neuere Version..."
        cat > "$DB_FILE" << 'EOF'
"""
Datenbankmodul
-------------

Dieses Modul stellt die Datenbankverbindung und SQLAlchemy-Base-Klasse bereit.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

# Datenbank-URL aus Umgebungsvariablen oder Standardwerte
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "swissairdry")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "swissairdry")

SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Engine mit Verbindungspooling
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # Prüfung der Verbindung vor Verwendung
    pool_recycle=300,    # Verbindungen alle 5 Minuten erneuern
)

# SessionLocal-Klasse
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base-Klasse für deklarative Modelle
Base = declarative_base()

# Hilfsfunktion zum Erhalten einer DB-Session
def get_db():
    """
    Gibt eine Datenbankverbindung zurück und stellt sicher, dass sie geschlossen wird,
    wenn sie nicht mehr benötigt wird.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
EOF
        success "database.py wurde aktualisiert"
    else
        info "database.py sieht korrekt aus, keine Änderungen erforderlich"
    fi
else
    info "database.py nicht gefunden. Erstelle neue Datei..."
    mkdir -p $(dirname "$DB_FILE")
    cat > "$DB_FILE" << 'EOF'
"""
Datenbankmodul
-------------

Dieses Modul stellt die Datenbankverbindung und SQLAlchemy-Base-Klasse bereit.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

# Datenbank-URL aus Umgebungsvariablen oder Standardwerte
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "swissairdry")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "swissairdry")

SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Engine mit Verbindungspooling
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # Prüfung der Verbindung vor Verwendung
    pool_recycle=300,    # Verbindungen alle 5 Minuten erneuern
)

# SessionLocal-Klasse
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base-Klasse für deklarative Modelle
Base = declarative_base()

# Hilfsfunktion zum Erhalten einer DB-Session
def get_db():
    """
    Gibt eine Datenbankverbindung zurück und stellt sicher, dass sie geschlossen wird,
    wenn sie nicht mehr benötigt wird.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
EOF
    success "Neue database.py-Datei erstellt"
fi

# 4. Erstelle oder aktualisiere __init__.py-Dateien, um Zirkelbezüge zu vermeiden
info "Erstelle oder aktualisiere __init__.py-Dateien..."

# Hauptpaket __init__.py
API_INIT="swissairdry/api/app/__init__.py"
mkdir -p $(dirname "$API_INIT")
cat > "$API_INIT" << 'EOF'
"""
SwissAirDry API-Paket
-------------------

Dieses Paket enthält die API-Implementierung für das SwissAirDry-System.
"""

__version__ = "1.0.0"
EOF
success "app/__init__.py erstellt"

# Models __init__.py
MODELS_INIT="swissairdry/api/app/models/__init__.py"
mkdir -p $(dirname "$MODELS_INIT")
cat > "$MODELS_INIT" << 'EOF'
"""
Modelle-Paket
-----------

Dieses Paket enthält die SQLAlchemy-Modelle für die Datenbank.
"""

from .device import Device, DeviceType, CommunicationType

__all__ = ["Device", "DeviceType", "CommunicationType"]
EOF
success "models/__init__.py erstellt"

# Routes __init__.py
ROUTES_INIT="swissairdry/api/app/routes/__init__.py"
mkdir -p $(dirname "$ROUTES_INIT")
cat > "$ROUTES_INIT" << 'EOF'
"""
Routen-Paket
----------

Dieses Paket enthält die API-Routen und Endpunkte.
"""

from fastapi import APIRouter

api_router = APIRouter()

# Importiere die Routen-Module
# from .devices import router as devices_router
# from .data import router as data_router

# Registriere die Routen
# api_router.include_router(devices_router, prefix="/devices", tags=["devices"])
# api_router.include_router(data_router, prefix="/data", tags=["data"])

__all__ = ["api_router"]
EOF
success "routes/__init__.py erstellt"

# Schemas __init__.py
SCHEMAS_INIT="swissairdry/api/app/schemas/__init__.py"
mkdir -p $(dirname "$SCHEMAS_INIT")
cat > "$SCHEMAS_INIT" << 'EOF'
"""
Schemas-Paket
-----------

Dieses Paket enthält die Pydantic-Modelle für API-Requests und -Responses.
"""

# Importiere die Schema-Klassen hier
# from .device import DeviceCreate, DeviceUpdate, DeviceResponse, DeviceList
# from .data import DataCreate, DataResponse, DataList

# __all__ = [
#     "DeviceCreate", "DeviceUpdate", "DeviceResponse", "DeviceList",
#     "DataCreate", "DataResponse", "DataList"
# ]
EOF
success "schemas/__init__.py erstellt"

# 5. Erstelle eine verbesserte run.py mit Fehlerbehandlung
info "Erstelle eine verbesserte run.py..."
RUN_FILE="swissairdry/api/app/run.py"

cat > "$RUN_FILE" << 'EOF'
#!/usr/bin/env python3
"""
SwissAirDry FastAPI Server
--------------------------

FastAPI-Server für die Haupt-API von SwissAirDry.
"""

import os
import logging
import sys
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

# Logging-Konfiguration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Lade Umgebungsvariablen
load_dotenv()

try:
    # Versuche, die Datenbankmodule zu importieren
    from .database import Base, engine
    from .models import Device
    
    # Erstelle die Datenbanktabellen
    Base.metadata.create_all(bind=engine)
    logger.info("Datenbanktabellen wurden erstellt")
    
except Exception as db_error:
    logger.error(f"Fehler bei der Datenbankinitialisierung: {str(db_error)}")
    # Setze das Programm trotz Fehler fort, aber ohne Datenbankfunktionalität

# FastAPI-App erstellen
app = FastAPI(
    title="SwissAirDry API",
    description="API für die Verwaltung von SwissAirDry-Geräten",
    version="1.0.0"
)

# CORS-Konfiguration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Globale Ausnahmebehandlung
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unbehandelte Ausnahme: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Interner Serverfehler", "details": str(exc)}
    )

# API-Routen
@app.get("/")
async def root():
    """Startseite"""
    return {"message": "Willkommen bei der SwissAirDry API"}

@app.get("/api/status")
async def status():
    """API-Status"""
    return {
        "status": "online",
        "version": "1.0.0"
    }

# Importiere die API-Routen, falls sie existieren
try:
    from .routes import api_router
    app.include_router(api_router, prefix="/api")
    logger.info("API-Routen wurden registriert")
except ImportError as import_error:
    logger.warning(f"API-Routen konnten nicht importiert werden: {str(import_error)}")
    logger.warning("Die API läuft mit eingeschränkter Funktionalität")

# MQTT-Client initialisieren, falls verfügbar
try:
    import paho.mqtt.client as mqtt
    
    # MQTT-Konfiguration aus Umgebungsvariablen oder Standardwerte
    MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
    MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
    
    # MQTT-Callbacks
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"Mit MQTT-Broker verbunden: {MQTT_BROKER}:{MQTT_PORT}")
            client.subscribe("swissairdry/#")
        else:
            logger.warning(f"Verbindung zum MQTT-Broker fehlgeschlagen mit Code {rc}")
    
    def on_message(client, userdata, msg):
        logger.debug(f"MQTT-Nachricht empfangen: {msg.topic}")
    
    # MQTT-Client initialisieren
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    
    # Verbinde mit MQTT-Broker
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        logger.info("MQTT-Client wurde initialisiert")
    except Exception as mqtt_error:
        logger.warning(f"Verbindung zum MQTT-Broker fehlgeschlagen: {str(mqtt_error)}")
        mqtt_client = None
    
except ImportError:
    logger.warning("paho-mqtt nicht installiert. MQTT-Funktionalität deaktiviert.")
    mqtt_client = None

# Hauptfunktion
if __name__ == "__main__":
    logger.info("API-Server wird gestartet...")
    
    # Server-Port aus Umgebungsvariablen oder Standardwert
    PORT = int(os.getenv("API_PORT", 5000))
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=PORT)
    except KeyboardInterrupt:
        logger.info("API-Server wurde vom Benutzer gestoppt")
    except Exception as server_error:
        logger.error(f"Serverfehler: {str(server_error)}")
    finally:
        # MQTT-Client beenden, falls aktiv
        if mqtt_client:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
            logger.info("MQTT-Client wurde beendet")
        
        logger.info("API-Server wurde beendet")
EOF
chmod +x "$RUN_FILE"
success "Verbesserte run.py mit Fehlerbehandlung erstellt"

# 6. Installiere die notwendigen Dependencies zur Laufzeit
info "Installiere notwendige Python-Pakete..."
pip install --quiet --upgrade fastapi uvicorn sqlalchemy psycopg2-binary pydantic python-dotenv paho-mqtt
success "Python-Pakete installiert"

# 7. Erstelle eine minimal funktionierende models/device.py und schemas
info "Erstelle minimale funktionierende Schemas..."

# Erstelle ein Device-Schema
DEVICE_SCHEMA="swissairdry/api/app/schemas/device.py"
mkdir -p $(dirname "$DEVICE_SCHEMA")
cat > "$DEVICE_SCHEMA" << 'EOF'
"""
Geräte-Schemas
------------

Diese Schemas definieren die API-Datenstrukturen für Geräte.
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class DeviceBase(BaseModel):
    """Basisschema für Geräte."""
    name: str
    device_type: str
    communication_type: str
    location: Optional[str] = None
    firmware_version: Optional[str] = None

class DeviceCreate(DeviceBase):
    """Schema für die Erstellung eines Geräts."""
    id: str

class DeviceUpdate(BaseModel):
    """Schema für die Aktualisierung eines Geräts."""
    name: Optional[str] = None
    location: Optional[str] = None
    firmware_version: Optional[str] = None
    device_metadata: Optional[str] = None

class DeviceInDB(DeviceBase):
    """Schema für ein Gerät in der Datenbank."""
    id: str
    last_seen: datetime
    created_at: datetime
    device_metadata: Optional[str] = None
    
    class Config:
        from_attributes = True

class DeviceResponse(BaseModel):
    """Antwortschema für Geräte-Operationen."""
    success: bool
    message: str
    device_id: str
    updated: Optional[bool] = None

class DeviceItem(BaseModel):
    """Schema für ein einzelnes Gerät in Listen."""
    id: str
    name: str
    device_type: str
    communication_type: str
    location: Optional[str] = None
    firmware_version: Optional[str] = None
    last_seen: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

class DeviceList(BaseModel):
    """Schema für eine Liste von Geräten."""
    count: int
    devices: List[DeviceItem]
EOF
success "Device-Schema erstellt"

# Aktualisiere models/__init__.py für das Schema
cat > "$SCHEMAS_INIT" << 'EOF'
"""
Schemas-Paket
-----------

Dieses Paket enthält die Pydantic-Modelle für API-Requests und -Responses.
"""

from .device import DeviceCreate, DeviceUpdate, DeviceResponse, DeviceList, DeviceInDB, DeviceItem, DeviceBase

__all__ = [
    "DeviceBase", "DeviceCreate", "DeviceUpdate", "DeviceResponse", "DeviceList", "DeviceInDB", "DeviceItem"
]
EOF
success "schemas/__init__.py aktualisiert"

# 8. Erstelle eine simple API-Route für Geräte
info "Erstelle eine einfache API-Route für Geräte..."
DEVICES_ROUTE="swissairdry/api/app/routes/devices.py"
mkdir -p $(dirname "$DEVICES_ROUTE")
cat > "$DEVICES_ROUTE" << 'EOF'
"""
Geräte-Routen
-----------

Diese Routen verwalten Geräteoperationen.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
from typing import List

from .. import models, schemas
from ..database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=schemas.DeviceResponse)
def create_device(device: schemas.DeviceCreate, db: Session = Depends(get_db)):
    """
    Erstellt ein neues Gerät.
    """
    try:
        # Prüfe, ob Gerät bereits existiert
        db_device = db.query(models.Device).filter(models.Device.id == device.id).first()
        if db_device:
            # Aktualisiere das Gerät
            db_device.name = device.name
            db_device.device_type = device.device_type
            db_device.communication_type = device.communication_type
            
            if device.location:
                db_device.location = device.location
            
            if device.firmware_version:
                db_device.firmware_version = device.firmware_version
            
            db.commit()
            db.refresh(db_device)
            
            return {
                "success": True,
                "message": f"Gerät mit ID {device.id} aktualisiert",
                "device_id": db_device.id,
                "updated": True
            }
        
        # Erstelle neues Gerät
        new_device = models.Device(
            id=device.id,
            name=device.name,
            device_type=device.device_type,
            communication_type=device.communication_type,
            location=device.location,
            firmware_version=device.firmware_version
        )
        
        db.add(new_device)
        db.commit()
        db.refresh(new_device)
        
        return {
            "success": True,
            "message": f"Gerät mit ID {device.id} erstellt",
            "device_id": new_device.id,
            "updated": False
        }
    
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Geräts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/", response_model=schemas.DeviceList)
def read_devices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Gibt eine Liste aller Geräte zurück.
    """
    try:
        devices = db.query(models.Device).offset(skip).limit(limit).all()
        return {
            "count": len(devices),
            "devices": devices
        }
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Geräte: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{device_id}", response_model=schemas.DeviceItem)
def read_device(device_id: str, db: Session = Depends(get_db)):
    """
    Gibt ein Gerät anhand seiner ID zurück.
    """
    try:
        device = db.query(models.Device).filter(models.Device.id == device_id).first()
        if device is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Gerät mit ID {device_id} nicht gefunden"
            )
        return device
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Geräts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{device_id}", response_model=schemas.DeviceResponse)
def update_device(device_id: str, device: schemas.DeviceUpdate, db: Session = Depends(get_db)):
    """
    Aktualisiert ein Gerät.
    """
    try:
        db_device = db.query(models.Device).filter(models.Device.id == device_id).first()
        if db_device is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Gerät mit ID {device_id} nicht gefunden"
            )
        
        # Aktualisiere die Felder, falls sie im Request vorhanden sind
        if device.name:
            db_device.name = device.name
        
        if device.location:
            db_device.location = device.location
        
        if device.firmware_version:
            db_device.firmware_version = device.firmware_version
        
        if device.device_metadata:
            db_device.device_metadata = device.device_metadata
        
        db.commit()
        db.refresh(db_device)
        
        return {
            "success": True,
            "message": f"Gerät mit ID {device_id} aktualisiert",
            "device_id": db_device.id,
            "updated": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren des Geräts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{device_id}", response_model=schemas.DeviceResponse)
def delete_device(device_id: str, db: Session = Depends(get_db)):
    """
    Löscht ein Gerät.
    """
    try:
        db_device = db.query(models.Device).filter(models.Device.id == device_id).first()
        if db_device is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Gerät mit ID {device_id} nicht gefunden"
            )
        
        db.delete(db_device)
        db.commit()
        
        return {
            "success": True,
            "message": f"Gerät mit ID {device_id} gelöscht",
            "device_id": device_id,
            "updated": False
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Löschen des Geräts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
EOF
success "Geräte-Route erstellt"

# Aktualisiere routes/__init__.py
cat > "$ROUTES_INIT" << 'EOF'
"""
Routen-Paket
----------

Dieses Paket enthält die API-Routen und Endpunkte.
"""

from fastapi import APIRouter

api_router = APIRouter()

# Importiere die Routen-Module
from .devices import router as devices_router
# from .data import router as data_router

# Registriere die Routen
api_router.include_router(devices_router, prefix="/devices", tags=["devices"])
# api_router.include_router(data_router, prefix="/data", tags=["data"])

__all__ = ["api_router"]
EOF
success "routes/__init__.py aktualisiert"

# 9. Erstelle zusätzliche Verzeichnisse für eine vollständige Struktur
info "Erstelle zusätzliche Verzeichnisse für eine vollständige Struktur..."
mkdir -p swissairdry/api/app/utils
mkdir -p swissairdry/api/app/templates
mkdir -p swissairdry/api/app/static/{css,js,images}
success "Zusätzliche Verzeichnisstruktur erstellt"

# 10. Erstelle eine run2.py-Datei, die mit dem Workflow-Skript kompatibel ist
info "Erstelle run2.py für den Workflow..."
cat > "swissairdry/api/app/run2.py" << 'EOF'
#!/usr/bin/env python3
"""
SwissAirDry FastAPI Server
--------------------------

FastAPI-Server für die Haupt-API von SwissAirDry.
"""

import sys
import os
import logging
from pathlib import Path

# Füge das Stammverzeichnis zum Python-Pfad hinzu, damit Module gefunden werden
current_dir = Path(__file__).parent
app_dir = current_dir
api_dir = app_dir.parent
swissairdry_dir = api_dir.parent
repo_dir = swissairdry_dir.parent
sys.path.insert(0, str(repo_dir))
sys.path.insert(0, str(swissairdry_dir))
sys.path.insert(0, str(api_dir))
sys.path.insert(0, str(app_dir))

# Logging-Konfiguration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

logger.info(f"Python-Pfade: {sys.path}")

try:
    from swissairdry.api.app.run import app
    import uvicorn
    
    # Hauptfunktion
    if __name__ == "__main__":
        logger.info("API-Server wird gestartet...")
        
        # Server-Port aus Umgebungsvariablen oder Standardwert
        PORT = int(os.getenv("API_PORT", 5000))
        
        try:
            uvicorn.run(app, host="0.0.0.0", port=PORT)
        except KeyboardInterrupt:
            logger.info("API-Server wurde vom Benutzer gestoppt")
        except Exception as server_error:
            logger.error(f"Serverfehler: {str(server_error)}")
            raise
        
except Exception as import_error:
    logger.error(f"Fehler beim Importieren der API-Module: {str(import_error)}")
    logger.error("Details:", exc_info=True)
    
    # Erstelle trotzdem eine minimale API
    from fastapi import FastAPI
    import uvicorn
    
    app = FastAPI(
        title="SwissAirDry API (Notfallmodus)",
        description="Minimale API im Notfallmodus",
        version="1.0.0"
    )
    
    @app.get("/")
    async def root():
        """Startseite"""
        return {
            "message": "SwissAirDry API im Notfallmodus",
            "error": str(import_error)
        }
    
    @app.get("/api/status")
    async def status():
        """API-Status"""
        return {
            "status": "error",
            "error": str(import_error),
            "version": "1.0.0"
        }
    
    # Starte Server im Notfallmodus
    if __name__ == "__main__":
        logger.warning("API-Server wird im Notfallmodus gestartet...")
        
        # Server-Port aus Umgebungsvariablen oder Standardwert
        PORT = int(os.getenv("API_PORT", 5000))
        
        uvicorn.run(app, host="0.0.0.0", port=PORT)
EOF
chmod +x "swissairdry/api/app/run2.py"
success "run2.py für den Workflow erstellt"

# 11. Aktualisiere oder erstelle eine kompatible Dockerfile
info "Aktualisiere oder erstelle eine kompatible Dockerfile..."
DOCKERFILE="swissairdry/api/Dockerfile"
mkdir -p $(dirname "$DOCKERFILE")
cat > "$DOCKERFILE" << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Installiere Abhängigkeiten
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Kopiere requirements.txt
COPY requirements.api.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere Anwendungsdateien
COPY app/ app/

# Setze Umgebungsvariablen
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Lege Port frei
EXPOSE 5000

# Starte die Anwendung
CMD ["python", "app/run2.py"]
EOF
success "Dockerfile erstellt"

# Erstelle requirements.api.txt, falls nicht vorhanden
REQUIREMENTS="swissairdry/api/requirements.api.txt"
mkdir -p $(dirname "$REQUIREMENTS")
cat > "$REQUIREMENTS" << 'EOF'
fastapi==0.109.2
uvicorn==0.27.1
pydantic==2.5.2
paho-mqtt==1.6.1
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
python-multipart==0.0.9
python-dotenv==1.0.1
httpx==0.25.2
jinja2==3.1.3
EOF
success "requirements.api.txt erstellt"

echo ""
success "API-Fehlersuche und -behebung abgeschlossen"
echo ""
info "Was wurde erledigt:"
echo " - Namenskonflikt mit 'metadata' in device.py behoben (falls vorhanden)"
echo " - Vollständige, fehlertolerante database.py erstellt"
echo " - Notwendige __init__.py-Dateien erstellt/aktualisiert"
echo " - Verbesserte run.py mit umfassender Fehlerbehandlung erstellt"
echo " - run2.py für den Workflow erstellt, mit Notfallmodus"
echo " - Grundlegende Schemas und Routen erstellt"
echo " - Dockerfile und requirements.api.txt aktualisiert"
echo ""
info "Nächste Schritte:"
echo " 1. Starten Sie die API mit: cd swissairdry/api/app && python run2.py"
echo " 2. Verwenden Sie den Workflow: RESTARTEN Sie 'SwissAirDry API' im Replit-Workflow"
echo " 3. Testen Sie die API mit: curl http://localhost:5000/api/status"
echo ""