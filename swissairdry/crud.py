"""
SwissAirDry - CRUD-Operationen

Dieser Modul importiert alle CRUD-Operationen aus dem API-Untermodul,
um sie auf Paketebene verfügbar zu machen. Dies vereinfacht Importe und Tests.

@author Swiss Air Dry Team <info@swissairdry.com>
@copyright 2023-2025 Swiss Air Dry Team
"""

# Alle CRUD-Operationen aus dem API-Modul importieren
from swissairdry.api.app.crud import (
    # Geräte-Operationen
    get_device,
    get_device_by_device_id, 
    get_devices, 
    create_device, 
    update_device, 
    delete_device,
    
    # Sensordaten-Operationen
    get_sensor_data,
    get_sensor_data_by_device,
    create_sensor_data,
    
    # Kunden-Operationen
    get_customer,
    get_customers,
    create_customer,
    update_customer,
    delete_customer,
    get_customer_devices,
    
    # Auftrags-Operationen
    get_job,
    get_jobs,
    create_job,
    update_job,
    delete_job,
    
    # Berichts-Operationen
    get_report,
    get_reports,
    create_report,
    
    # Energiekosten-Operationen
    get_energy_cost,
    get_energy_costs,
    get_current_energy_cost,
    create_energy_cost,
)

# Exportierte Namen
__all__ = [
    # Geräte-Operationen
    "get_device",
    "get_device_by_device_id", 
    "get_devices", 
    "create_device", 
    "update_device", 
    "delete_device",
    
    # Sensordaten-Operationen
    "get_sensor_data",
    "get_sensor_data_by_device",
    "create_sensor_data",
    
    # Kunden-Operationen
    "get_customer",
    "get_customers",
    "create_customer",
    "update_customer",
    "delete_customer",
    "get_customer_devices",
    
    # Auftrags-Operationen
    "get_job",
    "get_jobs",
    "create_job",
    "update_job",
    "delete_job",
    
    # Berichts-Operationen
    "get_report",
    "get_reports",
    "create_report",
    
    # Energiekosten-Operationen
    "get_energy_cost",
    "get_energy_costs",
    "get_current_energy_cost",
    "create_energy_cost",
]