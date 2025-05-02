#!/bin/bash

# SwissAirDry Daten-Bereinigungsskript
# Dieses Skript bereinigt die Dateistruktur und organisiert die Daten übersichtlich

# Farbige Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}===========================================================${NC}"
echo -e "${BLUE}     SwissAirDry Daten-Aufräumungstool     ${NC}"
echo -e "${BLUE}===========================================================${NC}"
echo ""

# Funktion zum Anzeigen von Status-Meldungen
function status_message() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Funktion zum Anzeigen von Erfolgs-Meldungen
function success_message() {
    echo -e "${GREEN}[ERFOLG]${NC} $1"
}

# Funktion zum Anzeigen von Warnungen
function warning_message() {
    echo -e "${YELLOW}[WARNUNG]${NC} $1"
}

# Funktion zum Anzeigen von Fehlern
function error_message() {
    echo -e "${RED}[FEHLER]${NC} $1"
}

# Funktion zum Aufräumen von Duplikaten
function cleanup_duplicates() {
    status_message "Suche nach doppelten Dateien..."
    
    # Erstelle temporäre Datei für die Hash-Werte
    TMP_FILE=$(mktemp)
    
    # Berechne MD5-Hashes für alle Dateien
    find . -type f -not -path "*/\.*" -not -path "*/node_modules/*" -exec md5sum {} \; > "$TMP_FILE"
    
    # Zähle Duplikate
    DUPLICATE_COUNT=$(sort "$TMP_FILE" | cut -d ' ' -f 1 | uniq -d | wc -l)
    
    if [ "$DUPLICATE_COUNT" -eq 0 ]; then
        success_message "Keine doppelten Dateien gefunden."
    else
        warning_message "$DUPLICATE_COUNT doppelte Dateien gefunden."
        
        # Erstelle ein Backup-Verzeichnis
        mkdir -p duplicates_backup
        
        # Hole die doppelten Dateien
        DUPLICATES=$(sort "$TMP_FILE" | cut -d ' ' -f 1 | uniq -d)
        
        for hash in $DUPLICATES; do
            # Finde die Dateien mit diesem Hash
            FILES=$(grep "$hash" "$TMP_FILE" | cut -d ' ' -f 3-)
            
            # Behalte die erste Datei, verschiebe die anderen in das Backup-Verzeichnis
            FIRST_FILE=""
            for file in $FILES; do
                if [ -z "$FIRST_FILE" ]; then
                    FIRST_FILE="$file"
                    echo -e "- Behalte: ${CYAN}$file${NC}"
                else
                    echo -e "- Duplikat: $file -> ${YELLOW}duplicates_backup/$(basename "$file")${NC}"
                    cp "$file" "duplicates_backup/$(basename "$file")"
                    rm "$file"
                fi
            done
        done
        
        success_message "Doppelte Dateien wurden in 'duplicates_backup' verschoben."
    fi
    
    # Entferne temporäre Datei
    rm "$TMP_FILE"
}

# Funktion zum Aufräumen temporärer Dateien
function cleanup_temp_files() {
    status_message "Suche nach temporären Dateien..."
    
    # Bekannte temporäre Dateiendungen
    TEMP_EXTENSIONS=("tmp" "temp" "bak" "swp" "~" "log")
    
    TOTAL_REMOVED=0
    
    # Erstelle ein Backup-Verzeichnis
    mkdir -p temp_files_backup
    
    # Suche nach Dateien mit temporären Endungen
    for ext in "${TEMP_EXTENSIONS[@]}"; do
        # Finde temporäre Dateien
        TEMP_FILES=$(find . -type f -name "*.$ext" -not -path "*/\.*" -not -path "*/node_modules/*")
        
        # Zähle und verschiebe temporäre Dateien
        COUNT=0
        for file in $TEMP_FILES; do
            echo -e "- Temporäre Datei: $file -> ${YELLOW}temp_files_backup/$(basename "$file")${NC}"
            cp "$file" "temp_files_backup/$(basename "$file")"
            rm "$file"
            COUNT=$((COUNT+1))
        done
        
        TOTAL_REMOVED=$((TOTAL_REMOVED+COUNT))
        
        if [ "$COUNT" -gt 0 ]; then
            success_message "$COUNT temporäre Dateien mit Endung *.$ext entfernt."
        fi
    done
    
    if [ "$TOTAL_REMOVED" -eq 0 ]; then
        success_message "Keine temporären Dateien gefunden."
    else
        success_message "Insgesamt $TOTAL_REMOVED temporäre Dateien wurden in 'temp_files_backup' verschoben."
    fi
}

