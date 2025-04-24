# SwissAirDry Nextcloud Integration

Diese Integration ermöglicht die Einbindung von SwissAirDry in Nextcloud über das External App Framework.

## Übersicht

Die SwissAirDry-App für Nextcloud ist als "External App" implementiert, was bedeutet, dass sie in einem iframe ausgeführt wird und nicht direkt in den Nextcloud-PHP-Code integriert ist. Diese Architektur verbessert die Stabilität und verhindert Abstürze der Nextcloud-Instanz.

## Installation

### Voraussetzungen

- Nextcloud Version 25 oder höher
- SwissAirDry API-Server, der erreichbar ist von der Nextcloud-Instanz

### Manuelle Installation

1. Kopieren Sie den Ordner `swissairdry` in das `apps`-Verzeichnis Ihrer Nextcloud-Installation:

```bash
cp -r swissairdry /pfad/zu/nextcloud/apps/
```

2. Aktivieren Sie die App über die Nextcloud-Kommandozeile:

```bash
cd /pfad/zu/nextcloud
sudo -u www-data php occ app:enable swissairdry
```

## Konfiguration

Die Hauptkonfigurationsdatei ist `appinfo/info.xml`, die definiert, wie die App in Nextcloud eingebunden wird.

Die External App wird durch diesen XML-Block konfiguriert:

```xml
<external-app>
    <load-parallel/>
    <iframe id="frame" src="https://swissairdry.ch/api/nextcloud?origin={{origin}}&amp;url={{url}}"/>
    <iframe-selector>@import @nextcloud/dialogs;</iframe-selector>
</external-app>
```

Diese Konfiguration sorgt dafür, dass:

- Die App parallel geladen wird (`load-parallel`) und nicht den Hauptthread von Nextcloud blockiert
- Die App in einem iframe läuft, der auf den SwissAirDry API-Server verweist
- Der iframe mit der korrekten Herkunft und URL konfiguriert ist

## Fehlerbehebung

### Problem: Nextcloud stürzt ab

Wenn Ihre Nextcloud-Instanz beim Zugriff auf die SwissAirDry-App abstürzt:

1. Prüfen Sie, ob die `info.xml` korrekt konfiguriert ist mit dem `<external-app>`-Tag
2. Überprüfen Sie, ob der API-Server läuft und von Nextcloud aus erreichbar ist
3. Prüfen Sie die CORS-Einstellungen des API-Servers
4. Schauen Sie in die Nextcloud-Logs für weitere Hinweise auf Probleme

### Problem: Iframe bleibt leer oder zeigt einen Fehler

Wenn der iframe leer bleibt oder einen Fehler anzeigt:

1. Überprüfen Sie die URL des API-Servers in der `info.xml`
2. Stellen Sie sicher, dass die API korrekt konfiguriert ist, um Anfragen vom Nextcloud-Origin zu akzeptieren
3. Prüfen Sie die Browser-Konsole auf CORS-Fehler oder andere JavaScript-Fehler

## Sicherheitshinweise

- Die External App kommuniziert direkt mit dem API-Server, dadurch bleiben sensible Daten außerhalb der Nextcloud-Datenbank
- Stellen Sie sicher, dass die Kommunikation zwischen Nextcloud und dem API-Server über HTTPS erfolgt
- Der API-Server sollte so konfiguriert sein, dass er nur autorisierte Anfragen akzeptiert