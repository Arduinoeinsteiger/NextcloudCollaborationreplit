"""
Umfassende Reparatur von fehlerhaften 'swissairdry' Importanweisungen in Python-Bibliotheken

Dieses Skript sucht nach allen Arten von fehlerhaften Importen, die 'swissairdry' enthalten,
und korrigiert sie basierend auf dem Kontext.
"""

import os
import re
import fileinput
from pathlib import Path

# Pfad zur Pythonumgebung
PYTHON_LIBS_PATH = '/home/runner/workspace/.pythonlibs/lib/python3.11/site-packages'

def find_problematic_files(base_path, pattern='swissairdry'):
    """Findet Dateien, die das problematische Importmuster enthalten."""
    problematic_files = []
    
    print(f"Suche nach Dateien mit Muster '{pattern}' in {base_path}")
    count = 0
    
    for root, _, files in os.walk(base_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if pattern in content:
                            problematic_files.append(file_path)
                            count += 1
                            if count % 10 == 0:
                                print(f"Bereits {count} problematische Dateien gefunden...")
                except Exception as e:
                    print(f"Fehler beim Lesen von {file_path}: {e}")
    
    print(f"Insgesamt {len(problematic_files)} problematische Dateien gefunden.")
    return problematic_files

def fix_problematic_imports(file_paths):
    """Korrigiert alle Arten von fehlerhaften swissairdry-Importanweisungen in den angegebenen Dateien."""
    # Verschiedene Muster und deren Ersetzungen
    replacements = [
        # Relative lokale Imports korrigieren
        (r'from\s+swissairdry\.\.\s+', 'from .. '),
        (r'from\s+swissairdry\.\s+', 'from . '),
        
        # Typische Werkzeug-Imports korrigieren
        (r'from\s+swissairdry\.serving\s+', 'from werkzeug.serving '),
        (r'import\s+swissairdry\.serving\s+', 'import werkzeug.serving '),
        
        # Andere typische Pakete
        (r'from\s+swissairdry\.wsgi\s+', 'from werkzeug.wsgi '),
        (r'import\s+swissairdry\.wsgi\s+', 'import werkzeug.wsgi '),
        
        # Allgemeine Ersetzung als Fallback
        (r'from\s+swissairdry\.', 'from werkzeug.'),
        (r'import\s+swissairdry\.', 'import werkzeug.'),
    ]
    
    print(f"Korrigiere {len(file_paths)} Dateien...")
    fixed_count = 0
    
    for file_path in file_paths:
        try:
            with fileinput.FileInput(file_path, inplace=True, backup='.bak') as file:
                for line in file:
                    fixed_line = line
                    for pattern, replacement in replacements:
                        fixed_line = re.sub(pattern, replacement, fixed_line)
                    print(fixed_line, end='')  # Wird in die Datei geschrieben
            
            fixed_count += 1
            if fixed_count % 10 == 0:
                print(f"Bereits {fixed_count} Dateien korrigiert...")
        except Exception as e:
            print(f"Fehler beim Korrigieren von {file_path}: {e}")
    
    print(f"Korrektur abgeschlossen. {fixed_count} Dateien wurden repariert.")

def main():
    print("Starte umfassende Reparatur von fehlerhaften swissairdry-Importanweisungen...")
    
    problematic_files = find_problematic_files(PYTHON_LIBS_PATH)
    
    if problematic_files:
        print(f"Es wurden {len(problematic_files)} problematische Dateien gefunden. Starte umfassende Reparatur...")
        fix_problematic_imports(problematic_files)
        print("Reparatur abgeschlossen. Bitte starten Sie Ihre Anwendung neu.")
    else:
        print("Keine problematischen Dateien gefunden.")

if __name__ == "__main__":
    main()