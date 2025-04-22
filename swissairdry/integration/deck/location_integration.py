#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SwissAirDry Nextcloud Deck BLE Standort-Integration
--------------------------------------------------

Diese Datei erweitert die SwissAirDry Deck Integration um Funktionen zur Visualisierung
von BLE-Standortdaten in Nextcloud Deck Karten.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union

from .integration import SwissAirDryDeckIntegration
from .client import DeckAPIClient, DeckAPIException

# Logger konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("swissairdry_deck_location")


class BLELocationDeckIntegration:
    """
    Integration von BLE-Standortdaten mit Nextcloud Deck
    
    Diese Klasse erweitert die Basisfunktionalität der SwissAirDryDeckIntegration
    um spezifische Funktionen für die Visualisierung und Verwaltung von BLE-Standortdaten.
    """
    
    def __init__(self, deck_integration: SwissAirDryDeckIntegration):
        """
        Initialisiere die BLE-Standort-Integration
        
        Args:
            deck_integration: Eine Instanz der SwissAirDryDeckIntegration
        """
        self.deck_integration = deck_integration
        self.deck_client = deck_integration.deck_client
        self.location_board_id = self._get_or_create_location_board()
        logger.info(f"SwissAirDry Standort-Board ID: {self.location_board_id}")
    
    def _get_or_create_location_board(self) -> int:
        """
        Hole oder erstelle ein spezielles Board für Standortinformationen
        
        Returns:
            Die ID des Standort-Boards
        """
        BOARD_TITLE = "SwissAirDry Geräteverfolgung"
        
        # Alle Boards abrufen und nach dem Standort-Board suchen
        boards = self.deck_client.get_all_boards()
        for board in boards:
            if board["title"] == BOARD_TITLE:
                logger.info(f"Bestehendes Standort-Board gefunden: ID {board['id']}")
                # Stacks überprüfen und ggf. erstellen
                self._ensure_location_stacks(board["id"])
                return board["id"]
        
        # Wenn nicht gefunden, neues Board erstellen
        logger.info("Kein Standort-Board gefunden, erstelle ein neues...")
        board = self.deck_client.create_board(BOARD_TITLE, color="3498db")  # Blau
        board_id = board["id"]
        
        # Standort-Stacks erstellen
        self._ensure_location_stacks(board_id)
        
        return board_id
    
    def _ensure_location_stacks(self, board_id: int) -> None:
        """
        Stelle sicher, dass alle benötigten Stacks für das Standort-Board vorhanden sind
        
        Args:
            board_id: ID des Boards
        """
        # Definition der Stacks für die Standortverfolgung
        location_stacks = [
            "Aktuelle Einsatzorte",
            "Lager/Basis",
            "In Transit",
            "Wartung",
            "Offline"
        ]
        
        # Vorhandene Stacks abrufen
        existing_stacks = self.deck_client.get_stacks(board_id)
        existing_stack_titles = [stack["title"] for stack in existing_stacks]
        
        # Fehlende Stacks erstellen
        for stack_title in location_stacks:
            if stack_title not in existing_stack_titles:
                logger.info(f"Erstelle Stack '{stack_title}' im Board {board_id}")
                self.deck_client.create_stack(board_id, stack_title)
    
    def create_location_card(self, 
                           device_id: str, 
                           device_name: str, 
                           location_name: str,
                           location_description: Optional[str] = None,
                           location_coordinates: Optional[Dict[str, float]] = None,
                           rssi: Optional[int] = None,
                           stack_name: str = "Aktuelle Einsatzorte") -> int:
        """
        Erstelle oder aktualisiere eine Standortkarte für ein Gerät
        
        Args:
            device_id: ID des Geräts
            device_name: Name des Geräts
            location_name: Name des Standorts
            location_description: Beschreibung des Standorts (optional)
            location_coordinates: Geografische Koordinaten (optional)
            rssi: RSSI-Wert der BLE-Verbindung (optional)
            stack_name: Name des Stacks, in dem die Karte erstellt werden soll
            
        Returns:
            Die ID der erstellten oder aktualisierten Karte
        """
        stack_id = self.deck_integration.get_stack_id_by_title(self.location_board_id, stack_name)
        if not stack_id:
            raise ValueError(f"Stack mit Titel '{stack_name}' nicht gefunden im Board {self.location_board_id}")
        
        # Karten im Stack durchsuchen, um zu prüfen, ob bereits eine Karte für dieses Gerät existiert
        cards = self.deck_client.get_cards(self.location_board_id, stack_id)
        existing_card = None
        existing_card_stack_id = None
        
        # In allen Stacks des Boards nach einer Karte für dieses Gerät suchen
        stacks = self.deck_client.get_stacks(self.location_board_id)
        for stack in stacks:
            cards_in_stack = self.deck_client.get_cards(self.location_board_id, stack["id"])
            for card in cards_in_stack:
                # Prüfen, ob der Titel der Karte den device_id enthält
                if device_id in card["title"]:
                    existing_card = card
                    existing_card_stack_id = stack["id"]
                    break
            if existing_card:
                break
        
        # Markdown-Beschreibung für die Karte erstellen
        description = f"""
# {device_name}
* **Geräte-ID:** {device_id}
* **Standort:** {location_name}
"""
        
        if location_description:
            description += f"* **Details:** {location_description}\n"
        
        if location_coordinates:
            lat = location_coordinates.get("latitude")
            lon = location_coordinates.get("longitude")
            if lat and lon:
                description += f"* **Koordinaten:** {lat}, {lon}\n"
                # Google Maps Link hinzufügen
                description += f"* **Karte:** [Google Maps](https://www.google.com/maps/search/?api=1&query={lat},{lon})\n"
                # Link zur integrierten Kartenansicht
                description += f"* **Kartenansicht:** [Integrierte Karte](/map-view?lat={lat}&lon={lon}&device={device_id})\n"
        
        if rssi:
            # RSSI in Signalstärke umrechnen (vereinfacht)
            signal_strength = "Stark" if rssi > -70 else "Mittel" if rssi > -85 else "Schwach"
            description += f"* **Signalstärke:** {signal_strength} ({rssi} dBm)\n"
        
        description += f"\n**Aktualisiert:** {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Wenn eine Karte bereits existiert, diese aktualisieren (löschen und neu erstellen)
        if existing_card:
            logger.info(f"Aktualisiere bestehende Standortkarte für Gerät {device_id}")
            self.deck_client.delete_card(self.location_board_id, existing_card_stack_id, existing_card["id"])
            new_card = self.deck_client.create_card(
                self.location_board_id,
                stack_id,
                title=f"{device_name} ({device_id})",
                description=description
            )
            return new_card["id"]
        else:
            # Neue Karte erstellen
            logger.info(f"Erstelle neue Standortkarte für Gerät {device_id}")
            new_card = self.deck_client.create_card(
                self.location_board_id,
                stack_id,
                title=f"{device_name} ({device_id})",
                description=description
            )
            return new_card["id"]
    
    def update_device_location(self, 
                             device_id: str, 
                             device_name: str,
                             new_location: str,
                             location_description: Optional[str] = None,
                             rssi: Optional[int] = None,
                             coordinates: Optional[Dict[str, float]] = None) -> None:
        """
        Aktualisiere den Standort eines Geräts
        
        Args:
            device_id: ID des Geräts
            device_name: Name des Geräts
            new_location: Neuer Standortname
            location_description: Beschreibung des neuen Standorts (optional)
            rssi: RSSI-Wert der BLE-Verbindung (optional)
            coordinates: Geografische Koordinaten (optional)
        """
        # Bestimme den Stack basierend auf dem Standort oder BLE-Status
        stack_name = "Aktuelle Einsatzorte"
        
        if new_location.lower() == "lager" or new_location.lower() == "basis":
            stack_name = "Lager/Basis"
        elif new_location.lower() == "transport" or new_location.lower() == "transit":
            stack_name = "In Transit"
        elif new_location.lower() == "wartung" or new_location.lower() == "service":
            stack_name = "Wartung"
        elif not rssi or rssi < -90:  # Schwaches oder kein Signal
            stack_name = "Offline"
        
        # Karte erstellen oder aktualisieren
        self.create_location_card(
            device_id=device_id,
            device_name=device_name,
            location_name=new_location,
            location_description=location_description,
            location_coordinates=coordinates,
            rssi=rssi,
            stack_name=stack_name
        )
    
    def mark_device_offline(self, device_id: str, device_name: str, last_seen: Optional[datetime] = None) -> None:
        """
        Markiere ein Gerät als offline
        
        Args:
            device_id: ID des Geräts
            device_name: Name des Geräts
            last_seen: Zeitpunkt der letzten Verbindung (optional)
        """
        last_seen_str = last_seen.strftime('%Y-%m-%d %H:%M') if last_seen else "Unbekannt"
        location_description = f"Gerät ist offline. Zuletzt gesehen: {last_seen_str}"
        
        self.create_location_card(
            device_id=device_id,
            device_name=device_name,
            location_name="Offline",
            location_description=location_description,
            stack_name="Offline"
        )


# Beispielverwendung
if __name__ == "__main__":
    NEXTCLOUD_URL = os.environ.get("NEXTCLOUD_URL", "https://cloud.example.com")
    NEXTCLOUD_USER = os.environ.get("NEXTCLOUD_USER", "admin")
    NEXTCLOUD_PASSWORD = os.environ.get("NEXTCLOUD_PASSWORD", "password")
    
    try:
        # Basis-Integration initialisieren
        base_integration = SwissAirDryDeckIntegration(NEXTCLOUD_URL, NEXTCLOUD_USER, NEXTCLOUD_PASSWORD)
        
        # Standort-Integration initialisieren
        location_integration = BLELocationDeckIntegration(base_integration)
        
        # Beispiel: Standort eines Geräts aktualisieren
        location_integration.update_device_location(
            device_id="SAD_2025042201",
            device_name="SwissAirDry Pro #1",
            new_location="Baustelle XYZ",
            location_description="Raum 2.07, 2. Stock",
            rssi=-65,  # Gutes Signal
            coordinates={"latitude": 47.3769, "longitude": 8.5417}  # Zürich
        )
        
        print("Standort erfolgreich aktualisiert")
        
    except Exception as e:
        print(f"Fehler: {e}")