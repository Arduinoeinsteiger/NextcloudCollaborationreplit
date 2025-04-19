# ESP32C6 Bibliotheken-Installation

Um den ESP32C6 mit der neuen MQTT-Implementierung korrekt zu kompilieren, müssen folgende Bibliotheken im Arduino IDE installiert werden:

## Erforderliche Bibliotheken

1. **ESP32 Core** (neueste Version 3.x, mindestens 3.2.0)
   - Über Arduino-Boardverwalter installieren
   - Wähle "ESP32-C6" als Board

2. **ArduinoJson** (neueste Version 7.x)
   - Über Bibliotheksverwalter installieren

3. **TFT_eSPI** (neueste Version, mindestens 2.5.43)
   - Über Bibliotheksverwalter installieren
   - Konfiguration für 1.47" Display mit ST7789 Treiber anpassen (siehe unten)

4. **QRCode** von Richard Moore
   - Über Bibliotheksverwalter installieren (suche nach "qrcode")

## TFT_eSPI Konfiguration für 1.47" Display (172x320)

Um das 1.47" Display korrekt zu konfigurieren, müssen Sie die `User_Setup.h` in der TFT_eSPI-Bibliothek anpassen:

1. Navigieren Sie zum Bibliotheksordner (z.B. `Documents/Arduino/libraries/TFT_eSPI`)
2. Öffnen Sie die Datei `User_Setup.h`
3. Kommentieren Sie alle vordefinierten Displays aus
4. Fügen Sie folgende Zeilen hinzu:

```cpp
// Konfiguration für 1.47" Display (172x320) mit ST7789 Treiber
#define ST7789_DRIVER
#define TFT_WIDTH  172
#define TFT_HEIGHT 320
#define TFT_RGB_ORDER TFT_BGR  // Farbreihenfolge anpassen (kann je nach Display variieren)
```

4. Definieren Sie die Pins für SPI:

```cpp
// ESP32-C6 XIAO Pins für Display
#define TFT_MISO -1  // Nicht verwendet
#define TFT_MOSI 7   // SDA
#define TFT_SCLK 8   // SCL
#define TFT_CS   9   // CS
#define TFT_DC   6   // DC
#define TFT_RST  5   // RESET
```

## Wichtiger Hinweis zur MQTT-Bibliothek

Die neue Implementierung verwendet die native ESP32-MQTT-Bibliothek (`mqtt_client.h`), die bereits im ESP32-Core enthalten ist. Sie müssen **keine** externe PubSubClient-Bibliothek installieren.

Diese native MQTT-Implementierung bietet folgende Vorteile:
- Bessere Leistung und Stabilität
- Automatische Wiederverbindung
- SSL/TLS-Unterstützung
- Geringerer Speicherverbrauch
- Optimiert für neuere ESP32-Chips wie den ESP32-C6

## Partitionierung

Die beigefügte `partitions.csv` bietet ein erweitertes Partitionsschema mit:
- Mehr Speicher für OTA-Updates (2x 2.5MB)
- Größerer SPIFFS-Bereich für Daten (ca. 11MB)

Vergewissern Sie sich, dass diese Partitionsdatei beim Kompilieren verwendet wird. In der Arduino IDE können Sie dies über Werkzeuge > Partitionierungsschema > "Custom Partition" auswählen und den Pfad zur `partitions.csv` angeben.

## Fehlersuche

Sollte die Kompilierung fehlschlagen:

1. Überprüfen Sie, ob Sie die richtige Board-Version ausgewählt haben (ESP32-C6)
2. Stellen Sie sicher, dass alle oben genannten Bibliotheken installiert sind
3. Überprüfen Sie die TFT_eSPI-Konfiguration
4. Überprüfen Sie die Partitionstabelle