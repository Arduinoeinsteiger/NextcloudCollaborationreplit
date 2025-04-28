"""
FastAPI Applications Module

Dieses Modul stellt die FastAPI-Anwendungsklasse zur Verfügung.
Es dient als Ersatz für die originale FastAPI-Klasse, die in unseren Modulen verwendet wird.
"""

# Importiere Original FastAPI
from fastapi.applications import FastAPI as OriginalFastAPI

# Re-exportiere die Original-FastAPI-Klasse
FastAPI = OriginalFastAPI