"""
SwissAirDry - Pydantic Schemas

Dieser Modul importiert alle Schemas aus dem API-Untermodul, um sie auf Paketebene verfügbar zu machen.
Dies vereinfacht Importe und Tests.

@author Swiss Air Dry Team <info@swissairdry.com>
@copyright 2023-2025 Swiss Air Dry Team
"""

# Alle Schemas aus dem API-Modul importieren
from swissairdry.api.app.schemas import (
    Message,
    
    # Device Schemas
    DeviceBase,
    DeviceCreate,
    DeviceUpdate,
    Device,
    
    # SensorData Schemas
    SensorDataBase,
    SensorDataCreate,
    SensorData,
    SensorDataResponse,
    
    # Customer Schemas
    CustomerBase,
    CustomerCreate,
    CustomerUpdate,
    Customer,
    
    # Job Schemas
    JobBase,
    JobCreate,
    JobUpdate,
    Job,
    
    # Report Schemas
    ReportBase,
    ReportCreate,
    Report,
    
    # User Schemas
    UserBase,
    UserCreate,
    User,
    
    # Alert Schemas
    AlertBase,
    AlertCreate,
    Alert,
    
    # EnergyCost Schemas
    EnergyCostBase,
    EnergyCostCreate,
    EnergyCost,
    
    # APIKey Schemas
    APIKeyBase,
    APIKeyCreate,
    APIKey,
    
    # DeviceCommand Schema
    DeviceCommand,
)

# Exportierte Namen
__all__ = [
    "Message",
    "DeviceBase",
    "DeviceCreate",
    "DeviceUpdate",
    "Device",
    "SensorDataBase",
    "SensorDataCreate",
    "SensorData",
    "SensorDataResponse",
    "CustomerBase",
    "CustomerCreate",
    "CustomerUpdate",
    "Customer",
    "JobBase",
    "JobCreate",
    "JobUpdate",
    "Job",
    "ReportBase",
    "ReportCreate",
    "Report",
    "UserBase",
    "UserCreate",
    "User",
    "AlertBase",
    "AlertCreate",
    "Alert",
    "EnergyCostBase",
    "EnergyCostCreate",
    "EnergyCost",
    "APIKeyBase",
    "APIKeyCreate",
    "APIKey",
    "DeviceCommand",
]