"""
SwissAirDry API - OpenAPI-Konfiguration

Diese Datei konfiguriert die OpenAPI/Swagger-Dokumentation für die SwissAirDry API.

@author Swiss Air Dry Team <info@swissairdry.com>
@copyright 2023-2025 Swiss Air Dry Team
"""

# OpenAPI/Swagger-Konfiguration
swagger_config = {
    "title": "SwissAirDry API",
    "description": """
    ## API für die Verwaltung von SwissAirDry-Geräten und -Daten
    
    Diese API erlaubt die Verwaltung von Luftentfeuchtern, Sensordaten, Kunden und Aufträgen.
    Sie ist für die Integration mit Frontend-Anwendungen und IoT-Geräten konzipiert.
    
    ### Authentifizierung
    
    Die API unterstützt Authentifizierung über API-Schlüssel. Der API-Schlüssel muss in allen 
    Anfragen im HTTP-Header `X-API-Key` mitgegeben werden.
    
    ### MQTT-Integration
    
    Die API integriert MQTT für Echtzeit-Kommunikation mit Geräten. Befehle können über 
    den `/api/device/{device_id}/command`-Endpunkt gesendet werden und werden über MQTT 
    an die Geräte weitergeleitet.
    
    ### Weitere Informationen
    
    Eine ausführliche Dokumentation finden Sie unter `/api/docs/API_DOCUMENTATION.md`.
    """,
    "version": "1.0.0",
    "openapi_version": "3.0.2",
    "contact": {
        "name": "Swiss Air Dry Team",
        "url": "https://www.swissairdry.com",
        "email": "info@swissairdry.com",
    },
    "license_info": {
        "name": "Proprietary",
        "url": "https://www.swissairdry.com/license",
    },
    "terms_of_service": "https://www.swissairdry.com/terms",
    "servers": [
        {
            "url": "https://api.vgnc.org/v1",
            "description": "Produktionsserver",
        },
        {
            "url": "http://localhost:5000",
            "description": "Lokaler Entwicklungsserver",
        },
    ],
    "tags": [
        {
            "name": "Geräte",
            "description": "Endpunkte zur Verwaltung von Geräten",
        },
        {
            "name": "Sensordaten",
            "description": "Endpunkte zur Verwaltung von Sensordaten",
        },
        {
            "name": "Kunden",
            "description": "Endpunkte zur Verwaltung von Kunden",
        },
        {
            "name": "Aufträge",
            "description": "Endpunkte zur Verwaltung von Aufträgen",
        },
        {
            "name": "System",
            "description": "Systemendpunkte (Status, Gesundheit, etc.)",
        },
    ],
    "security": [
        {
            "APIKeyHeader": [],
        }
    ],
    "components": {
        "securitySchemes": {
            "APIKeyHeader": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API-Schlüssel für die Authentifizierung",
            }
        }
    },
    "externalDocs": {
        "description": "SwissAirDry Dokumentation",
        "url": "https://docs.swissairdry.com",
    },
}


# Beispielcode zur Integration der OpenAPI-Konfiguration in die FastAPI-App:
"""
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from .docs.openapi_config import swagger_config

app = FastAPI()

@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    return get_openapi(
        title=swagger_config["title"],
        version=swagger_config["version"],
        description=swagger_config["description"],
        routes=app.routes,
        tags=swagger_config["tags"],
        servers=swagger_config["servers"],
        terms_of_service=swagger_config["terms_of_service"],
        contact=swagger_config["contact"],
        license_info=swagger_config["license_info"],
    )

@app.get("/docs", include_in_schema=False)
async def get_documentation():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{swagger_config['title']} - Dokumentation",
    )
"""