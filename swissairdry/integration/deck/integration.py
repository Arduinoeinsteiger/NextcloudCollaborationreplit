"""
SwissAirDry Integration - Nextcloud Deck Integration
---------------------------------------------------

Diese Datei enthält die Integration mit der Nextcloud Deck App.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from .client import DeckAPIClient, DeckAPIException


class SwissAirDryDeckIntegration:
    """
    Integration zwischen SwissAirDry und der Nextcloud Deck App
    
    Diese Klasse stellt Funktionen bereit, um SwissAirDry-Daten in Nextcloud Deck
    zu visualisieren und zu verwalten.
    """
    
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        board_name: str = "SwissAirDry"
    ):
        """
        Initialisiert die SwissAirDry Deck Integration.
        
        Args:
            base_url: Basis-URL der Nextcloud-Instanz
            username: Nextcloud-Benutzername
            password: Nextcloud-Passwort oder App-Passwort
            board_name: Name des Boards für SwissAirDry-Daten
        """
        self.logger = logging.getLogger(__name__)
        self.client = DeckAPIClient(base_url, username, password)
        self.board_name = board_name
        self.board_id = None
        self.stacks = {}
        
    async def initialize(self) -> bool:
        """
        Initialisiert die Integration und stellt sicher, dass das Board und die Listen existieren.
        
        Returns:
            bool: True, wenn die Initialisierung erfolgreich war, sonst False
        """
        try:
            # Board finden oder erstellen
            self.board_id = await self._get_or_create_board()
            if not self.board_id:
                self.logger.error("Konnte kein Board erstellen oder finden")
                return False
                
            # Standard-Listen erstellen
            stack_names = ["Aktive Aufträge", "Abgeschlossene Aufträge", "Wartung", "Alarme"]
            for name in stack_names:
                stack_id = await self._get_or_create_stack(name)
                if stack_id:
                    self.stacks[name] = stack_id
                    
            self.logger.info(f"Deck Integration initialisiert: Board ID {self.board_id}, Listen: {len(self.stacks)}")
            return True
            
        except DeckAPIException as e:
            self.logger.error(f"Fehler bei der Initialisierung der Deck Integration: {e}")
            return False
    
    async def _get_or_create_board(self) -> Optional[int]:
        """
        Findet oder erstellt ein Board für SwissAirDry.
        
        Returns:
            Optional[int]: Board-ID oder None, wenn kein Board gefunden oder erstellt werden konnte
        """
        try:
            # Alle Boards abrufen
            boards = self.client.get_boards()
            
            # Nach SwissAirDry-Board suchen
            for board in boards:
                if board.get("title") == self.board_name:
                    self.logger.info(f"Existierendes Board gefunden: {board['id']} - {self.board_name}")
                    return board["id"]
            
            # Kein Board gefunden, neues erstellen
            board = self.client.create_board(self.board_name, "0082c9")
            self.logger.info(f"Neues Board erstellt: {board['id']} - {self.board_name}")
            return board["id"]
            
        except DeckAPIException as e:
            self.logger.error(f"Fehler beim Finden/Erstellen des Boards: {e}")
            return None
    
    async def _get_or_create_stack(self, name: str) -> Optional[int]:
        """
        Findet oder erstellt eine Liste (Stack) im SwissAirDry-Board.
        
        Args:
            name: Name der Liste
            
        Returns:
            Optional[int]: Listen-ID oder None, wenn keine Liste gefunden oder erstellt werden konnte
        """
        if not self.board_id:
            self.logger.error("Kein Board initialisiert")
            return None
            
        try:
            # Alle Listen des Boards abrufen
            stacks = self.client.get_stacks(self.board_id)
            
            # Nach Liste mit angegebenem Namen suchen
            for stack in stacks:
                if stack.get("title") == name:
                    self.logger.info(f"Existierende Liste gefunden: {stack['id']} - {name}")
                    return stack["id"]
            
            # Keine Liste gefunden, neue erstellen
            stack = self.client.create_stack(self.board_id, name)
            self.logger.info(f"Neue Liste erstellt: {stack['id']} - {name}")
            return stack["id"]
            
        except DeckAPIException as e:
            self.logger.error(f"Fehler beim Finden/Erstellen der Liste: {e}")
            return None
    
    async def create_job_card(
        self,
        job_id: str,
        title: str,
        description: str,
        status: str = "Aktiv",
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Erstellt eine Karte für einen Auftrag.
        
        Args:
            job_id: Auftrags-ID
            title: Titel des Auftrags
            description: Beschreibung des Auftrags
            status: Status des Auftrags ("Aktiv" oder "Abgeschlossen")
            details: Weitere Details zum Auftrag
            
        Returns:
            bool: True, wenn die Karte erstellt wurde, sonst False
        """
        # Board ID-Prüfung
        if self.board_id is None:
            self.logger.error("Board ID ist None, Karte kann nicht erstellt werden")
            return False
            
        # Stack anhand des Status bestimmen
        stack_name = "Aktive Aufträge" if status == "Aktiv" else "Abgeschlossene Aufträge"
        stack_id = self.stacks.get(stack_name)
        
        if not stack_id:
            self.logger.error(f"Keine Liste für Status {status} gefunden")
            return False
            
        # Beschreibung erweitern
        full_description = f"**Auftrags-ID:** {job_id}\n\n{description}\n\n"
        
        # Details hinzufügen, wenn vorhanden
        if details:
            full_description += "**Details:**\n\n"
            for key, value in details.items():
                full_description += f"- **{key}:** {value}\n"
        
        # Zeitstempel hinzufügen
        full_description += f"\n\n_Erstellt: {datetime.now().strftime('%d.%m.%Y %H:%M')}_"
        
        try:
            # Karte erstellen mit benannten Parametern für bessere Typprüfung
            board_id_int = int(self.board_id)  # Explizite Typkonvertierung
            stack_id_int = int(stack_id)       # Explizite Typkonvertierung
            
            card = self.client.create_card(
                board_id=board_id_int,
                stack_id=stack_id_int,
                title=title,
                description=full_description
            )
            self.logger.info(f"Auftragskarte erstellt: {card['id']} - {title}")
            return True
            
        except (DeckAPIException, ValueError, TypeError) as e:
            self.logger.error(f"Fehler beim Erstellen der Auftragskarte: {e}")
            return False
    
    async def create_alarm_card(
        self,
        device_id: str,
        alarm_type: str,
        description: str,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Erstellt eine Alarmkarte.
        
        Args:
            device_id: Geräte-ID
            alarm_type: Typ des Alarms
            description: Beschreibung des Alarms
            timestamp: Zeitstempel des Alarms (optional)
            
        Returns:
            bool: True, wenn die Karte erstellt wurde, sonst False
        """
        # Board ID-Prüfung
        if self.board_id is None:
            self.logger.error("Board ID ist None, Karte kann nicht erstellt werden")
            return False
            
        stack_id = self.stacks.get("Alarme")
        
        if not stack_id:
            self.logger.error("Keine Alarmliste gefunden")
            return False
            
        # Titel generieren
        title = f"Alarm: {alarm_type} ({device_id})"
        
        # Zeitstempel formatieren
        if not timestamp:
            timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%d.%m.%Y %H:%M:%S")
        
        # Beschreibung erstellen
        full_description = (
            f"**Geräte-ID:** {device_id}\n\n"
            f"**Alarmtyp:** {alarm_type}\n\n"
            f"**Zeitpunkt:** {timestamp_str}\n\n"
            f"**Beschreibung:**\n{description}\n\n"
        )
        
        try:
            # Karte erstellen mit benannten Parametern für bessere Typprüfung
            board_id_int = int(self.board_id)  # Explizite Typkonvertierung
            stack_id_int = int(stack_id)       # Explizite Typkonvertierung
            
            card = self.client.create_card(
                board_id=board_id_int,
                stack_id=stack_id_int,
                title=title,
                description=full_description
            )
            self.logger.info(f"Alarmkarte erstellt: {card['id']} - {title}")
            return True
            
        except (DeckAPIException, ValueError, TypeError) as e:
            self.logger.error(f"Fehler beim Erstellen der Alarmkarte: {e}")
            return False