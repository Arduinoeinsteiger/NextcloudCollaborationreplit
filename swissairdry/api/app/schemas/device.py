"""
SwissAirDry - Geräteschemas
--------------------------

Pydantic-Modelle für die API-Endpunkte zur Verwaltung von Geräten.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from pydantic import BaseModel, Field, validator


class DeviceBase(BaseModel):
    """Basis-Schema für Geräte"""
    device_id: str = Field(..., description="Die eindeutige ID des Geräts")
    name: str = Field(..., description="Der Name des Geräts")
    device_type: str = Field(..., description="Der Typ des Geräts (esp8266, esp32, stm32, other)")
    communication_type: str = Field(..., description="Der Kommunikationstyp (mqtt, http, ble)")
    location: Optional[str] = Field(None, description="Der Standort des Geräts")
    firmware_version: Optional[str] = Field(None, description="Die Firmware-Version des Geräts")
    ip_address: Optional[str] = Field(None, description="Die IP-Adresse des Geräts")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Zusätzliche Metadaten zum Gerät")


class DeviceCreate(DeviceBase):
    """Schema zum Erstellen eines neuen Geräts"""
    pass


class DeviceUpdate(BaseModel):
    """Schema zum Aktualisieren eines vorhandenen Geräts"""
    name: Optional[str] = Field(None, description="Der Name des Geräts")
    location: Optional[str] = Field(None, description="Der Standort des Geräts")
    firmware_version: Optional[str] = Field(None, description="Die Firmware-Version des Geräts")
    ip_address: Optional[str] = Field(None, description="Die IP-Adresse des Geräts")
    status: Optional[str] = Field(None, description="Der Status des Geräts")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Zusätzliche Metadaten zum Gerät")
    is_active: Optional[bool] = Field(None, description="Gibt an, ob das Gerät aktiv ist")


class DeviceResponse(DeviceBase):
    """Schema für die Antwort bei Geräteabfragen"""
    id: int = Field(..., description="Die interne ID des Geräts in der Datenbank")
    status: str = Field(..., description="Der Status des Geräts")
    last_seen: datetime = Field(..., description="Der Zeitpunkt der letzten Aktivität des Geräts")
    created_at: datetime = Field(..., description="Der Zeitpunkt der Erstellung des Geräts")
    updated_at: datetime = Field(..., description="Der Zeitpunkt der letzten Aktualisierung des Geräts")
    is_active: bool = Field(..., description="Gibt an, ob das Gerät aktiv ist")
    
    class Config:
        from_attributes = True


class SensorDataBase(BaseModel):
    """Basis-Schema für Sensordaten"""
    temperature: Optional[float] = Field(None, description="Die Temperatur in °C")
    humidity: Optional[float] = Field(None, description="Die Luftfeuchtigkeit in %")
    pressure: Optional[float] = Field(None, description="Der Luftdruck in hPa")
    air_quality: Optional[float] = Field(None, description="Die Luftqualität (Index)")
    voltage: Optional[float] = Field(None, description="Die Spannung in V")
    current: Optional[float] = Field(None, description="Der Strom in A")
    power: Optional[float] = Field(None, description="Die Leistung in W")
    energy: Optional[float] = Field(None, description="Die Energie in kWh")
    rssi: Optional[float] = Field(None, description="Die Signalstärke in dBm")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Die Rohdaten des Sensors")


class SensorDataCreate(SensorDataBase):
    """Schema zum Erstellen neuer Sensordaten"""
    pass


class SensorDataResponse(SensorDataBase):
    """Schema für die Antwort bei Sensordatenabfragen"""
    id: int = Field(..., description="Die interne ID der Sensordaten in der Datenbank")
    device_id: int = Field(..., description="Die ID des zugehörigen Geräts")
    timestamp: datetime = Field(..., description="Der Zeitpunkt der Messung")
    
    class Config:
        from_attributes = True


class DeviceConfigurationBase(BaseModel):
    """Basis-Schema für Gerätekonfigurationen"""
    config_key: str = Field(..., description="Der Schlüssel der Konfiguration")
    config_value: str = Field(..., description="Der Wert der Konfiguration")


class DeviceConfigurationCreate(DeviceConfigurationBase):
    """Schema zum Erstellen einer neuen Gerätekonfiguration"""
    pass


class DeviceConfigurationResponse(DeviceConfigurationBase):
    """Schema für die Antwort bei Gerätekonfigurationsabfragen"""
    id: int = Field(..., description="Die interne ID der Konfiguration in der Datenbank")
    device_id: int = Field(..., description="Die ID des zugehörigen Geräts")
    created_at: datetime = Field(..., description="Der Zeitpunkt der Erstellung der Konfiguration")
    updated_at: datetime = Field(..., description="Der Zeitpunkt der letzten Aktualisierung der Konfiguration")
    
    class Config:
        from_attributes = True


class DeviceCommandBase(BaseModel):
    """Basis-Schema für Gerätebefehle"""
    command: str = Field(..., description="Der Befehl, der an das Gerät gesendet werden soll")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Die Parameter des Befehls")


class DeviceCommandCreate(DeviceCommandBase):
    """Schema zum Erstellen eines neuen Gerätebefehls"""
    pass


class DeviceCommandResponse(DeviceCommandBase):
    """Schema für die Antwort bei Gerätebefehlsabfragen"""
    id: int = Field(..., description="Die interne ID des Befehls in der Datenbank")
    device_id: int = Field(..., description="Die ID des zugehörigen Geräts")
    executed: bool = Field(..., description="Gibt an, ob der Befehl ausgeführt wurde")
    result: Optional[str] = Field(None, description="Das Ergebnis der Befehlsausführung")
    created_at: datetime = Field(..., description="Der Zeitpunkt der Erstellung des Befehls")
    executed_at: Optional[datetime] = Field(None, description="Der Zeitpunkt der Ausführung des Befehls")
    
    class Config:
        from_attributes = True


# STM32-spezifische Schemas

class STM32DeviceRegister(BaseModel):
    """Schema zum Registrieren eines STM32-Geräts"""
    device_id: str = Field(..., description="Die eindeutige ID des STM32-Geräts")
    name: str = Field(..., description="Der Name des STM32-Geräts")
    communication_type: Optional[str] = Field("mqtt", description="Der Kommunikationstyp (mqtt, http, ble)")
    location: Optional[str] = Field(None, description="Der Standort des STM32-Geräts")
    firmware_version: Optional[str] = Field(None, description="Die Firmware-Version des STM32-Geräts")
    ip_address: Optional[str] = Field(None, description="Die IP-Adresse des STM32-Geräts")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Zusätzliche Metadaten zum STM32-Gerät")


class STM32DeviceData(BaseModel):
    """Schema für STM32-spezifische Sensordaten"""
    temp: Optional[float] = Field(None, description="Die Temperatur in °C")
    hum: Optional[float] = Field(None, description="Die Luftfeuchtigkeit in %")
    pres: Optional[float] = Field(None, description="Der Luftdruck in hPa")
    volt: Optional[float] = Field(None, description="Die Spannung in V")
    curr: Optional[float] = Field(None, description="Der Strom in A")
    pwr: Optional[float] = Field(None, description="Die Leistung in W")
    e: Optional[float] = Field(None, description="Die Energie in kWh")
    rssi: Optional[float] = Field(None, description="Die Signalstärke in dBm")
    status: Optional[str] = Field(None, description="Der Status des STM32-Geräts")
    raw: Optional[Dict[str, Any]] = Field(None, description="Zusätzliche Rohdaten des STM32-Geräts")