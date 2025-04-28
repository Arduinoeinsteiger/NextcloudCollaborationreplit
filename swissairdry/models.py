"""
SwissAirDry - Datenbankmodelle

Dieser Modul importiert alle Modelle aus dem API-Untermodul, um sie auf Paketebene verfügbar zu machen.
Dies vereinfacht Importe und Tests.

@author Swiss Air Dry Team <info@swissairdry.com>
@copyright 2023-2025 Swiss Air Dry Team
"""

# Alle Modelle aus dem API-Modul importieren
from swissairdry.api.app.models import (
    Device, 
    SensorData, 
    DeviceConfiguration,
    DeviceCommand,
    DeviceType,
    DeviceStatus,
    CommunicationType
)

# Diese Modelle fehlen noch und müssen implementiert werden
# Customer, 
# Job, 
# Report, 
# EnergyCost

# Konstanten und Enum-Klassen für die Modelle
JOB_STATUS_NEW = "new"
JOB_STATUS_IN_PROGRESS = "in_progress"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_CANCELLED = "cancelled"

DEVICE_STATUS_ONLINE = "online"
DEVICE_STATUS_OFFLINE = "offline"
DEVICE_STATUS_ERROR = "error"
DEVICE_STATUS_MAINTENANCE = "maintenance"

# Exportierte Namen
__all__ = [
    "Device", 
    "SensorData", 
    "Customer", 
    "Job", 
    "Report", 
    "EnergyCost",
    "JOB_STATUS_NEW",
    "JOB_STATUS_IN_PROGRESS",
    "JOB_STATUS_COMPLETED",
    "JOB_STATUS_CANCELLED",
    "DEVICE_STATUS_ONLINE",
    "DEVICE_STATUS_OFFLINE",
    "DEVICE_STATUS_ERROR",
    "DEVICE_STATUS_MAINTENANCE"
]