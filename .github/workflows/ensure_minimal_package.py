#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dieses Skript stellt sicher, dass ein minimales SwissAirDry-Paket erzeugt werden kann.
Es erstellt fehlende Dateien und Verzeichnisse, um sicherzustellen, dass der Build nicht fehlschlägt.
"""

import os
import sys
import shutil
from pathlib import Path

# Minimale Version des Pakets
MINIMAL_VERSION = "1.0.0"

# Garantierte Verzeichnisse, die existieren müssen
CRITICAL_DIRS = [
    'swissairdry',
    'swissairdry/api',
    'swissairdry/api/app',
    'swissairdry/api/app/routes',
    'swissairdry/db',
    'swissairdry/mqtt',
    'swissairdry/integration',
    'swissairdry/integration/deck',
    'swissairdry/nextcloud',
]

# Minimale Dateien, die existieren müssen
MINIMAL_FILES = {
    'swissairdry/__init__.py': f'''"""
SwissAirDry Package

Hauptpaket für die SwissAirDry Python-Module.
"""

__version__ = "{MINIMAL_VERSION}"
__author__ = "SwissAirDry Team"
''',

    'swissairdry/api/__init__.py': '''"""
SwissAirDry API Package

Dieses Paket enthält die API-Komponenten des SwissAirDry-Systems.
"""
''',

    'swissairdry/db/__init__.py': '''"""
SwissAirDry Database Package

Dieses Paket enthält die Datenbankkomponenten des SwissAirDry-Systems.
"""
''',

    'swissairdry/mqtt/__init__.py': '''"""
SwissAirDry MQTT Package

Dieses Paket enthält die MQTT-Komponenten des SwissAirDry-Systems.
"""
''',

    'swissairdry/integration/__init__.py': '''"""
SwissAirDry Integration Package

Dieses Paket enthält Integrationen mit externen Systemen.
"""
''',

    'swissairdry/integration/deck/__init__.py': '''"""
SwissAirDry Deck Integration

Dieses Modul stellt eine Integration mit der Nextcloud Deck-App bereit.
"""
''',

    'swissairdry/nextcloud/__init__.py': '''"""
SwissAirDry Nextcloud Integration

Dieses Paket enthält die Nextcloud-Integration des SwissAirDry-Systems.
"""
''',
}

# Minimale Konfigurationsdateien
MINIMAL_CONFIG = {
    'pyproject.toml': f'''[build-system]
requires = ["setuptools>=42", "wheel>=0.37.0", "build>=0.7.0"]
build-backend = "setuptools.build_meta"

[project]
name = "swissairdry"
version = "{MINIMAL_VERSION}"
authors = [
    {{name = "SwissAirDry Team", email = "info@swissairdry.com"}},
]
description = "SwissAirDry IoT System"
readme = "README.md"
requires-python = ">=3.9"
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]

[tool.setuptools]
packages = {{ find = {{ include = ["swissairdry", "swissairdry.*"] }} }}
package-dir = {{ "" = "." }}
''',

    'setup.py': f'''#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="swissairdry",
    version="{MINIMAL_VERSION}",
    packages=find_packages(include=['swissairdry', 'swissairdry.*']),
    install_requires=[
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "paho-mqtt>=1.6.0",
        "sqlalchemy>=1.4.0",
        "pydantic>=1.8.0",
        "python-dotenv>=0.19.0",
    ],
    python_requires=">=3.9",
)
''',

    'MANIFEST.in': '''include README.md
include SECURITY.md
include LICENSE
include pyproject.toml
include setup.py
include .flake8

recursive-include swissairdry/api/app/templates *.html
recursive-include swissairdry/api/app/static *.css *.js *.png *.jpg *.svg
recursive-include swissairdry/mqtt *.conf
recursive-include swissairdry/nextcloud *.xml *.json *.php
recursive-include swissairdry *.md *.txt *.json *.yaml *.yml

prune tests
prune .github
prune build
prune dist
prune *.egg-info
prune */__pycache__
prune */*/__pycache__
prune */*/*/__pycache__
''',

    'README.md': '''# SwissAirDry

Eine modulare IoT-Plattform für Swiss Air Dry Geräte und Dienstleistungen.

## Beschreibung

Diese Software ist die zentrale Komponente des SwissAirDry IoT-Ökosystems.
Sie verbindet Sensoren, Geräte und Benutzeranwendungen miteinander.

## Installation

```
pip install swissairdry
```

## Features

- IoT-Gerätemanagement
- Nextcloud-Integration
- MQTT-Messaging
- REST API
''',
}


def ensure_directories(base_dir):
    """Stellt sicher, dass alle wichtigen Verzeichnisse existieren."""
    for d in CRITICAL_DIRS:
        full_path = os.path.join(base_dir, d)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
            print(f"Verzeichnis erstellt: {full_path}")


def ensure_files(base_dir):
    """Stellt sicher, dass alle Minimaldateien existieren."""
    for file_path, content in MINIMAL_FILES.items():
        full_path = os.path.join(base_dir, file_path)
        if not os.path.exists(full_path) or os.path.getsize(full_path) == 0:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
            print(f"Datei erstellt/aktualisiert: {full_path}")


def ensure_config(base_dir):
    """Stellt sicher, dass alle Konfigurationsdateien existieren."""
    for file_path, content in MINIMAL_CONFIG.items():
        full_path = os.path.join(base_dir, file_path)
        # Für diese Dateien greifen wir nur ein, wenn sie nicht existieren
        if not os.path.exists(full_path):
            with open(full_path, 'w') as f:
                f.write(content)
            print(f"Konfiguration erstellt: {full_path}")


def main():
    """Hauptfunktion für die Ausführung des Skripts."""
    base_dir = os.path.abspath('.')
    
    print(f"Basis-Verzeichnis: {base_dir}")
    print("Stelle sicher, dass ein minimales SwissAirDry-Paket gebaut werden kann...")
    
    ensure_directories(base_dir)
    ensure_files(base_dir)
    ensure_config(base_dir)
    
    print("\nMinimales Paket gesichert! Der Build sollte nun funktionieren.")
    return 0


if __name__ == "__main__":
    sys.exit(main())