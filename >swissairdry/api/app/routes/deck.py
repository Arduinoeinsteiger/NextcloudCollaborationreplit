"""
SwissAirDry API - Deck Integration Routes
----------------------------------------

Diese Datei enthält die API-Routen für die Integration mit der Nextcloud Deck App.
"""

import os
import json
from typing import Dict, List, Optional, Any, Union
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel

from swissairdry.integration.deck import DeckAPIClient, SwissAirDryDeckIntegration, DeckAPIException

# API-Router erstellen
router = APIRouter(
    prefix="/api/deck",
    tags=["deck"],
    responses={404: {"description": "Not found"}},
)

# Konfiguration aus Umgebungsvariablen
NEXTCLOUD_URL = os.getenv("NEXTCLOUD_URL", "")
NEXTCLOUD_USER = os.getenv("NEXTCLOUD_USER", "")
NEXTCLOUD_PASSWORD = os.getenv("NEXTCLOUD_PASSWORD", "")

# Modelle für API-Anfragen und Antworten
class DeckConfig(BaseModel):
    nextcloud_url: str
    username: str
    password: str

class JobRequest(BaseModel):
    job_id: str
    job_title: str
    customer_name: str

class DeviceRequest(BaseModel):
    board_id: int
    device_id: str
    device_name: str
    status: str = "In Vorbereitung"

class DeviceUpdateRequest(BaseModel):
    board_id: int
    card_id: int
    source_stack_id: int
    target_status: str
    measurement_data: Optional[Dict[str, Any]] = None

class TaskRequest(BaseModel):
    board_id: int
    task_title: str
    task_description: str
    assigned_to: Optional[str] = None
    due_date: Optional[str] = None
    stack_name: str = "In Vorbereitung"

class TaskCompletionRequest(BaseModel):
    board_id: int
    card_id: int
    source_stack_id: int
    completion_note: Optional[str] = None

class DeckResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

# Dependency für Deck Integration
def get_deck_integration():
    """Erstelle und gebe eine Instanz der DeckIntegration zurück"""
    if not NEXTCLOUD_URL or not NEXTCLOUD_USER or not NEXTCLOUD_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nextcloud Deck Integration ist nicht konfiguriert. Bitte NEXTCLOUD_URL, NEXTCLOUD_USER und NEXTCLOUD_PASSWORD in der Umgebung setzen."
        )
    try:
        integration = SwissAirDryDeckIntegration(NEXTCLOUD_URL, NEXTCLOUD_USER, NEXTCLOUD_PASSWORD)
        return integration
    except DeckAPIException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Fehler bei der Verbindung zur Nextcloud Deck API: {str(e)}"
        )

# API-Routen

@router.post("/config", response_model=DeckResponse)
async def set_deck_config(config: DeckConfig):
    """
    Konfiguriere die Nextcloud Deck Integration.
    
    Diese Route ist nur für die initiale Konfiguration oder zum Ändern der Konfiguration gedacht.
    Im Produktionssystem sollte die Konfiguration über Umgebungsvariablen erfolgen.
    """
    global NEXTCLOUD_URL, NEXTCLOUD_USER, NEXTCLOUD_PASSWORD
    
    # Konfiguration temporär setzen (wird bei Neustart zurückgesetzt)
    NEXTCLOUD_URL = config.nextcloud_url
    NEXTCLOUD_USER = config.username
    NEXTCLOUD_PASSWORD = config.password
    
    # Verbindung testen
    try:
        integration = SwissAirDryDeckIntegration(NEXTCLOUD_URL, NEXTCLOUD_USER, NEXTCLOUD_PASSWORD)
        return DeckResponse(
            success=True,
            message="Deck Integration erfolgreich konfiguriert und getestet",
            data={"main_board_id": integration.main_board_id}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fehler bei der Konfiguration der Deck Integration: {str(e)}"
        )

