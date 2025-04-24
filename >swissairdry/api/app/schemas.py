"""
Schemas für die SwissAirDry API.

Diese Datei enthält die Pydantic-Schemas für die API-Endpunkte.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from pydantic import BaseModel, Field, validator


class DeviceBase(BaseModel):
    """Basisschema für Geräte."""
    name: str = Field(..., description="Name des Geräts")
    type: str = Field(..., description="Typ des Geräts (z.B. dehumidifier, fan)")
    location: Optional[str] = Field(None, description="Standort des Geräts")
    status: str = Field("inactive", description="Status des Geräts (active, inactive, warning, alarm)")


class DeviceCreate(DeviceBase):
    """Schema für die Erstellung eines neuen Geräts."""
    serial_number: str = Field(..., description="Seriennummer des Geräts")
    mac_address: Optional[str] = Field(None, description="MAC-Adresse des Geräts")
    firmware_version: Optional[str] = Field(None, description="Firmware-Version des Geräts")


class DeviceUpdate(BaseModel):
    """Schema für die Aktualisierung eines vorhandenen Geräts."""
    name: Optional[str] = Field(None, description="Name des Geräts")
    type: Optional[str] = Field(None, description="Typ des Geräts")
    location: Optional[str] = Field(None, description="Standort des Geräts")
    status: Optional[str] = Field(None, description="Status des Geräts")
    firmware_version: Optional[str] = Field(None, description="Firmware-Version des Geräts")
    last_update: Optional[datetime] = Field(None, description="Zeitpunkt der letzten Aktualisierung")


class DeviceResponse(DeviceBase):
    """Antwortschema für Gerätedaten."""
    id: str = Field(..., description="ID des Geräts")
    serial_number: str = Field(..., description="Seriennummer des Geräts")
    mac_address: Optional[str] = Field(None, description="MAC-Adresse des Geräts")
    firmware_version: Optional[str] = Field(None, description="Firmware-Version des Geräts")
    last_update: datetime = Field(..., description="Zeitpunkt der letzten Aktualisierung")
    created_at: datetime = Field(..., description="Zeitpunkt der Erstellung")

    class Config:
        from_attributes = True


class DeviceOverview(BaseModel):
    """Schema für die Geräteübersicht."""
    id: str = Field(..., description="ID des Geräts")
    name: str = Field(..., description="Name des Geräts")
    type: str = Field(..., description="Typ des Geräts")
    status: str = Field(..., description="Status des Geräts")
    last_update: datetime = Field(..., description="Zeitpunkt der letzten Aktualisierung")
    telemetry: Optional[Dict[str, Any]] = Field(None, description="Neueste Telemetriedaten")


class DeviceDetailResponse(DeviceResponse):
    """Detailliertes Antwortschema für Gerätedaten mit Sensor- und Alarminformationen."""
    sensors: Optional[List[Dict[str, Any]]] = Field(None, description="Liste der neuesten Sensordaten")
    alarms: Optional[List[Dict[str, Any]]] = Field(None, description="Liste der aktiven Alarme")
    config: Optional[Dict[str, Any]] = Field(None, description="Gerätekonfiguration")


class SensorBase(BaseModel):
    """Basisschema für Sensordaten."""
    device_id: str = Field(..., description="ID des zugehörigen Geräts")
    temperature: Optional[float] = Field(None, description="Temperatur in °C")
    humidity: Optional[float] = Field(None, description="Luftfeuchtigkeit in %")
    pressure: Optional[float] = Field(None, description="Luftdruck in hPa")
    battery_level: Optional[float] = Field(None, description="Batteriestand in %")
    power_consumption: Optional[float] = Field(None, description="Energieverbrauch in Watt")
    water_level: Optional[float] = Field(None, description="Wasserstand in %")
    water_extracted: Optional[float] = Field(None, description="Extrahierte Wassermenge in Litern")
    airflow: Optional[float] = Field(None, description="Luftstrom in m³/h")
    runtime: Optional[int] = Field(None, description="Laufzeit in Minuten")
    error_code: Optional[int] = Field(None, description="Fehlercode (0 = kein Fehler)")
    custom_data: Optional[Dict[str, Any]] = Field(None, description="Benutzerdefinierte Sensordaten")


class SensorCreate(SensorBase):
    """Schema für die Erstellung neuer Sensordaten."""
    timestamp: Optional[datetime] = Field(None, description="Zeitpunkt der Messung")


class SensorResponse(SensorBase):
    """Antwortschema für Sensordaten."""
    id: str = Field(..., description="ID des Sensordatensatzes")
    timestamp: datetime = Field(..., description="Zeitpunkt der Messung")
    created_at: datetime = Field(..., description="Zeitpunkt der Erstellung")

    class Config:
        from_attributes = True


class AlarmBase(BaseModel):
    """Basisschema für Alarme."""
    device_id: str = Field(..., description="ID des zugehörigen Geräts")
    title: str = Field(..., description="Titel des Alarms")
    description: str = Field(..., description="Beschreibung des Alarms")
    severity: str = Field(..., description="Schweregrad des Alarms (critical, high, medium, low)")
    status: str = Field("open", description="Status des Alarms (open, acknowledged, resolved)")


class AlarmCreate(AlarmBase):
    """Schema für die Erstellung eines neuen Alarms."""
    timestamp: Optional[datetime] = Field(None, description="Zeitpunkt des Alarms")
    custom_data: Optional[Dict[str, Any]] = Field(None, description="Benutzerdefinierte Alarmdaten")


class AlarmUpdate(BaseModel):
    """Schema für die Aktualisierung eines vorhandenen Alarms."""
    title: Optional[str] = Field(None, description="Titel des Alarms")
    description: Optional[str] = Field(None, description="Beschreibung des Alarms")
    severity: Optional[str] = Field(None, description="Schweregrad des Alarms")
    status: Optional[str] = Field(None, description="Status des Alarms")
    resolved_by: Optional[str] = Field(None, description="Benutzer, der den Alarm behoben hat")
    resolved_at: Optional[datetime] = Field(None, description="Zeitpunkt der Behebung des Alarms")
    custom_data: Optional[Dict[str, Any]] = Field(None, description="Benutzerdefinierte Alarmdaten")


class AlarmResponse(AlarmBase):
    """Antwortschema für Alarme."""
    id: str = Field(..., description="ID des Alarms")
    timestamp: datetime = Field(..., description="Zeitpunkt des Alarms")
    created_at: datetime = Field(..., description="Zeitpunkt der Erstellung")
    acknowledged_by: Optional[str] = Field(None, description="Benutzer, der den Alarm bestätigt hat")
    acknowledged_at: Optional[datetime] = Field(None, description="Zeitpunkt der Bestätigung des Alarms")
    resolved_by: Optional[str] = Field(None, description="Benutzer, der den Alarm behoben hat")
    resolved_at: Optional[datetime] = Field(None, description="Zeitpunkt der Behebung des Alarms")
    custom_data: Optional[Dict[str, Any]] = Field(None, description="Benutzerdefinierte Alarmdaten")

    class Config:
        from_attributes = True


class AlarmOverview(BaseModel):
    """Schema für die Alarmübersicht."""
    id: str = Field(..., description="ID des Alarms")
    title: str = Field(..., description="Titel des Alarms")
    description: str = Field(..., description="Beschreibung des Alarms")
    severity: str = Field(..., description="Schweregrad des Alarms")
    device_id: str = Field(..., description="ID des zugehörigen Geräts")
    timestamp: datetime = Field(..., description="Zeitpunkt des Alarms")
    status: str = Field(..., description="Status des Alarms")


class JobBase(BaseModel):
    """Basisschema für Jobs."""
    title: str = Field(..., description="Titel des Jobs")
    description: Optional[str] = Field(None, description="Beschreibung des Jobs")
    status: str = Field("pending", description="Status des Jobs (pending, in_progress, completed, cancelled)")
    priority: str = Field("medium", description="Priorität des Jobs (high, medium, low)")
    customer_id: Optional[str] = Field(None, description="ID des Kunden")
    location: Optional[str] = Field(None, description="Ort des Jobs")
    scheduled_start: Optional[datetime] = Field(None, description="Geplanter Starttermin")
    scheduled_end: Optional[datetime] = Field(None, description="Geplanter Endtermin")


class JobCreate(JobBase):
    """Schema für die Erstellung eines neuen Jobs."""
    devices: Optional[List[str]] = Field(None, description="Liste der zugehörigen Geräte-IDs")
    custom_data: Optional[Dict[str, Any]] = Field(None, description="Benutzerdefinierte Jobdaten")


class JobUpdate(BaseModel):
    """Schema für die Aktualisierung eines vorhandenen Jobs."""
    title: Optional[str] = Field(None, description="Titel des Jobs")
    description: Optional[str] = Field(None, description="Beschreibung des Jobs")
    status: Optional[str] = Field(None, description="Status des Jobs")
    priority: Optional[str] = Field(None, description="Priorität des Jobs")
    customer_id: Optional[str] = Field(None, description="ID des Kunden")
    location: Optional[str] = Field(None, description="Ort des Jobs")
    scheduled_start: Optional[datetime] = Field(None, description="Geplanter Starttermin")
    scheduled_end: Optional[datetime] = Field(None, description="Geplanter Endtermin")
    actual_start: Optional[datetime] = Field(None, description="Tatsächlicher Starttermin")
    actual_end: Optional[datetime] = Field(None, description="Tatsächlicher Endtermin")
    devices: Optional[List[str]] = Field(None, description="Liste der zugehörigen Geräte-IDs")
    custom_data: Optional[Dict[str, Any]] = Field(None, description="Benutzerdefinierte Jobdaten")


class JobResponse(JobBase):
    """Antwortschema für Jobs."""
    id: str = Field(..., description="ID des Jobs")
    created_at: datetime = Field(..., description="Zeitpunkt der Erstellung")
    updated_at: datetime = Field(..., description="Zeitpunkt der letzten Aktualisierung")
    created_by: str = Field(..., description="Ersteller des Jobs")
    assigned_to: Optional[str] = Field(None, description="Zugewiesener Benutzer")
    actual_start: Optional[datetime] = Field(None, description="Tatsächlicher Starttermin")
    actual_end: Optional[datetime] = Field(None, description="Tatsächlicher Endtermin")
    devices: List[str] = Field([], description="Liste der zugehörigen Geräte-IDs")
    custom_data: Optional[Dict[str, Any]] = Field(None, description="Benutzerdefinierte Jobdaten")

    class Config:
        from_attributes = True


class JobDetailResponse(JobResponse):
    """Detailliertes Antwortschema für Jobs mit Geräte- und Alarminformationen."""
    devices_data: Optional[List[DeviceOverview]] = Field(None, description="Details zu den zugehörigen Geräten")
    alarms: Optional[List[AlarmOverview]] = Field(None, description="Liste der aktiven Alarme für diese Geräte")


class ReportBase(BaseModel):
    """Basisschema für Berichte."""
    job_id: str = Field(..., description="ID des zugehörigen Jobs")
    title: str = Field(..., description="Titel des Berichts")
    content: str = Field(..., description="Inhalt des Berichts")
    report_type: str = Field("standard", description="Typ des Berichts (standard, detailed, summary)")


class ReportCreate(ReportBase):
    """Schema für die Erstellung eines neuen Berichts."""
    attachments: Optional[List[str]] = Field(None, description="Liste der Anhänge (z.B. Dateipfade)")
    custom_data: Optional[Dict[str, Any]] = Field(None, description="Benutzerdefinierte Berichtsdaten")


class ReportUpdate(BaseModel):
    """Schema für die Aktualisierung eines vorhandenen Berichts."""
    title: Optional[str] = Field(None, description="Titel des Berichts")
    content: Optional[str] = Field(None, description="Inhalt des Berichts")
    report_type: Optional[str] = Field(None, description="Typ des Berichts")
    attachments: Optional[List[str]] = Field(None, description="Liste der Anhänge")
    custom_data: Optional[Dict[str, Any]] = Field(None, description="Benutzerdefinierte Berichtsdaten")


class ReportResponse(ReportBase):
    """Antwortschema für Berichte."""
    id: str = Field(..., description="ID des Berichts")
    created_at: datetime = Field(..., description="Zeitpunkt der Erstellung")
    updated_at: datetime = Field(..., description="Zeitpunkt der letzten Aktualisierung")
    created_by: str = Field(..., description="Ersteller des Berichts")
    attachments: List[str] = Field([], description="Liste der Anhänge")
    custom_data: Optional[Dict[str, Any]] = Field(None, description="Benutzerdefinierte Berichtsdaten")

    class Config:
        from_attributes = True


class MQTTMessage(BaseModel):
    """Schema für MQTT-Nachrichten."""
    topic: str = Field(..., description="MQTT-Topic")
    payload: Dict[str, Any] = Field(..., description="MQTT-Payload")
    qos: int = Field(0, description="Quality of Service (0, 1, 2)")
    retain: bool = Field(False, description="Retain-Flag")


class MQTTCommand(BaseModel):
    """Schema für MQTT-Befehle an Geräte."""
    device_id: str = Field(..., description="ID des Zielgeräts")
    command: str = Field(..., description="Befehl (z.B. power_on, power_off, set_target)")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Befehlsparameter")


class SystemStatusResponse(BaseModel):
    """Antwortschema für den Systemstatus."""
    api: bool = Field(..., description="Status der API")
    mqtt: bool = Field(..., description="Status der MQTT-Verbindung")
    deck: Dict[str, Any] = Field(..., description="Status der Deck-Integration")
    update_time: datetime = Field(..., description="Zeitpunkt der Aktualisierung")


class DeckStatusResponse(BaseModel):
    """Antwortschema für den Status der Deck-Integration."""
    available: bool = Field(..., description="Verfügbarkeit der Deck-API")
    initialized: bool = Field(..., description="Initialisierungsstatus der Deck-Integration")
    message: Optional[str] = Field(None, description="Statusinformationen oder Fehlermeldungen")
    boards: Optional[List[Dict[str, Any]]] = Field(None, description="Liste der verfügbaren Boards")


class DashboardResponse(BaseModel):
    """Antwortschema für das Dashboard."""
    devices: Dict[str, Any] = Field(..., description="Gerätedaten und -statistiken")
    alarms: Dict[str, Any] = Field(..., description="Alarmdaten und -statistiken")
    status: Dict[str, Any] = Field(..., description="Systemstatus")
    update_time: datetime = Field(..., description="Zeitpunkt der Aktualisierung")


class ErrorResponse(BaseModel):
    """Antwortschema für Fehler."""
    detail: str = Field(..., description="Fehlermeldung")
    status_code: int = Field(..., description="HTTP-Statuscode")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Zeitpunkt des Fehlers")