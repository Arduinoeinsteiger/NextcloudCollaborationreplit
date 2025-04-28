"""
SwissAirDry API - Starter Skript für die einfache API (Backup-Version)

@author Swiss Air Dry Team <info@swissairdry.com>
@copyright 2023-2025 Swiss Air Dry Team
"""

import os
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))  # Verwende einen anderen Port (5001)
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"SwissAirDry Simplified API Server startet auf Port {port}...")
    
    # Starte den API-Server
    uvicorn.run(
        "simple_api_backup:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )