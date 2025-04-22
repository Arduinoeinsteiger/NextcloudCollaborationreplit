#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SwissAirDry Nextcloud Deck API Client
-------------------------------------

Diese Datei enthält den Client für die Nextcloud Deck API Integration.
"""

import os
import json
import requests
import logging
from typing import Dict, List, Optional, Any, Union

# Logger konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("swissairdry_deck")


class DeckAPIException(Exception):
    """Exception für Fehler bei der Kommunikation mit der Deck API"""
    pass


class DeckAPIClient:
    """
    Client für die Nextcloud Deck API
    
    Diese Klasse erlaubt die Interaktion mit der Nextcloud Deck API, um 
    Boards, Stacks (Listen) und Karten zu verwalten.
    """
    
    def __init__(self, base_url: str, username: str, password: str):
        """
        Initialisiere den Deck API Client
        
        Args:
            base_url: Die Basis-URL der Nextcloud-Instanz (z.B. https://cloud.example.com)
            username: Benutzername für die Authentifizierung
            password: Passwort oder App-Passwort für die Authentifizierung
        """
        self.base_url = base_url.rstrip("/")
        self.auth = (username, password)
        self.api_url = f"{self.base_url}/index.php/apps/deck/api/v1.0"
        self.session = requests.Session()
        self.session.auth = self.auth
        
        # Authentifizierung testen
        try:
            self.test_connection()
            logger.info(f"Verbindung zur Deck API auf {base_url} hergestellt")
        except Exception as e:
            logger.error(f"Fehler beim Verbinden zur Deck API: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Teste die Verbindung zur Deck API
        
        Returns:
            bool: True wenn die Verbindung erfolgreich ist
            
        Raises:
            DeckAPIException: Bei Fehlern in der Verbindung
        """
        response = self.session.get(f"{self.api_url}/boards")
        if response.status_code == 200:
            return True
        elif response.status_code == 401:
            raise DeckAPIException("Authentifizierungsfehler bei der Deck API")
        else:
            raise DeckAPIException(f"Fehler beim Verbinden zur Deck API: {response.status_code}, {response.text}")
    
    def get_all_boards(self) -> List[Dict[str, Any]]:
        """
        Hole alle verfügbaren Boards
        
        Returns:
            Liste von Board-Objekten
        """
        response = self.session.get(f"{self.api_url}/boards")
        if response.status_code != 200:
            raise DeckAPIException(f"Fehler beim Abrufen der Boards: {response.status_code}, {response.text}")
        return response.json()
    
    def create_board(self, title: str, color: str = "0082c9") -> Dict[str, Any]:
        """
        Erstelle ein neues Board
        
        Args:
            title: Titel des Boards
            color: Farbe des Boards als Hex-Code (ohne #)
            
        Returns:
            Das erstellte Board-Objekt
        """
        data = {
            "title": title,
            "color": color
        }
        response = self.session.post(f"{self.api_url}/boards", json=data)
        if response.status_code != 200:
            raise DeckAPIException(f"Fehler beim Erstellen des Boards: {response.status_code}, {response.text}")
        return response.json()
    
    def get_board(self, board_id: int) -> Dict[str, Any]:
        """
        Hole ein Board anhand seiner ID
        
        Args:
            board_id: ID des Boards
            
        Returns:
            Das Board-Objekt
        """
        response = self.session.get(f"{self.api_url}/boards/{board_id}")
        if response.status_code != 200:
            raise DeckAPIException(f"Fehler beim Abrufen des Boards: {response.status_code}, {response.text}")
        return response.json()
    
    def update_board(self, board_id: int, title: Optional[str] = None, color: Optional[str] = None) -> Dict[str, Any]:
        """
        Aktualisiere ein Board
        
        Args:
            board_id: ID des Boards
            title: Neuer Titel (optional)
            color: Neue Farbe als Hex-Code ohne # (optional)
            
        Returns:
            Das aktualisierte Board-Objekt
        """
        # Erst aktuelles Board abrufen
        current_board = self.get_board(board_id)
        
        current_title = current_board.get("title", "")
        current_color = current_board.get("color", "0082c9")
        
        # Nur angegebene Felder aktualisieren
        data = {
            "title": title if title is not None else current_title,
            "color": color if color is not None else current_color,
            "archived": current_board.get("archived", False)
        }
        
        response = self.session.put(f"{self.api_url}/boards/{board_id}", json=data)
        if response.status_code != 200:
            raise DeckAPIException(f"Fehler beim Aktualisieren des Boards: {response.status_code}, {response.text}")
        return response.json()
    
    def delete_board(self, board_id: int) -> bool:
        """
        Lösche ein Board
        
        Args:
            board_id: ID des Boards
            
        Returns:
            True bei Erfolg
        """
        response = self.session.delete(f"{self.api_url}/boards/{board_id}")
        if response.status_code != 200:
            raise DeckAPIException(f"Fehler beim Löschen des Boards: {response.status_code}, {response.text}")
        return True
    
    # Stack (Listen) Methoden
    
    def get_stacks(self, board_id: int) -> List[Dict[str, Any]]:
        """
        Hole alle Stacks (Listen) eines Boards
        
        Args:
            board_id: ID des Boards
            
        Returns:
            Liste von Stack-Objekten
        """
        response = self.session.get(f"{self.api_url}/boards/{board_id}/stacks")
        if response.status_code != 200:
            raise DeckAPIException(f"Fehler beim Abrufen der Stacks: {response.status_code}, {response.text}")
        return response.json()
    
    def create_stack(self, board_id: int, title: str) -> Dict[str, Any]:
        """
        Erstelle einen neuen Stack (Liste) in einem Board
        
        Args:
            board_id: ID des Boards
            title: Titel des Stacks
            
        Returns:
            Das erstellte Stack-Objekt
        """
        data = {
            "title": title,
            "order": 999  # Am Ende einfügen
        }
        response = self.session.post(f"{self.api_url}/boards/{board_id}/stacks", json=data)
        if response.status_code != 200:
            raise DeckAPIException(f"Fehler beim Erstellen des Stacks: {response.status_code}, {response.text}")
        return response.json()
    
    # Card (Karten) Methoden
    
    def get_cards(self, board_id: int, stack_id: int) -> List[Dict[str, Any]]:
        """
        Hole alle Karten eines Stacks
        
        Args:
            board_id: ID des Boards
            stack_id: ID des Stacks
            
        Returns:
            Liste von Card-Objekten
        """
        response = self.session.get(f"{self.api_url}/boards/{board_id}/stacks/{stack_id}/cards")
        if response.status_code != 200:
            raise DeckAPIException(f"Fehler beim Abrufen der Karten: {response.status_code}, {response.text}")
        return response.json()
    
    def create_card(self, board_id: int, stack_id: int, title: str, 
                   description: str = "", due_date: Optional[str] = None, 
                   labels: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Erstelle eine neue Karte in einem Stack
        
        Args:
            board_id: ID des Boards
            stack_id: ID des Stacks
            title: Titel der Karte
            description: Beschreibung der Karte (optional)
            due_date: Fälligkeitsdatum im Format "YYYY-MM-DD HH:MM:SS" (optional)
            labels: Liste von Label-IDs (optional)
            
        Returns:
            Das erstellte Card-Objekt
        """
        data = {
            "title": title,
            "description": description,
            "order": 999,  # Am Ende einfügen
            "type": "plain"
        }
        
        if due_date:
            data["duedate"] = due_date
            
        if labels:
            data["labels"] = labels
            
        response = self.session.post(
            f"{self.api_url}/boards/{board_id}/stacks/{stack_id}/cards", 
            json=data
        )
        if response.status_code != 200:
            raise DeckAPIException(f"Fehler beim Erstellen der Karte: {response.status_code}, {response.text}")
        return response.json()
    
    def update_card(self, board_id: int, stack_id: int, card_id: int, 
                   title: Optional[str] = None, description: Optional[str] = None, 
                   due_date: Optional[str] = None, labels: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Aktualisiere eine Karte
        
        Args:
            board_id: ID des Boards
            stack_id: ID des Stacks
            card_id: ID der Karte
            title: Neuer Titel (optional)
            description: Neue Beschreibung (optional)
            due_date: Neues Fälligkeitsdatum im Format "YYYY-MM-DD HH:MM:SS" (optional)
            labels: Neue Liste von Label-IDs (optional)
            
        Returns:
            Das aktualisierte Card-Objekt
        """
        # Erst aktuelle Karte abrufen
        current_card = self.get_card(board_id, stack_id, card_id)
        
        # Nur angegebene Felder aktualisieren
        data = {
            "title": title if title is not None else current_card.get("title"),
            "description": description if description is not None else current_card.get("description"),
            "type": current_card.get("type", "plain")
        }
        
        if due_date is not None:
            data["duedate"] = due_date
        elif "duedate" in current_card:
            data["duedate"] = current_card["duedate"]
            
        if labels is not None:
            data["labels"] = labels
        elif "labels" in current_card:
            data["labels"] = current_card["labels"]
            
        response = self.session.put(
            f"{self.api_url}/boards/{board_id}/stacks/{stack_id}/cards/{card_id}", 
            json=data
        )
        if response.status_code != 200:
            raise DeckAPIException(f"Fehler beim Aktualisieren der Karte: {response.status_code}, {response.text}")
        return response.json()
    
    def get_card(self, board_id: int, stack_id: int, card_id: int) -> Dict[str, Any]:
        """
        Hole eine Karte anhand ihrer ID
        
        Args:
            board_id: ID des Boards
            stack_id: ID des Stacks
            card_id: ID der Karte
            
        Returns:
            Das Card-Objekt
        """
        response = self.session.get(
            f"{self.api_url}/boards/{board_id}/stacks/{stack_id}/cards/{card_id}"
        )
        if response.status_code != 200:
            raise DeckAPIException(f"Fehler beim Abrufen der Karte: {response.status_code}, {response.text}")
        return response.json()
    
    def delete_card(self, board_id: int, stack_id: int, card_id: int) -> bool:
        """
        Lösche eine Karte
        
        Args:
            board_id: ID des Boards
            stack_id: ID des Stacks
            card_id: ID der Karte
            
        Returns:
            True bei Erfolg
        """
        response = self.session.delete(
            f"{self.api_url}/boards/{board_id}/stacks/{stack_id}/cards/{card_id}"
        )
        if response.status_code != 200:
            raise DeckAPIException(f"Fehler beim Löschen der Karte: {response.status_code}, {response.text}")
        return True
    
    # Anhänge-Methoden
    
    def add_attachment(self, board_id: int, stack_id: int, card_id: int, 
                      file_path: str, file_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Füge einen Anhang zu einer Karte hinzu
        
        Args:
            board_id: ID des Boards
            stack_id: ID des Stacks
            card_id: ID der Karte
            file_path: Pfad zur Datei
            file_type: MIME-Typ der Datei (optional, wird automatisch ermittelt wenn nicht angegeben)
            
        Returns:
            Das erstellte Attachment-Objekt
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Datei nicht gefunden: {file_path}")
            
        file_name = os.path.basename(file_path)
        
        # MIME-Typ ermitteln falls nicht angegeben
        if not file_type:
            import mimetypes
            file_type, _ = mimetypes.guess_type(file_path)
            if not file_type:
                file_type = "application/octet-stream"
        
        with open(file_path, "rb") as f:
            files = {"file": (file_name, f, file_type)}
            response = self.session.post(
                f"{self.api_url}/boards/{board_id}/stacks/{stack_id}/cards/{card_id}/attachments",
                files=files
            )
            
        if response.status_code != 200:
            raise DeckAPIException(f"Fehler beim Hinzufügen des Anhangs: {response.status_code}, {response.text}")
        return response.json()


# Beispielverwendung
if __name__ == "__main__":
    # Nur zur Demonstration, in der realen Anwendung sollten die Zugangsdaten 
    # aus einer Konfigurationsdatei oder Umgebungsvariablen geladen werden
    NEXTCLOUD_URL = os.environ.get("NEXTCLOUD_URL", "https://cloud.example.com")
    NEXTCLOUD_USER = os.environ.get("NEXTCLOUD_USER", "admin")
    NEXTCLOUD_PASSWORD = os.environ.get("NEXTCLOUD_PASSWORD", "password")
    
    try:
        client = DeckAPIClient(NEXTCLOUD_URL, NEXTCLOUD_USER, NEXTCLOUD_PASSWORD)
        
        # Beispiel: Alle Boards auflisten
        boards = client.get_all_boards()
        print(f"Verfügbare Boards: {len(boards)}")
        for board in boards:
            print(f"- {board['title']} (ID: {board['id']})")
        
    except Exception as e:
        print(f"Fehler: {e}")