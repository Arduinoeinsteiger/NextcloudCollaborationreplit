#!/usr/bin/env python3
"""
Dieses Skript repariert die Paketstruktur für die CI/CD-Pipeline.
Es erstellt alle notwendigen __init__.py Dateien in den Unterverzeichnissen
und sorgt dafür, dass die Paketstruktur korrekt ist.
"""

import os
import sys
import shutil
from pathlib import Path


def create_init_files(base_dir):
    """Erstellt __init__.py Dateien in allen Python-Package-Verzeichnissen."""
    created_files = []

    # Iteriere durch alle Unterverzeichnisse
    for root, dirs, files in os.walk(os.path.join(base_dir, 'swissairdry')):
        # Überspringe versteckte Verzeichnisse und spezielle Verzeichnisse
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'tests', 'build', 'dist']]
        
        # Erstelle in jedem Verzeichnis eine __init__.py Datei
        init_file = os.path.join(root, '__init__.py')
        
        # Wenn noch keine __init__.py existiert, erstelle eine
        if not os.path.exists(init_file):
            package_name = os.path.basename(root)
            with open(init_file, 'w') as f:
                f.write(f'"""\n{package_name} Package\n\nDieses Modul ist Teil des SwissAirDry-Projekts.\n"""\n\n')
            created_files.append(init_file)
            print(f"Erstellt: {init_file}")
    
    return created_files


def ensure_critical_files():
    """Stellt sicher, dass kritische Konfigurationsdateien vorhanden sind."""
    # MANIFEST.in prüfen und erstellen/korrigieren falls nötig
    manifest_path = 'MANIFEST.in'
    if not os.path.exists(manifest_path):
        manifest_content = """include README.md
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
"""
        with open(manifest_path, 'w') as f:
            f.write(manifest_content)
        print(f"MANIFEST.in erstellt: {manifest_path}")
    
    # pyproject.toml prüfen
    if os.path.exists('pyproject.toml'):
        print("pyproject.toml gefunden: ✓")
    else:
        # Erstelle eine minimal funktionierende pyproject.toml
        pyproject_content = """[build-system]
requires = ["setuptools==59.8.0", "wheel>=0.37.0", "build>=0.7.0"]
build-backend = "setuptools.build_meta"

[project]
name = "swissairdry"
version = "1.0.0"
authors = [
    {name = "Swiss Air Dry Team", email = "info@swissairdry.com"},
]
description = "Swiss Air Dry IoT System"
readme = "README.md"
requires-python = ">=3.9"
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]

[tool.setuptools]
packages = { find = { include = ["swissairdry", "swissairdry.*"] } }
package-dir = { "" = "." }

[tool.pytest.ini_options]
testpaths = ["tests"]
"""
        with open('pyproject.toml', 'w') as f:
            f.write(pyproject_content)
        print("pyproject.toml erstellt: ✓")
    
    # setup.py prüfen
    if os.path.exists('setup.py'):
        with open('setup.py', 'r') as f:
            content = f.read()
        # Überprüfe, ob setup.py find_packages verwendet
        if "from setuptools import find_packages" not in content:
            # Füge find_packages hinzu
            content = content.replace(
                "from setuptools import setup",
                "from setuptools import setup, find_packages"
            )
            # Ersetze packages=packages oder ähnliches durch find_packages
            if "packages=find_packages(include=['swissairdry', 'swissairdry.*'])" not in content:
                content = content.replace(
                    "packages=packages",
                    "packages=find_packages(include=['swissairdry', 'swissairdry.*'])"
                )
                content = content.replace(
                    "packages=['swissairdry']",
                    "packages=find_packages(include=['swissairdry', 'swissairdry.*'])"
                )
            with open('setup.py', 'w') as f:
                f.write(content)
            print("setup.py korrigiert: ✓")
        else:
            print("setup.py überprüft: ✓")
    else:
        # Erstelle eine minimal funktionierende setup.py
        setup_content = """#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="swissairdry",
    version="1.0.0",
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
"""
        with open('setup.py', 'w') as f:
            f.write(setup_content)
        print("setup.py erstellt: ✓")


def main():
    """Hauptfunktion für die Ausführung des Skripts."""
    # Verwende das aktuelle Verzeichnis als Basis
    base_dir = os.path.abspath('.')
    
    print(f"Basis-Verzeichnis: {base_dir}")
    
    # Stelle sicher, dass alle wichtigen Verzeichnisse existieren
    critical_dirs = [
        'swissairdry',
        'swissairdry/api',
        'swissairdry/api/app',
        'swissairdry/api/app/routes',
        'swissairdry/api/app/routers',
        'swissairdry/db',
        'swissairdry/mqtt',
        'swissairdry/nextcloud',
        'swissairdry/integration',
        'swissairdry/integration/deck',
        'swissairdry/ExApp',
    ]
    
    for d in critical_dirs:
        full_path = os.path.join(base_dir, d)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
            print(f"Verzeichnis erstellt: {full_path}")
    
    # __init__.py Dateien erstellen
    created_files = create_init_files(base_dir)
    print(f"Insgesamt {len(created_files)} __init__.py Dateien erstellt.")
    
    # Stelle sicher, dass kritische Konfigurationsdateien vorhanden sind
    ensure_critical_files()
    
    print("\nPaketstruktur korrigiert! Die Builds sollten jetzt erfolgreich sein.")
    return 0


if __name__ == "__main__":
    sys.exit(main())