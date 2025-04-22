"""
SwissAirDry API - Datenbankverbindung

@author Swiss Air Dry Team <info@swissairdry.com>
@copyright 2023-2025 Swiss Air Dry Team
"""

import os
from typing import Dict, Any

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Umgebungsvariablen laden
load_dotenv()

# Datenbankverbindungs-URL
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./swissairdry.db")

# Engine erstellen
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = sqlalchemy.create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = sqlalchemy.create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
    )

# Sessionmaker erstellen
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Basisklasse für Modelle
Base = declarative_base()


# Hilfsfunktion für Datenbankabfragen
def get_db():
    """
    Datenbankverbindung herstellen und als Generator zurückgeben.
    Wird für Dependency Injection in FastAPI-Routen verwendet.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()