"""
SwissAirDry - Message Schemas
----------------------------

Einfache Nachrichtenschemas für API-Antworten
"""

from typing import Dict, Any, Optional
from swissairdry.api.app.schemas.base import BaseModel, Field


class Message(BaseModel):
    """Einfaches Nachrichtenmodell für API-Antworten"""
    message: str = Field(..., description="Nachrichtentext")
    status: str = Field("success", description="Status der Nachricht (success, error, warning, info)")
    details: Optional[Dict[str, Any]] = Field(None, description="Weitere Details zur Nachricht")