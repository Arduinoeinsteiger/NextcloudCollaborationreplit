# SwissAirDry QR-Code Generator

Der SwissAirDry QR-Code Generator ist ein integriertes Werkzeug, das die schnelle Konfiguration von SwissAirDry-Geräten ermöglicht. Mit diesem Generator können Sie QR-Codes erstellen, die von der SwissAirDry App gescannt werden können, um Geräte automatisch zu konfigurieren.

## Funktionen

- Erstellen von QR-Codes mit benutzerdefinierten Konfigurationsdaten
- Anpassbare Größe und Titel
- Ausgabe als HTML (mit eingebettetem Bild und Download-Option) oder direkt als PNG-Bild
- Vordefinierte Konfigurationen für gängige Anwendungsfälle

## Verwendung

### Über die Webschnittstelle

1. Öffnen Sie den QR-Code Generator unter `/qrcode`
2. Geben Sie die Konfigurationsdaten ein
3. Passen Sie Titel, Größe und Format an
4. Klicken Sie auf "QR-Code generieren"
5. Der generierte QR-Code kann direkt heruntergeladen werden

### Über die API

Der QR-Code Generator kann auch direkt über die API aufgerufen werden:

```
GET /qrcode?data=KONFIGURATIONSDATEN&title=TITEL&size=GRÖSSE&format=FORMAT
```

#### Parameter

| Parameter | Beschreibung | Standardwert |
|-----------|--------------|--------------|
| data | Zu codierende Konfigurationsdaten | (erforderlich) |
| title | Titel des QR-Codes | "SwissAirDry Konfiguration" |
| size | Größe in Pixeln (100-800) | 300 |
| format | Ausgabeformat (html oder png) | png |

#### Beispiele

**WLAN-Konfiguration:**
```
/qrcode?data=WLAN:T:WPA;S:MeinNetzwerk;P:MeinPasswort;;&format=html
```

**Gerätekonfiguration:**
```
/qrcode?data={"device_id":"device001","server":"192.168.1.100:5002","mode":"standard"}&title=Gerätekonfiguration
```

## Unterstützte Datenformate

### WLAN-Konfiguration

Für die Konfiguration von WLAN-Netzwerken wird das Format `WLAN:T:TYP;S:SSID;P:PASSWORT;;` verwendet, wobei:

- `T:` der Typ des Netzwerks ist (WPA, WEP, OPEN)
- `S:` die SSID (Netzwerkname) ist
- `P:` das Passwort ist

### Gerätekonfiguration

Für die Konfiguration von Geräten wird ein JSON-Format verwendet:

```json
{
  "device_id": "GERÄTE-ID",
  "server": "SERVER:PORT",
  "mode": "MODUS"
}
```

## Integration in Apps

Der generierte QR-Code kann von der SwissAirDry App gescannt werden, um die enthaltenen Konfigurationsdaten automatisch zu übernehmen. Dies vereinfacht die Einrichtung neuer Geräte erheblich.

## Sicherheitshinweise

- QR-Codes mit sensiblen Daten (z.B. WLAN-Passwörter) sollten nicht öffentlich zugänglich gemacht werden
- Die Daten werden nicht verschlüsselt im QR-Code gespeichert
- Es wird empfohlen, nach der Konfiguration die QR-Codes zu löschen, um unbefugten Zugriff zu vermeiden