#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests für die API-Endpunkte des SwissAirDry-Projekts
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# FastAPI-App importieren
from swissairdry.api.app.run2 import app


@pytest.fixture
def client():
    """Test-Client für die FastAPI-App"""
    return TestClient(app)


class TestAPIEndpoints:
    """Testklasse für die API-Endpunkte"""

    def test_root_endpoint(self, client):
        """Testet den Root-Endpunkt"""
        response = client.get("/")
        
        assert response.status_code == 200
        assert "version" in response.json()
        assert "name" in response.json()
        assert response.json()["name"] == "SwissAirDry API"

    def test_health_endpoint(self, client):
        """Testet den Health-Check-Endpunkt"""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    @patch("swissairdry.api.app.routes.devices.get_all_devices")
    def test_get_devices(self, mock_get_all_devices, client):
        """Testet den Endpunkt zum Abrufen aller Geräte"""
        # Mock-Daten für den Test
        mock_devices = [
            {"id": "device1", "name": "Testgerät 1", "type": "dehumidifier"},
            {"id": "device2", "name": "Testgerät 2", "type": "sensor"}
        ]
        
        # Mock konfigurieren
        mock_get_all_devices.return_value = mock_devices
        
        # API-Endpunkt testen
        response = client.get("/api/devices")
        
        # Assertions
        assert response.status_code == 200
        assert response.json() == mock_devices

    @patch("swissairdry.api.app.routes.devices.get_device_by_id")
    def test_get_device_by_id(self, mock_get_device_by_id, client):
        """Testet den Endpunkt zum Abrufen eines Geräts anhand seiner ID"""
        # Mock-Daten für den Test
        mock_device = {
            "id": "device1",
            "name": "Testgerät 1",
            "type": "dehumidifier",
            "status": "active"
        }
        
        # Mock konfigurieren
        mock_get_device_by_id.return_value = mock_device
        
        # API-Endpunkt testen
        response = client.get("/api/devices/device1")
        
        # Assertions
        assert response.status_code == 200
        assert response.json() == mock_device
        
        # Testen, wenn das Gerät nicht gefunden wird
        mock_get_device_by_id.return_value = None
        response = client.get("/api/devices/nonexistent")
        assert response.status_code == 404