@router.get("/status", response_model=DeckResponse)
async def get_deck_status(integration: SwissAirDryDeckIntegration = Depends(get_deck_integration)):
    """Prüfe den Status der Deck Integration"""
    try:
        boards = integration.deck_client.get_all_boards()
        return DeckResponse(
            success=True,
            message="Deck Integration ist aktiv",
            data={
                "main_board_id": integration.main_board_id,
                "board_count": len(boards)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Fehler bei der Verbindung zur Nextcloud Deck API: {str(e)}"
        )

@router.post("/jobs", response_model=DeckResponse)
async def create_job(
    job: JobRequest,
    integration: SwissAirDryDeckIntegration = Depends(get_deck_integration)
):
    """Erstelle ein neues Auftragsboard in Deck"""
    try:
        board_id = integration.create_job_board(job.job_id, job.job_title, job.customer_name)
        return DeckResponse(
            success=True,
            message=f"Auftragsboard für {job.job_id} erfolgreich erstellt",
            data={"board_id": board_id}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Erstellen des Auftragsboards: {str(e)}"
        )

@router.post("/devices", response_model=DeckResponse)
async def add_device(
    device: DeviceRequest,
    integration: SwissAirDryDeckIntegration = Depends(get_deck_integration)
):
    """Füge ein Gerät zu einem Auftragsboard hinzu"""
    try:
        card_id = integration.add_device_card(
            device.board_id, 
            device.device_id, 
            device.device_name,
            device.status
        )
        return DeckResponse(
            success=True,
            message=f"Gerät {device.device_name} erfolgreich zum Board hinzugefügt",
            data={"card_id": card_id}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Hinzufügen des Geräts: {str(e)}"
        )

@router.put("/devices", response_model=DeckResponse)
async def update_device(
    update: DeviceUpdateRequest,
    integration: SwissAirDryDeckIntegration = Depends(get_deck_integration)
):
    """Aktualisiere den Status eines Geräts"""
    try:
        integration.update_device_status(
            update.board_id,
            update.card_id,
            update.source_stack_id,
            update.target_status,
            update.measurement_data
        )
        return DeckResponse(
            success=True,
            message=f"Gerätestatus erfolgreich auf '{update.target_status}' aktualisiert"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Aktualisieren des Gerätestatus: {str(e)}"
        )

@router.post("/tasks", response_model=DeckResponse)
async def add_task(
    task: TaskRequest,
    integration: SwissAirDryDeckIntegration = Depends(get_deck_integration)
):
    """Füge eine Aufgabe zu einem Auftragsboard hinzu"""
    try:
        card_id = integration.add_task_card(
            task.board_id,
            task.task_title,
            task.task_description,
            task.assigned_to,
            None if not task.due_date else task.due_date,
            task.stack_name
        )
        return DeckResponse(
            success=True,
            message=f"Aufgabe '{task.task_title}' erfolgreich zum Board hinzugefügt",
            data={"card_id": card_id}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Hinzufügen der Aufgabe: {str(e)}"
        )

@router.put("/tasks/complete", response_model=DeckResponse)
async def complete_task(
    completion: TaskCompletionRequest,
    integration: SwissAirDryDeckIntegration = Depends(get_deck_integration)
):
    """Markiere eine Aufgabe als abgeschlossen"""
    try:
        integration.complete_task(
            completion.board_id,
            completion.card_id,
            completion.source_stack_id,
            completion.completion_note
        )
        return DeckResponse(
            success=True,
            message="Aufgabe erfolgreich als abgeschlossen markiert"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abschließen der Aufgabe: {str(e)}"
        )

@router.get("/boards", response_model=DeckResponse)
async def get_boards(
    integration: SwissAirDryDeckIntegration = Depends(get_deck_integration)
):
    """Hole alle verfügbaren Boards"""
    try:
        boards = integration.deck_client.get_all_boards()
        return DeckResponse(
            success=True,
            message=f"{len(boards)} Boards gefunden",
            data={"boards": boards}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen der Boards: {str(e)}"
        )