"""
SwissAirDry API - Datenbankmodelle

@author Swiss Air Dry Team <info@swissairdry.com>
@copyright 2023-2025 Swiss Air Dry Team
"""

import datetime
from typing import List, Optional, Dict, Any

import sqlalchemy
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class Device(Base):
    """
    Modell für Trocknungsgeräte.
    """
    __tablename__ = "devices"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String, index=True)
    status = Column(String, index=True, default="offline")
    last_seen = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    config = Column(JSON, default={})
    meta_data = Column(JSON, default={})  # Umbenannt von metadata zu meta_data, da metadata ein reservierter Name ist

    # Beziehungen
    sensor_data = relationship("SensorData", back_populates="device", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert das Modell in ein Dictionary.
        """
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "status": self.status,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "config": self.config,
            "meta_data": self.meta_data
        }


class SensorData(Base):
    """
    Modell für Sensordaten von Trocknungsgeräten.
    """
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, ForeignKey("devices.id", ondelete="CASCADE"), index=True)
    timestamp = Column(DateTime, default=func.now(), index=True)
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    power = Column(Float, nullable=True)
    energy = Column(Float, nullable=True)
    relay_state = Column(Boolean, nullable=True)
    runtime = Column(Integer, nullable=True)  # Laufzeit in Sekunden
    meta_data = Column(JSON, default={})  # Umbenannt von metadata zu meta_data, da metadata ein reservierter Name ist
    
    # Beziehungen
    device = relationship("Device", back_populates="sensor_data")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert das Modell in ein Dictionary.
        """
        return {
            "id": self.id,
            "device_id": self.device_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "power": self.power,
            "energy": self.energy,
            "relay_state": self.relay_state,
            "runtime": self.runtime,
            "meta_data": self.meta_data
        }