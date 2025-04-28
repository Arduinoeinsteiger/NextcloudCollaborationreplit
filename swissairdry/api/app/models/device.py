"""
SwissAirDry - Gerätemodelle
---------------------------

Dieses Modul definiert die Datenbankmodelle für Geräte und deren Sensordaten.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, JSON, Boolean
from sqlalchemy.orm import relationship

from swissairdry.api.app.database import Base


class DeviceType(str, PyEnum):
    """Unterstützte Gerätetypen"""
    ESP8266 = "esp8266"
    ESP32 = "esp32"
    STM32 = "stm32"
    OTHER = "other"


class DeviceStatus(str, PyEnum):
    """Gerätestatus-Enum"""
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    UNKNOWN = "unknown"


class CommunicationType(str, PyEnum):
    """Unterstützte Kommunikationstypen"""
    MQTT = "mqtt"
    HTTP = "http"
    BLE = "ble"


class Device(Base):
    """Modell für Geräte in der Datenbank"""
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True)
    device_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    device_type = Column(Enum(DeviceType), nullable=False)
    communication_type = Column(Enum(CommunicationType), nullable=False)
    status = Column(Enum(DeviceStatus), default=DeviceStatus.UNKNOWN)
    location = Column(String(100))
    firmware_version = Column(String(50))
    last_seen = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ip_address = Column(String(50))
    device_metadata = Column(JSON, default={})  # Umbenannt von 'metadata' zu 'device_metadata', um Konflikte mit SQLAlchemy zu vermeiden
    is_active = Column(Boolean, default=True)
    
    # Beziehungen
    sensor_data = relationship("SensorData", back_populates="device", cascade="all, delete-orphan")
    configurations = relationship("DeviceConfiguration", back_populates="device", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Device {self.name} ({self.device_id})>"


class SensorData(Base):
    """Modell für Sensordaten in der Datenbank"""
    __tablename__ = "sensor_data"
    
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Sensor-Werte
    temperature = Column(Float)
    humidity = Column(Float)
    pressure = Column(Float)
    air_quality = Column(Float)
    voltage = Column(Float)
    current = Column(Float)
    power = Column(Float)
    energy = Column(Float)
    rssi = Column(Float)
    
    # Gerätespezifische Daten
    raw_data = Column(JSON, default={})
    
    # Beziehungen
    device = relationship("Device", back_populates="sensor_data")
    
    def __repr__(self):
        return f"<SensorData for device={self.device_id} at {self.timestamp}>"


class DeviceConfiguration(Base):
    """Modell für Gerätekonfigurationen in der Datenbank"""
    __tablename__ = "device_configurations"
    
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    config_key = Column(String(100), nullable=False)
    config_value = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Beziehungen
    device = relationship("Device", back_populates="configurations")
    
    def __repr__(self):
        return f"<DeviceConfiguration {self.config_key}={self.config_value} for device={self.device_id}>"


class DeviceCommand(Base):
    """Modell für Gerätebefehle in der Datenbank"""
    __tablename__ = "device_commands"
    
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    command = Column(String(100), nullable=False)
    parameters = Column(JSON, default={})
    executed = Column(Boolean, default=False)
    result = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime)
    
    device = relationship("Device")
    
    def __repr__(self):
        return f"<DeviceCommand {self.command} for device={self.device_id}>"