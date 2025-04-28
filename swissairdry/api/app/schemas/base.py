"""
SwissAirDry - Base Schema Classes
---------------------------------

Basisklassen für alle Schemas in der API.
"""

# Einfache Ersatzklasse für Pydantic's BaseModel
class BaseModel:
    """Einfache temporäre Ersatzklasse für Pydantic's BaseModel."""
    
    def __init__(self, **data):
        for key, value in data.items():
            setattr(self, key, value)

# Einfacher Ersatz für Field
def Field(*args, **kwargs):
    """Einfache temporäre Ersatzfunktion für Pydantic's Field."""
    return None