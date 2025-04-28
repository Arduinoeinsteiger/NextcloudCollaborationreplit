"""
Diagnose und Reparatur von fehlerhaften Importen in Python-Bibliotheken

Dieses Skript sucht nach fehlerhaften Importanweisungen, die durch eine fehlerhafte
Such-/Ersetzungsoperation entstanden sind, und korrigiert diese.

Problemmuster: 'from swissairdry..' wurde anstelle von 'from ..' in vielen Bibliotheksdateien eingefügt.
"""

import os
import sys
import re
from pathlib import Path
import fileinput

# Pfad zur Pythonumgebung
PYTHON_LIBS_PATH = '/home/runner/workspace/.pythonlibs/lib/python3.11/site-packages'

def find_problematic_files(base_path, pattern='swissairdry\\.\\.'):
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
                        if re.search(pattern, content):
                            problematic_files.append(file_path)
                            count += 1
                            if count % 10 == 0:
                                print(f"Bereits {count} problematische Dateien gefunden...")
                except Exception as e:
                    print(f"Fehler beim Lesen von {file_path}: {e}")
    
    print(f"Insgesamt {len(problematic_files)} problematische Dateien gefunden.")
    return problematic_files

def fix_problematic_imports(file_paths):
    """Korrigiert fehlerhafte Importanweisungen in den angegebenen Dateien."""
    pattern = r'from\s+swissairdry\.\.'
    replacement = 'from ..'
    
    print(f"Korrigiere {len(file_paths)} Dateien...")
    fixed_count = 0
    
    for file_path in file_paths:
        try:
            with fileinput.FileInput(file_path, inplace=True, backup='.bak') as file:
                for line in file:
                    fixed_line = re.sub(pattern, replacement, line)
                    print(fixed_line, end='')  # Wird in die Datei geschrieben
            
            fixed_count += 1
            if fixed_count % 10 == 0:
                print(f"Bereits {fixed_count} Dateien korrigiert...")
        except Exception as e:
            print(f"Fehler beim Korrigieren von {file_path}: {e}")
    
    print(f"Korrektur abgeschlossen. {fixed_count} Dateien wurden repariert.")

def main():
    print("Starte Diagnose und Reparatur von fehlerhaften Importanweisungen...")
    
    problematic_files = find_problematic_files(PYTHON_LIBS_PATH)
    
    if problematic_files:
        user_input = input(f"Möchten Sie {len(problematic_files)} Dateien korrigieren? (j/n): ")
        if user_input.lower() in ('j', 'ja', 'y', 'yes'):
            fix_problematic_imports(problematic_files)
            print("Reparatur abgeschlossen. Bitte starten Sie Ihre Anwendung neu.")
        else:
            print("Reparatur abgebrochen.")
    else:
        print("Keine problematischen Dateien gefunden.")

if __name__ == "__main__":
    main()