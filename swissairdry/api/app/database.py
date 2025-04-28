"""
SwissAirDry - Datenbank-Modul
-----------------------------

Datenbank-Verbindung und Basispfadklasse für die Tabellen.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator


# Datenbankverbindungs-URL aus Umgebungsvariable oder Standardwert
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./swissairdry.db")

# SQLAlchemy-Engine erstellen
engine = create_engine(
    DATABASE_URL,
    echo=False,  # SQL-Anweisungen nicht ausgeben
    pool_pre_ping=True,  # Verbindung prüfen, bevor sie aus dem Pool geholt wird
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# Session-Factory erstellen
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Basisklasse für die Models erstellen
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Gibt eine Datenbankverbindung zurück und schließt diese nach Verwendung.
    Diese Funktion dient als Dependency für FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialisiert die Datenbank und erstellt alle Tabellen.
    """
    # Import der Modelle, damit sie registriert werden
    from swissairdry.api.app.models import device
    
    # Tabellen erstellen, falls sie noch nicht existieren
    Base.metadata.create_all(bind=engine)