#!/usr/bin/env python3
"""
Dieses Skript repariert die Paketstruktur für die CI/CD-Pipeline.
Es erstellt alle notwendigen __init__.py Dateien in den Unterverzeichnissen
und sorgt dafür, dass die Paketstruktur korrekt ist.
"""

import os
import sys
from pathlib import Path


def create_init_files(base_dir):
    """Erstellt __init__.py Dateien in allen Python-Package-Verzeichnissen."""
    created_files = []

    # Iteriere durch alle Unterverzeichnisse
    for root, dirs, files in os.walk(base_dir):
        # Überspringe versteckte Verzeichnisse und spezielle Verzeichnisse
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'tests', 'build', 'dist']]
        
        # Prüfe, ob es sich um ein Python-Paket-Verzeichnis handelt (enthält .py Dateien)
        py_files = [f for f in files if f.endswith('.py')]
        
        # Wenn es .py Dateien gibt oder es ein Unterverzeichnis von swissairdry ist
        is_swissairdry_subdir = 'swissairdry' in root
        is_package_dir = len(py_files) > 0 or any('__init__.py' in os.listdir(os.path.join(root, d)) for d in dirs if os.path.isdir(os.path.join(root, d)))
        
        if is_swissairdry_subdir or is_package_dir:
            init_file = os.path.join(root, '__init__.py')
            
            # Wenn noch keine __init__.py existiert, erstelle eine
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    package_name = os.path.basename(root)
                    f.write(f'"""\n{package_name} Package\n\nDieses Modul ist Teil des SwissAirDry-Projekts.\n"""\n\n')
                created_files.append(init_file)
                print(f"Erstellt: {init_file}")
    
    return created_files


def main():
    """Hauptfunktion für die Ausführung des Skripts."""
    if len(sys.argv) > 1:
        base_dir = os.path.abspath(sys.argv[1])
    else:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    print(f"Basis-Verzeichnis: {base_dir}")
    
    # Stelle sicher, dass das swissairdry-Verzeichnis existiert
    swissairdry_dir = os.path.join(base_dir, 'swissairdry')
    if not os.path.isdir(swissairdry_dir):
        print(f"Fehler: Das swissairdry-Verzeichnis wurde nicht gefunden: {swissairdry_dir}", file=sys.stderr)
        return 1
    
    # Stelle sicher, dass kritische Verzeichnisse existieren
    critical_dirs = [
        'swissairdry/db',
        'swissairdry/mqtt',
        'swissairdry/nextcloud',
        'swissairdry/integration',
        'swissairdry/integration/deck',
        'swissairdry/api/app/routes',
        'swissairdry/api/app/routers',
        'swissairdry/ExApp',
        'swissairdry/esp',
        'swissairdry/mobile',
        'swissairdry/docs'
    ]
    
    for d in critical_dirs:
        full_path = os.path.join(base_dir, d)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
            print(f"Verzeichnis erstellt: {full_path}")
    
    # Erstelle __init__.py Dateien
    created_files = create_init_files(swissairdry_dir)
    print(f"Insgesamt {len(created_files)} __init__.py Dateien erstellt.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())