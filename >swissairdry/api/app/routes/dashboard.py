"""
Dashboard-Routen für den SwissAirDry API-Server.

Diese Datei enthält alle Routen für die Dashboard-Ansicht der SwissAirDry API.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Device, Sensor, Alarm, Job, Report
from app.schemas import (
    DashboardResponse, DeviceOverview, AlarmOverview,
    SystemStatusResponse, DeckStatusResponse
)
from app.services.mqtt_service import MQTTService, get_mqtt_service
from app.services.deck_service import DeckService, get_deck_service

# Logger konfigurieren
logger = logging.getLogger("swissairdry_api")

# Router erstellen
router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    responses={404: {"description": "Nicht gefunden"}},
)


@router.get("/", response_model=DashboardResponse)
async def get_dashboard(
    db: Session = Depends(get_db),
    mqtt_service: MQTTService = Depends(get_mqtt_service),
    deck_service: Optional[DeckService] = Depends(get_deck_service),
    last_hours: int = Query(24, description="Daten der letzten X Stunden anzeigen")
):
    """
    Liefert die Dashboard-Übersicht mit aktuellen Daten.
    """
    try:
        # Zeitraum für Abfragen
        time_threshold = datetime.utcnow() - timedelta(hours=last_hours)

        # Geräteübersicht
        devices_data = db.query(Device).all()
        
        # Nur die neuesten Geräte (maximal 5) für die Vorschau
        recent_devices = (
            db.query(Device)
            .order_by(Device.last_update.desc())
            .limit(5)
            .all()
        )
        
        # Detaillierte Gerätedaten für die Vorschau mit Sensordaten
        devices_preview = []
        for device in recent_devices:
            # Neueste Sensordaten für dieses Gerät
            sensor_data = (
                db.query(Sensor)
                .filter(Sensor.device_id == device.id)
                .order_by(Sensor.timestamp.desc())
                .first()
            )
            
            # Grundlegende Gerätedaten
            device_data = {
                "id": device.id,
                "name": device.name,
                "type": device.type,
                "status": device.status,
                "last_update": device.last_update
            }
            
            # Sensordaten hinzufügen, falls vorhanden
            if sensor_data:
                device_data["telemetry"] = {
                    "temperature": sensor_data.temperature,
                    "humidity": sensor_data.humidity,
                    "pressure": sensor_data.pressure,
                    "battery": sensor_data.battery_level,
                    "last_update": sensor_data.timestamp
                }
            
            devices_preview.append(device_data)
            
        # Geräte nach Status für die Statistiken zählen
        device_counts = {
            "total": len(devices_data),
            "active": sum(1 for d in devices_data if d.status == "active"),
            "inactive": sum(1 for d in devices_data if d.status == "inactive"),
            "warning": sum(1 for d in devices_data if d.status == "warning"),
            "alarm": sum(1 for d in devices_data if d.status == "alarm"),
        }
        
        # Aktuelle Alarme
        recent_alarms = (
            db.query(Alarm)
            .filter(Alarm.timestamp >= time_threshold)
            .order_by(Alarm.timestamp.desc())
            .limit(5)
            .all()
        )
        
        # Alarmstatistiken
        alarm_counts = {
            "total": db.query(Alarm).filter(Alarm.timestamp >= time_threshold).count(),
            "critical": db.query(Alarm).filter(Alarm.severity == "critical", Alarm.timestamp >= time_threshold).count(),
            "high": db.query(Alarm).filter(Alarm.severity == "high", Alarm.timestamp >= time_threshold).count(),
            "medium": db.query(Alarm).filter(Alarm.severity == "medium", Alarm.timestamp >= time_threshold).count(),
            "low": db.query(Alarm).filter(Alarm.severity == "low", Alarm.timestamp >= time_threshold).count(),
        }
        
        # Status der Dienste abrufen
        mqtt_status = mqtt_service.get_status()
        deck_status = deck_service.get_status() if deck_service else {"available": False, "initialized": False}
        
        # Systemstatus zusammenstellen
        system_status = {
            "api": True,  # API ist offensichtlich verfügbar
            "mqtt": mqtt_status.get("connected", False),
            "deck": deck_status
        }
        
        # Alle Daten in der Response zusammenführen
        response = {
            "devices": {
                "overview": device_counts,
                "preview": devices_preview,
            },
            "alarms": {
                "overview": alarm_counts,
                "preview": [
                    {
                        "id": alarm.id,
                        "title": alarm.title,
                        "description": alarm.description,
                        "severity": alarm.severity,
                        "device_id": alarm.device_id,
                        "timestamp": alarm.timestamp,
                        "status": alarm.status
                    }
                    for alarm in recent_alarms
                ],
            },
            "status": system_status,
            "update_time": datetime.utcnow()
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Dashboard-Daten: {e}")
        raise HTTPException(status_code=500, detail=f"Interner Serverfehler: {str(e)}")


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(
    mqtt_service: MQTTService = Depends(get_mqtt_service),
    deck_service: Optional[DeckService] = Depends(get_deck_service),
):
    """
    Liefert den aktuellen Status des Systems.
    """
    try:
        # Status der Dienste abrufen
        mqtt_status = mqtt_service.get_status()
        deck_status = deck_service.get_status() if deck_service else {"available": False, "initialized": False}
        
        # Systemstatus zusammenstellen
        system_status = {
            "api": True,  # API ist offensichtlich verfügbar
            "mqtt": mqtt_status.get("connected", False),
            "deck": deck_status,
            "update_time": datetime.utcnow()
        }
        
        return system_status
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Systemstatus: {e}")
        raise HTTPException(status_code=500, detail=f"Interner Serverfehler: {str(e)}")


@router.get("/deck/status", response_model=DeckStatusResponse)
async def get_deck_status(
    deck_service: Optional[DeckService] = Depends(get_deck_service),
):
    """
    Liefert den aktuellen Status der Deck-Integration.
    """
    if not deck_service:
        return {
            "available": False,
            "initialized": False,
            "message": "Deck-Integration ist nicht konfiguriert"
        }
    
    try:
        status = deck_service.get_status()
        
        if not status.get("available", False):
            return {
                "available": False,
                "initialized": False,
                "message": "Nextcloud Deck API ist nicht erreichbar"
            }
        
        return status
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Deck-Status: {e}")
        return {
            "available": True,
            "initialized": False,
            "message": f"Fehler: {str(e)}"
        }