"""
FastAPI Background Tasks Module

Dieses Modul stellt die BackgroundTasks-Klasse zur Verfügung.
"""

# Importiere Original BackgroundTasks
from fastapi.background import BackgroundTasks as OriginalBackgroundTasks

# Re-exportiere die Original-BackgroundTasks-Klasse
BackgroundTasks = OriginalBackgroundTasks