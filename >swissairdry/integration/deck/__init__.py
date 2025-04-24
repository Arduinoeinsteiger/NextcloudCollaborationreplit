"""
SwissAirDry Integration - Nextcloud Deck
----------------------------------------

Dieses Modul enthält die Integration mit der Nextcloud Deck App.
"""

from .client import DeckAPIClient, DeckAPIException
from .integration import SwissAirDryDeckIntegration

__all__ = ['DeckAPIClient', 'DeckAPIException', 'SwissAirDryDeckIntegration']