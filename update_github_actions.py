#!/usr/bin/env python3
"""
Dieses Skript aktualisiert alle GitHub Actions auf die neuesten Versionen in der CI-Workflow-Datei.
Es aktualisiert:
- actions/checkout von v3 auf v4
- actions/setup-python von v4 (beibehaltend)
- actions/cache von v3 auf v4
- actions/upload-artifact von v3 auf v4
- actions/setup-node von v3 auf v4
- andstor/file-existence-action von v2 auf v2 (beibehaltend)
- shivammathur/setup-php von v2 auf v2 (beibehaltend)
"""

import re
import os

def update_action_versions(file_path):
    """GitHub Actions auf neueste Versionen aktualisieren."""
    updates = {
        r'uses: actions/checkout@v3': 'uses: actions/checkout@v4',
        r'uses: actions/cache@v3': 'uses: actions/cache@v4',
        r'uses: actions/upload-artifact@v3': 'uses: actions/upload-artifact@v4',
        r'uses: actions/setup-node@v3': 'uses: actions/setup-node@v4',
    }
    
    if not os.path.exists(file_path):
        print(f"Datei nicht gefunden: {file_path}")
        return False
    
    with open(file_path, 'r') as file:
        content = file.read()
    
    original_content = content
    for pattern, replacement in updates.items():
        content = re.sub(pattern, replacement, content)
    
    if content != original_content:
        with open(file_path, 'w') as file:
            file.write(content)
        print(f"Datei {file_path} aktualisiert.")
        return True
    else:
        print(f"Keine Änderungen in {file_path} notwendig.")
        return False

def main():
    """Hauptfunktion, die alle CI-Workflow-Dateien aktualisiert."""
    workflows_dir = '.github/workflows'
    
    if not os.path.exists(workflows_dir):
        print(f"Verzeichnis nicht gefunden: {workflows_dir}")
        return
    
    updated_files = 0
    for filename in os.listdir(workflows_dir):
        if filename.endswith('.yml') or filename.endswith('.yaml'):
            file_path = os.path.join(workflows_dir, filename)
            if update_action_versions(file_path):
                updated_files += 1
    
    print(f"{updated_files} Dateien wurden aktualisiert.")

if __name__ == "__main__":
    main()