# Funktion zum Aufräumen leerer Verzeichnisse
function cleanup_empty_directories() {
    status_message "Suche nach leeren Verzeichnissen..."
    
    # Finde leere Verzeichnisse
    EMPTY_DIRS=$(find . -type d -empty -not -path "*/\.*" -not -path "*/node_modules/*")
    
    COUNT=0
    for dir in $EMPTY_DIRS; do
        echo -e "- Leeres Verzeichnis: $dir"
        rmdir "$dir"
        COUNT=$((COUNT+1))
    done
    
    if [ "$COUNT" -eq 0 ]; then
        success_message "Keine leeren Verzeichnisse gefunden."
    else
        success_message "$COUNT leere Verzeichnisse wurden entfernt."
    fi
}

# Funktion zum Ordnen von Dateien nach Typ
function organize_files_by_type() {
    status_message "Ordne Dateien nach Typ..."
    
    # Erstelle Verzeichnisse für verschiedene Dateitypen
    mkdir -p organized_files/documents
    mkdir -p organized_files/images
    mkdir -p organized_files/code
    mkdir -p organized_files/archives
    mkdir -p organized_files/others
    
    # Sortiere Dateien nach Typ
    COUNT_DOCS=0
    COUNT_IMGS=0
    COUNT_CODE=0
    COUNT_ARCH=0
    COUNT_OTHERS=0
    
    # Gehe nur durch die Root-Verzeichnisse
    for file in *; do
        if [ -f "$file" ]; then
            # Bestimme den Dateityp
            TYPE=""
            EXTENSION="${file##*.}"
            
            case "$EXTENSION" in
                pdf|doc|docx|txt|md|odt|rtf|tex)
                    TYPE="documents"
                    COUNT_DOCS=$((COUNT_DOCS+1))
                    ;;
                jpg|jpeg|png|gif|bmp|svg|webp|avif)
                    TYPE="images"
                    COUNT_IMGS=$((COUNT_IMGS+1))
                    ;;
                py|js|html|css|ts|jsx|tsx|c|cpp|h|hpp|java|rs|go|php)
                    TYPE="code"
                    COUNT_CODE=$((COUNT_CODE+1))
                    ;;
                zip|tar|gz|rar|7z|bz2|xz)
                    TYPE="archives"
                    COUNT_ARCH=$((COUNT_ARCH+1))
                    ;;
                *)
                    TYPE="others"
                    COUNT_OTHERS=$((COUNT_OTHERS+1))
                    ;;
            esac
            
            # Kopiere die Datei in das entsprechende Verzeichnis
            if [ -f "$file" ] && [ "$TYPE" != "" ]; then
                cp "$file" "organized_files/$TYPE/"
                echo -e "- Organisierte Datei: $file -> ${CYAN}organized_files/$TYPE/$(basename "$file")${NC}"
            fi
        fi
    done
    
    success_message "Dateien sortiert: $COUNT_DOCS Dokumente, $COUNT_IMGS Bilder, $COUNT_CODE Code-Dateien, $COUNT_ARCH Archive, $COUNT_OTHERS Sonstige"
}

