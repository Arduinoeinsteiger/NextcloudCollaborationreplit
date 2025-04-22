#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SwissAirDry Nextcloud Deck Integration
--------------------------------------

Diese Datei enthält die Integrationslogik zwischen SwissAirDry und der Nextcloud Deck App.
Sie stellt den Service bereit, der Aufträge, Geräte und Aufgaben mit Boards, Stacks und Karten
in der Nextcloud Deck App synchronisiert.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union

from .client import DeckAPIClient, DeckAPIException

# Logger konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("swissairdry_deck_integration")


class SwissAirDryDeckIntegration:
    """
    Integration zwischen SwissAirDry und Nextcloud Deck
    
    Diese Klasse orchestriert die Integration von SwissAirDry-Daten mit der Nextcloud Deck App.
    Sie synchronisiert Aufträge, Geräte und Aufgaben mit Boards, Stacks und Karten in Deck.
    """
    
    DEFAULT_STACKS = ["In Vorbereitung", "In Bearbeitung", "Abgeschlossen", "Probleme"]
    STACK_COLORS = {
        "In Vorbereitung": "0082c9",   # Blau
        "In Bearbeitung": "ffa500",    # Orange
        "Abgeschlossen": "49b675",     # Grün
        "Probleme": "e9322d"           # Rot
    }
    
    def __init__(self, nextcloud_url: str, username: str, password: str):
        """
        Initialisiere die SwissAirDry-Deck Integration
        
        Args:
            nextcloud_url: Die Basis-URL der Nextcloud-Instanz
            username: Benutzername für die Authentifizierung
            password: Passwort oder App-Passwort für die Authentifizierung
        """
        self.deck_client = DeckAPIClient(nextcloud_url, username, password)
        self.board_cache = {}  # Cache für Board-Daten
        
        # Prüfen, ob ein Hauptboard für SwissAirDry existiert, sonst anlegen
        self.main_board_id = self._get_or_create_main_board()
        logger.info(f"SwissAirDry Hauptboard ID: {self.main_board_id}")
    
    def _get_or_create_main_board(self) -> int:
        """
        Hole oder erstelle das SwissAirDry Hauptboard
        
        Returns:
            Die ID des Hauptboards
        """
        BOARD_TITLE = "SwissAirDry"
        
        # Alle Boards abrufen und nach dem SwissAirDry-Board suchen
        boards = self.deck_client.get_all_boards()
        for board in boards:
            if board["title"] == BOARD_TITLE:
                logger.info(f"Bestehendes SwissAirDry-Board gefunden: ID {board['id']}")
                
                # Standard-Stacks überprüfen und ggf. erstellen
                self._ensure_default_stacks(board["id"])
                
                return board["id"]
        
        # Wenn nicht gefunden, neues Board erstellen
        logger.info("Kein SwissAirDry-Board gefunden, erstelle ein neues...")
        board = self.deck_client.create_board(BOARD_TITLE, color="0082c9")
        board_id = board["id"]
        
        # Standard-Stacks erstellen
        self._ensure_default_stacks(board_id)
        
        return board_id
    
    def _ensure_default_stacks(self, board_id: int) -> None:
        """
        Stelle sicher, dass alle Standard-Stacks im Board vorhanden sind
        
        Args:
            board_id: ID des Boards
        """
        # Vorhandene Stacks abrufen
        existing_stacks = self.deck_client.get_stacks(board_id)
        existing_stack_titles = [stack["title"] for stack in existing_stacks]
        
        # Fehlende Stacks erstellen
        for stack_title in self.DEFAULT_STACKS:
            if stack_title not in existing_stack_titles:
                logger.info(f"Erstelle Stack '{stack_title}' im Board {board_id}")
                self.deck_client.create_stack(board_id, stack_title)
    
    def get_stack_id_by_title(self, board_id: int, title: str) -> Optional[int]:
        """
        Hole die ID eines Stacks anhand seines Titels
        
        Args:
            board_id: ID des Boards
            title: Titel des Stacks
            
        Returns:
            Die ID des Stacks oder None, wenn nicht gefunden
        """
        stacks = self.deck_client.get_stacks(board_id)
        for stack in stacks:
            if stack["title"] == title:
                return stack["id"]
        return None
    
    def create_job_board(self, job_id: str, job_title: str, customer_name: str) -> int:
        """
        Erstelle ein neues Board für einen Auftrag
        
        Args:
            job_id: ID des Auftrags
            job_title: Titel des Auftrags
            customer_name: Name des Kunden
            
        Returns:
            Die ID des erstellten Boards
        """
        board_title = f"{job_id} - {customer_name}"
        board = self.deck_client.create_board(board_title, color="0082c9")
        board_id = board["id"]
        
        # Standard-Stacks für den Auftrag erstellen
        self._ensure_default_stacks(board_id)
        
        # Auftragsinformationen als Karte im Hauptboard hinzufügen
        main_stack_id = self.get_stack_id_by_title(self.main_board_id, "In Vorbereitung")
        if main_stack_id:
            description = f"""
# Auftrag: {job_title}
* Kunde: {customer_name}
* Auftragsnummer: {job_id}
* Erstellt: {datetime.now().strftime('%Y-%m-%d %H:%M')}

[Zum Auftragsboard](../boards/{board_id})
"""
            self.deck_client.create_card(
                self.main_board_id, 
                main_stack_id, 
                title=board_title, 
                description=description
            )
        
        return board_id
    
    def add_device_card(self, board_id: int, device_id: str, device_name: str, 
                       status: str = "In Vorbereitung") -> int:
        """
        Füge eine Karte für ein Gerät zu einem Auftragsboard hinzu
        
        Args:
            board_id: ID des Auftragsboards
            device_id: ID des Geräts
            device_name: Name des Geräts
            status: Status des Geräts (bestimmt den Stack)
            
        Returns:
            Die ID der erstellten Karte
        """
        stack_id = self.get_stack_id_by_title(board_id, status)
        if not stack_id:
            raise ValueError(f"Stack mit Titel '{status}' nicht gefunden im Board {board_id}")
        
        description = f"""
# Gerät: {device_name}
* Geräte-ID: {device_id}
* Status: {status}
* Hinzugefügt: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Letzte Messwerte:
* Temperatur: -
* Luftfeuchtigkeit: -
* Betriebsstunden: -
"""
        
        card = self.deck_client.create_card(
            board_id, 
            stack_id, 
            title=f"Gerät: {device_name}", 
            description=description
        )
        return card["id"]
    
    def update_device_status(self, board_id: int, card_id: int, source_stack_id: int, 
                           target_status: str, measurement_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Aktualisiere den Status eines Geräts, indem die Karte in einen anderen Stack verschoben wird
        
        Args:
            board_id: ID des Auftragsboards
            card_id: ID der Gerätekarte
            source_stack_id: Aktuelle Stack-ID der Karte
            target_status: Zielstatus (Stack-Titel)
            measurement_data: Optionale Messdaten zum Aktualisieren der Kartenbeschreibung
        """
        # Ziel-Stack finden
        target_stack_id = self.get_stack_id_by_title(board_id, target_status)
        if not target_stack_id:
            raise ValueError(f"Ziel-Stack '{target_status}' nicht gefunden im Board {board_id}")
        
        # Aktuelle Karte abrufen
        card = self.deck_client.get_card(board_id, source_stack_id, card_id)
        
        # Kartenbeschreibung aktualisieren, falls Messdaten vorhanden sind
        description = card["description"]
        if measurement_data:
            # Einfache Ersetzung der Messwerte in der Beschreibung
            # In einer realen Anwendung würde hier eine komplexere Textverarbeitung stattfinden
            if "temperature" in measurement_data:
                description = description.replace("* Temperatur: -", 
                                               f"* Temperatur: {measurement_data['temperature']} °C")
            if "humidity" in measurement_data:
                description = description.replace("* Luftfeuchtigkeit: -", 
                                                f"* Luftfeuchtigkeit: {measurement_data['humidity']} %")
            if "runtime" in measurement_data:
                description = description.replace("* Betriebsstunden: -", 
                                               f"* Betriebsstunden: {measurement_data['runtime']} h")
            
            # Aktualisierungszeitstempel hinzufügen
            description += f"\n\nAktualisiert: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Karte in neuen Stack verschieben
        # Dies erfordert das Löschen der Karte aus dem alten Stack und Neuerstellung im Ziel-Stack
        self.deck_client.delete_card(board_id, source_stack_id, card_id)
        self.deck_client.create_card(
            board_id, 
            target_stack_id, 
            title=card["title"], 
            description=description
        )
    
    def add_task_card(self, board_id: int, task_title: str, task_description: str, 
                    assigned_to: str = None, due_date: datetime = None, 
                    stack_name: str = "In Vorbereitung") -> int:
        """
        Füge eine Aufgabenkarte zu einem Auftragsboard hinzu
        
        Args:
            board_id: ID des Auftragsboards
            task_title: Titel der Aufgabe
            task_description: Beschreibung der Aufgabe
            assigned_to: Name der zugewiesenen Person (optional)
            due_date: Fälligkeitsdatum (optional)
            stack_name: Name des Stacks (Status)
            
        Returns:
            Die ID der erstellten Karte
        """
        stack_id = self.get_stack_id_by_title(board_id, stack_name)
        if not stack_id:
            raise ValueError(f"Stack mit Titel '{stack_name}' nicht gefunden im Board {board_id}")
        
        description = task_description + "\n\n"
        
        if assigned_to:
            description += f"**Zugewiesen an:** {assigned_to}\n"
        
        description += f"**Erstellt:** {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Fälligkeitsdatum formatieren, falls vorhanden
        due_date_str = None
        if due_date:
            due_date_str = due_date.strftime("%Y-%m-%d %H:%M:%S")
        
        card = self.deck_client.create_card(
            board_id, 
            stack_id, 
            title=task_title, 
            description=description,
            due_date=due_date_str
        )
        return card["id"]
    
    def complete_task(self, board_id: int, card_id: int, source_stack_id: int, 
                    completion_note: str = None) -> None:
        """
        Markiere eine Aufgabe als abgeschlossen, indem die Karte in den "Abgeschlossen"-Stack verschoben wird
        
        Args:
            board_id: ID des Auftragsboards
            card_id: ID der Aufgabenkarte
            source_stack_id: Aktuelle Stack-ID der Karte
            completion_note: Optionale Notiz zur Fertigstellung
        """
        target_stack_id = self.get_stack_id_by_title(board_id, "Abgeschlossen")
        if not target_stack_id:
            raise ValueError(f"Stack 'Abgeschlossen' nicht gefunden im Board {board_id}")
        
        # Aktuelle Karte abrufen
        card = self.deck_client.get_card(board_id, source_stack_id, card_id)
        
        # Beschreibung aktualisieren
        description = card["description"]
        description += f"\n\n**Abgeschlossen:** {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        if completion_note:
            description += f"\n\n**Anmerkung:** {completion_note}"
        
        # Karte in "Abgeschlossen"-Stack verschieben
        self.deck_client.delete_card(board_id, source_stack_id, card_id)
        self.deck_client.create_card(
            board_id, 
            target_stack_id, 
            title=card["title"], 
            description=description
        )


# Beispielverwendung
if __name__ == "__main__":
    # Nur zur Demonstration, in der realen Anwendung sollten die Zugangsdaten 
    # aus einer Konfigurationsdatei oder Umgebungsvariablen geladen werden
    NEXTCLOUD_URL = os.environ.get("NEXTCLOUD_URL", "https://cloud.example.com")
    NEXTCLOUD_USER = os.environ.get("NEXTCLOUD_USER", "admin")
    NEXTCLOUD_PASSWORD = os.environ.get("NEXTCLOUD_PASSWORD", "password")
    
    try:
        integration = SwissAirDryDeckIntegration(NEXTCLOUD_URL, NEXTCLOUD_USER, NEXTCLOUD_PASSWORD)
        
        # Beispiel: Neuen Auftrag erstellen
        job_board_id = integration.create_job_board("AUF-2023-042", "Keller Muster AG", "Muster AG")
        print(f"Neues Auftragsboard erstellt mit ID: {job_board_id}")
        
        # Beispiel: Gerät zum Auftrag hinzufügen
        device_card_id = integration.add_device_card(job_board_id, "DEV-123", "Entfeuchter 5000")
        print(f"Neue Gerätekarte erstellt mit ID: {device_card_id}")
        
    except Exception as e:
        print(f"Fehler: {e}")