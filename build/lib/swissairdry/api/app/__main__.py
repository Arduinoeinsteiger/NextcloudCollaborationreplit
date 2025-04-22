"""
SwissAirDry API Server - Hauptausführungsmodul

Dieses Modul dient als Einstiegspunkt, wenn das Paket als Modul ausgeführt wird.

@author Swiss Air Dry Team <info@swissairdry.com>
@copyright 2023-2025 Swiss Air Dry Team
"""

import os
import sys
import uvicorn

# Verzeichnis zum Suchpfad hinzufügen, um absolute Importe zu ermöglichen
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

if __name__ == "__main__":
    # Server starten
    uvicorn.run(
        "run:app",
        host="0.0.0.0",
        port=int(os.getenv("API_PORT", "5000")),
        reload=True,
        reload_dirs=[os.path.dirname(__file__)]
    )