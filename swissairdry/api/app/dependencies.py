#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SwissAirDry API - Dependencies
------------------------------

Diese Datei enthält Abhängigkeiten und Factory-Funktionen für die API.
"""

import os
import logging
from typing import Generator, Optional
from functools import lru_cache

from sqlalchemy.orm import Session

from swissairdry import database
from .utils.mqtt_client import MQTTClient

# Externe Integrationen (nur importieren wenn benötigt)
# Die imports werden hier als Variablen definiert, um sie lazy zu laden
# HINWEIS: Die alte Deck-Integration wird durch die ExApp ersetzt
# Die alten Variablen bleiben für Kompatibilität, nutzen aber die neue Implementierung
exapp_integration_module = None
exapp_client_module = None
location_integration_module = None

# Alte Variablennamen für Kompatibilität
deck_integration_module = None
deck_client_module = None

# Logger konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("swissairdry_api")


def get_db() -> Generator[Session, None, None]:
    """
    Factory-Funktion für Datenbankverbindungen
    
    Returns:
        Session: Eine SQLAlchemy-Datenbanksitzung
    """
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_mqtt_client() -> MQTTClient:
    """
    Factory-Funktion für den MQTT-Client
    
    Returns:
        MQTTClient: Eine Instanz des MQTT-Clients
    """
    mqtt_host = os.getenv("MQTT_HOST", "localhost")
    mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
    mqtt_user = os.getenv("MQTT_USER", "")
    mqtt_password = os.getenv("MQTT_PASSWORD", "")
    mqtt_topic_prefix = os.getenv("MQTT_TOPIC_PREFIX", "swissairdry")
    
    return MQTTClient(
        mqtt_host,
        mqtt_port,
        mqtt_user,
        mqtt_password,
        mqtt_topic_prefix
    )


# Lazy-Loading für die Integration-Module
def _load_integration_modules():
    """
    Lade die Nextcloud ExApp Integration Module bei Bedarf
    
    Diese Funktion lädt die neuen ExApp-Module und setzt die alten deck_*-Variablen
    für Kompatibilität mit bestehendem Code.
    """
    global exapp_integration_module, exapp_client_module, location_integration_module
    global deck_integration_module, deck_client_module  # Für Kompatibilität
    
    if exapp_integration_module is None:
        try:
            # Neue ExApp-Module laden
            from swissairdry.integration.exapp import integration as exapp_integration_module
            from swissairdry.integration.exapp import client as exapp_client_module
            from swissairdry.integration.exapp import location_integration as location_integration_module
            
            # Für Kompatibilität alten Variablen zuweisen (werden nicht geladen, nur referenziert)
            deck_integration_module = exapp_integration_module 
            deck_client_module = exapp_client_module
            
            logger.info("Nextcloud ExApp Integration Module geladen")
        except ImportError as e:
            # Fallback auf alte Deck-Module, falls ExApp nicht verfügbar
            try:
                from swissairdry.integration.deck import integration as deck_integration_module
                from swissairdry.integration.deck import client as deck_client_module
                from swissairdry.integration.deck import location_integration as location_integration_module
                
                # Alte Module für neue Variablennamen
                exapp_integration_module = deck_integration_module
                exapp_client_module = deck_client_module
                
                logger.warning("ExApp Module nicht gefunden, Fallback auf alte Deck Integration Module")
            except ImportError as e2:
                logger.error(f"Fehler beim Laden der Integration Module: {e2}")
                raise

# Kompatibilitätsfunktion für alte Aufrufe
def _load_deck_modules():
    """
    Kompatibilitätsfunktion für alte Aufrufe
    """
    _load_integration_modules()


@lru_cache
def get_deck_client():
    """
    Factory-Funktion für den Nextcloud Deck API Client
    
    Returns:
        DeckAPIClient: Eine Instanz des Deck API Clients
    """
    _load_deck_modules()
    
    nextcloud_url = os.getenv("NEXTCLOUD_URL", "")
    nextcloud_user = os.getenv("NEXTCLOUD_USER", "")
    nextcloud_password = os.getenv("NEXTCLOUD_PASSWORD", "")
    
    if not all([nextcloud_url, nextcloud_user, nextcloud_password]):
        logger.warning("Nextcloud-Zugangsdaten nicht vollständig konfiguriert")
        return None
    
    try:
        client = deck_client_module.DeckAPIClient(
            nextcloud_url, 
            nextcloud_user, 
            nextcloud_password
        )
        logger.info(f"Nextcloud Deck API Client erfolgreich initialisiert: {nextcloud_url}")
        return client
    except Exception as e:
        logger.error(f"Fehler beim Initialisieren des Deck API Clients: {e}")
        return None


@lru_cache
def get_deck_integration():
    """
    Factory-Funktion für die Nextcloud Deck Integration
    
    Returns:
        SwissAirDryDeckIntegration: Eine Instanz der Deck Integration
    """
    _load_deck_modules()
    
    nextcloud_url = os.getenv("NEXTCLOUD_URL", "")
    nextcloud_user = os.getenv("NEXTCLOUD_USER", "")
    nextcloud_password = os.getenv("NEXTCLOUD_PASSWORD", "")
    
    if not all([nextcloud_url, nextcloud_user, nextcloud_password]):
        logger.warning("Nextcloud-Zugangsdaten nicht vollständig konfiguriert")
        return None
    
    try:
        integration = deck_integration_module.SwissAirDryDeckIntegration(
            nextcloud_url, 
            nextcloud_user, 
            nextcloud_password
        )
        logger.info("SwissAirDry Deck Integration erfolgreich initialisiert")
        return integration
    except Exception as e:
        logger.error(f"Fehler beim Initialisieren der Deck Integration: {e}")
        return None


@lru_cache
def get_deck_location_integration():
    """
    Factory-Funktion für die Standort-Integration mit Nextcloud Deck
    
    Returns:
        BLELocationDeckIntegration: Eine Instanz der Standort-Integration
    """
    deck_integration = get_deck_integration()
    if not deck_integration:
        logger.warning("Basis-Deck-Integration nicht verfügbar, Standort-Integration kann nicht initialisiert werden")
        return None
    
    try:
        location_integration = location_integration_module.BLELocationDeckIntegration(deck_integration)
        logger.info("BLE Standort-Integration mit Deck erfolgreich initialisiert")
        return location_integration
    except Exception as e:
        logger.error(f"Fehler beim Initialisieren der Standort-Integration: {e}")
        return None