# Funktion zum Erstellen einer Dateiübersicht
function create_file_index() {
    status_message "Erstelle Dateiindex..."
    
    # Dateiindex-Datei
    INDEX_FILE="file_index.md"
    
    # Überschrift
    echo "# SwissAirDry Dateiindex" > "$INDEX_FILE"
    echo "" >> "$INDEX_FILE"
    echo "Erstellt am: $(date '+%Y-%m-%d %H:%M:%S')" >> "$INDEX_FILE"
    echo "" >> "$INDEX_FILE"
    
    # Erstelle eine Tabelle der Dateien
    echo "## Dateien nach Verzeichnis" >> "$INDEX_FILE"
    echo "" >> "$INDEX_FILE"
    
    # Durchlaufe alle Verzeichnisse und sammle Dateinamen
    for dir in $(find . -type d -not -path "*/\.*" -not -path "*/node_modules/*" -not -path "./duplicates_backup*" -not -path "./temp_files_backup*" -not -path "./organized_files*" | sort); do
        # Zähle die Dateien im Verzeichnis
        FILE_COUNT=$(find "$dir" -maxdepth 1 -type f | wc -l)
        
        if [ "$FILE_COUNT" -gt 0 ]; then
            echo "### $dir ($FILE_COUNT Dateien)" >> "$INDEX_FILE"
            echo "" >> "$INDEX_FILE"
            echo "| Dateiname | Typ | Größe | Letzte Änderung |" >> "$INDEX_FILE"
            echo "|-----------|-----|-------|-----------------|" >> "$INDEX_FILE"
            
            # Füge Dateien hinzu
            for file in $(find "$dir" -maxdepth 1 -type f | sort); do
                FILENAME=$(basename "$file")
                EXTENSION="${FILENAME##*.}"
                SIZE=$(du -h "$file" | cut -f1)
                MODIFIED=$(stat -c %y "$file" | cut -d' ' -f1)
                
                echo "| $FILENAME | $EXTENSION | $SIZE | $MODIFIED |" >> "$INDEX_FILE"
            done
            
            echo "" >> "$INDEX_FILE"
        fi
    done
    
    # Erstelle eine Zusammenfassung
    echo "## Zusammenfassung" >> "$INDEX_FILE"
    echo "" >> "$INDEX_FILE"
    
    TOTAL_FILES=$(find . -type f -not -path "*/\.*" -not -path "*/node_modules/*" -not -path "./duplicates_backup*" -not -path "./temp_files_backup*" -not -path "./organized_files*" | wc -l)
    TOTAL_DIRS=$(find . -type d -not -path "*/\.*" -not -path "*/node_modules/*" -not -path "./duplicates_backup*" -not -path "./temp_files_backup*" -not -path "./organized_files*" | wc -l)
    
    echo "- Gesamtzahl der Dateien: $TOTAL_FILES" >> "$INDEX_FILE"
    echo "- Gesamtzahl der Verzeichnisse: $TOTAL_DIRS" >> "$INDEX_FILE"
    echo "" >> "$INDEX_FILE"
    
    # Dateien nach Typ
    echo "### Dateien nach Typ" >> "$INDEX_FILE"
    echo "" >> "$INDEX_FILE"
    
    # Sammle häufige Dateitypen
    echo "| Dateityp | Anzahl |" >> "$INDEX_FILE"
    echo "|----------|--------|" >> "$INDEX_FILE"
    
    find . -type f -not -path "*/\.*" -not -path "*/node_modules/*" -not -path "./duplicates_backup*" -not -path "./temp_files_backup*" -not -path "./organized_files*" -name "*.*" | grep -o '\.[^\.]*$' | sort | uniq -c | sort -nr | while read -r count ext; do
        echo "| ${ext:1} | $count |" >> "$INDEX_FILE"
    done
    
    success_message "Dateiindex wurde erstellt: $INDEX_FILE"
}

# Hauptfunktion
function main() {
    echo -e "${YELLOW}Dieses Skript bereinigt und organisiert die Daten im Projekt.${NC}"
    echo -e "${YELLOW}Es werden Backups erstellt, bevor Dateien verschoben oder gelöscht werden.${NC}"
    echo ""
    read -p "Möchten Sie fortfahren? (j/n): " choice
    
    if [[ "$choice" != "j" && "$choice" != "J" ]]; then
        status_message "Abbruch durch Benutzer."
        exit 0
    fi
    
    echo ""
    status_message "Beginne mit der Datenbereinigung..."
    echo ""
    
    # Führe alle Bereinigungsfunktionen aus
    cleanup_duplicates
    echo ""
    
    cleanup_temp_files
    echo ""
    
    cleanup_empty_directories
    echo ""
    
    organize_files_by_type
    echo ""
    
    create_file_index
    
    echo ""
    echo -e "${BLUE}===========================================================${NC}"
    echo -e "${BLUE}                   Bereinigung abgeschlossen               ${NC}"
    echo -e "${BLUE}===========================================================${NC}"
    
    success_message "Die Datenbereinigung wurde abgeschlossen."
    success_message "Eine Übersicht wurde in der Datei 'file_index.md' erstellt."
    success_message "Die Originaldateien bleiben unberührt, außer:"
    success_message "- Doppelte Dateien wurden in 'duplicates_backup/' gesichert"
    success_message "- Temporäre Dateien wurden in 'temp_files_backup/' gesichert"
    success_message "- Leere Verzeichnisse wurden entfernt"
    success_message "- Kopien aller Dateien, sortiert nach Typ, sind in 'organized_files/'"
    
    return 0
}

# Starte die Hauptfunktion
main