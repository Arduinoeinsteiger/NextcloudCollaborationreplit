"""
SwissAirDry Nextcloud Deck Integration
--------------------------------------

Dieses Paket enthält die Integration zwischen SwissAirDry und der Nextcloud Deck App.

Die Hauptklassen sind:
- DeckAPIClient: Client für die Nextcloud Deck API
- SwissAirDryDeckIntegration: Integrationslogik zwischen SwissAirDry und Deck
"""

from .client import DeckAPIClient, DeckAPIException
from .integration import SwissAirDryDeckIntegration

__all__ = ["DeckAPIClient", "DeckAPIException", "SwissAirDryDeckIntegration"]