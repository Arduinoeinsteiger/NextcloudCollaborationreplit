"""
SwissAirDry - Datenbankverbindung

Dieser Modul importiert alle Datenbankfunktionalitäten aus dem API-Untermodul,
um sie auf Paketebene verfügbar zu machen. Dies vereinfacht Importe und Tests.

@author Swiss Air Dry Team <info@swissairdry.com>
@copyright 2023-2025 Swiss Air Dry Team
"""

# Alle Datenbankfunktionalitäten aus dem API-Modul importieren
from swissairdry.api.app.database import (
    Base,
    SessionLocal,
    engine,
    get_db,
    SQLALCHEMY_DATABASE_URL,
)

# Exportierte Namen
__all__ = [
    "Base",
    "SessionLocal",
    "engine",
    "get_db",
    "SQLALCHEMY_DATABASE_URL",
]