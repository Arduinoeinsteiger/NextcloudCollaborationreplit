"""
SwissAirDry Integration - Nextcloud Deck API Client
--------------------------------------------------

Diese Datei enthält den Client für die Integration mit der Nextcloud Deck API.
"""

import os
import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin


class DeckAPIException(Exception):
    """Exception für Fehler bei der Kommunikation mit der Deck API"""
    pass


class DeckAPIClient:
    """
    Client für die Kommunikation mit der Nextcloud Deck API
    
    Ermöglicht den Zugriff auf Boards, Listen und Karten in der Nextcloud Deck App.
    """
    
    def __init__(
        self, 
        base_url: str, 
        username: str, 
        password: str,
        api_path: str = "/index.php/apps/deck/api/v1.0"
    ):
        """
        Initialisiert den Deck API Client.
        
        Args:
            base_url: Basis-URL der Nextcloud-Instanz (z.B. https://cloud.example.com)
            username: Nextcloud-Benutzername
            password: Nextcloud-Passwort oder App-Passwort
            api_path: Pfad zur Deck API
        """
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}{api_path}"
        self.auth = (username, password)
        self.logger = logging.getLogger(__name__)
    
    def _request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Führt eine HTTP-Anfrage an die Deck API aus.
        
        Args:
            method: HTTP-Methode (GET, POST, PUT, DELETE)
            endpoint: API-Endpunkt (ohne Basis-URL)
            data: Daten für POST/PUT-Anfragen
            params: URL-Parameter für GET-Anfragen
            
        Returns:
            Dict: Antwort der API als Dictionary
            
        Raises:
            DeckAPIException: Bei Fehlern in der API-Kommunikation
        """
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                auth=self.auth,
                json=data,
                params=params
            )
            
            # Fehlerbehandlung
            if response.status_code >= 400:
                self.logger.error(f"Fehler bei API-Anfrage: {response.status_code} {response.text}")
                raise DeckAPIException(f"API-Fehler: {response.status_code} - {response.text}")
            
            # JSON-Antwort parsen
            if response.text:
                return response.json()
            return {}
            
        except requests.RequestException as e:
            self.logger.error(f"Verbindungsfehler zur Deck API: {e}")
            raise DeckAPIException(f"Verbindungsfehler: {e}")
    
    def get_boards(self) -> List[Dict[str, Any]]:
        """
        Ruft alle Boards ab.
        
        Returns:
            List[Dict]: Liste aller Boards
        """
        return self._request("GET", "boards")
    
    def get_board(self, board_id: int) -> Dict[str, Any]:
        """
        Ruft ein Board anhand seiner ID ab.
        
        Args:
            board_id: ID des Boards
            
        Returns:
            Dict: Board-Daten
        """
        return self._request("GET", f"boards/{board_id}")
    
    def create_board(self, title: str, color: str = "0082c9") -> Dict[str, Any]:
        """
        Erstellt ein neues Board.
        
        Args:
            title: Titel des Boards
            color: Farbe des Boards (Hex-Code)
            
        Returns:
            Dict: Daten des erstellten Boards
        """
        data = {
            "title": title,
            "color": color
        }
        return self._request("POST", "boards", data=data)
    
    def get_stacks(self, board_id: int) -> List[Dict[str, Any]]:
        """
        Ruft alle Listen (Stacks) eines Boards ab.
        
        Args:
            board_id: ID des Boards
            
        Returns:
            List[Dict]: Liste aller Listen im Board
        """
        return self._request("GET", f"boards/{board_id}/stacks")
    
    def create_stack(self, board_id: int, title: str) -> Dict[str, Any]:
        """
        Erstellt eine neue Liste (Stack) in einem Board.
        
        Args:
            board_id: ID des Boards
            title: Titel der Liste
            
        Returns:
            Dict: Daten der erstellten Liste
        """
        data = {"title": title}
        return self._request("POST", f"boards/{board_id}/stacks", data=data)
    
    def get_cards(self, board_id: int, stack_id: int) -> List[Dict[str, Any]]:
        """
        Ruft alle Karten einer Liste ab.
        
        Args:
            board_id: ID des Boards
            stack_id: ID der Liste
            
        Returns:
            List[Dict]: Liste aller Karten in der Liste
        """
        return self._request("GET", f"boards/{board_id}/stacks/{stack_id}/cards")
    
    def create_card(
        self, 
        board_id: int, 
        stack_id: int, 
        title: str, 
        description: str = "",
        labels: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Erstellt eine neue Karte in einer Liste.
        
        Args:
            board_id: ID des Boards
            stack_id: ID der Liste
            title: Titel der Karte
            description: Beschreibung der Karte
            labels: Liste von Label-IDs für die Karte
            
        Returns:
            Dict: Daten der erstellten Karte
        """
        data = {
            "title": title,
            "description": description
        }
        if labels:
            data["labels"] = labels
            
        return self._request("POST", f"boards/{board_id}/stacks/{stack_id}/cards", data=data)