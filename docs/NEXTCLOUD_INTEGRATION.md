# SwissAirDry Nextcloud-Integration

Diese Anleitung erklärt, wie Sie die SwissAirDry-Anwendung als externe App in Ihre Nextcloud-Instanz integrieren können, ohne dass es zu Abstürzen oder Instabilitäten kommt.

## Voraussetzungen

- Eine laufende Nextcloud-Instanz (Version 25 oder höher)
- Administratorzugriff auf die Nextcloud-Instanz
- Ein laufender SwissAirDry API-Server

## Installation der SwissAirDry-App in Nextcloud

### 1. Kopieren der App-Dateien

Kopieren Sie den Inhalt des Verzeichnisses `swissairdry/nextcloud/app` in das Apps-Verzeichnis Ihrer Nextcloud-Installation:

```bash
cp -r swissairdry/nextcloud/app /path/to/nextcloud/apps/swissairdry
```

Stellen Sie sicher, dass die Dateien die richtigen Berechtigungen haben:

```bash
chown -R www-data:www-data /path/to/nextcloud/apps/swissairdry
```

### 2. Aktivieren der App in Nextcloud

Melden Sie sich als Administrator bei Ihrer Nextcloud-Instanz an und gehen Sie zu:

**Einstellungen** → **Apps** → **Deaktivierte Apps**

Hier sollten Sie "Swiss Air Dry" finden. Klicken Sie auf den "Aktivieren"-Button.

### 3. Konfiguration der App

Nach der Aktivierung müssen Sie die App konfigurieren. Gehen Sie zu:

**Einstellungen** → **Administration** → **Swiss Air Dry**

Geben Sie die folgenden Informationen ein:
- API-Server-URL: Die vollständige URL zu Ihrem SwissAirDry API-Server (z.B. https://api.swissairdry.com)
- API-Schlüssel: Der API-Schlüssel für die Authentifizierung bei der API

## Stable Integration als External App

Die SwissAirDry-App ist als "External App" konfiguriert, was bedeutet, dass sie in einem iframe läuft und nicht direkt in den Nextcloud-PHP-Code integriert ist. Dies verbessert die Stabilität und verhindert Abstürze der Nextcloud-Instanz.

### Konfigurationsdatei info.xml

Die wichtigste Konfiguration befindet sich in der Datei `info.xml`:

```xml
<external-app>
    <load-parallel/>
    <iframe id="frame" src="https://api.swissairdry.com/nextcloud?origin={{origin}}&amp;url={{url}}"/>
    <iframe-selector>@import @nextcloud/dialogs;</iframe-selector>
</external-app>
```

Diese Konfiguration sorgt dafür, dass:
- Die App parallel geladen wird (`load-parallel`) und nicht den Hauptthread von Nextcloud blockiert
- Die App in einem iframe läuft, der auf den SwissAirDry API-Server verweist
- Der iframe mit der korrekten Herkunft und URL konfiguriert ist

## Fehlerbehebung bei der Integration

### Problem: Nextcloud stürzt ab

Wenn Ihre Nextcloud-Instanz beim Zugriff auf die SwissAirDry-App abstürzt, überprüfen Sie:

1. Ist die `info.xml` korrekt konfiguriert mit dem `<external-app>`-Tag?
2. Läuft der API-Server und ist er erreichbar?
3. Stimmen die Pfade in der iframe-src-URL?

### Problem: Keine Verbindung zum API-Server

Wenn die App keine Verbindung zum API-Server herstellen kann:

1. Überprüfen Sie, ob der API-Server läuft
2. Stellen Sie sicher, dass die URL in der `info.xml` korrekt ist
3. Überprüfen Sie, ob CORS richtig konfiguriert ist und Anfragen von Ihrer Nextcloud-Domäne zulässt

### Problem: Authentifizierungsfehler

Wenn Sie Authentifizierungsfehler sehen:

1. Überprüfen Sie, ob der API-Schlüssel korrekt ist
2. Stellen Sie sicher, dass die Nextcloud-Instanz als vertrauenswürdiger Client im API-Server konfiguriert ist

## Best Practices für eine stabile Integration

1. **Vermeiden Sie Direkte PHP-Integration**: Nutzen Sie immer den External-App-Ansatz mit einem iframe.
2. **Minimieren Sie API-Aufrufe**: Reduzieren Sie die Anzahl der API-Aufrufe, um die Last auf beiden Systemen zu verringern.
3. **Implementieren Sie Caching**: Zwischenspeichern von API-Ergebnissen im Frontend, um wiederholte Anfragen zu vermeiden.
4. **Fehlerbehandlung**: Implementieren Sie robuste Fehlerbehandlung, um Abstürze bei Netzwerkproblemen zu vermeiden.
5. **Logging**: Aktivieren Sie detailliertes Logging sowohl in Nextcloud als auch im API-Server zur einfacheren Fehlerbehebung.

## Aktualisierung der Integration

Beim Aktualisieren der SwissAirDry-App:

1. Deaktivieren Sie die App in Nextcloud
2. Ersetzen Sie die App-Dateien durch die neuen Versionen
3. Aktivieren Sie die App wieder
4. Überprüfen Sie die Konfiguration

## Sicherheitshinweise

- Verwenden Sie immer HTTPS für die Kommunikation zwischen Nextcloud und dem API-Server
- Beschränken Sie CORS-Zugriff auf vertrauenswürdige Domains
- Rotieren Sie API-Schlüssel regelmäßig
- Begrenzen Sie die Berechtigungen des Nextcloud-Integrationskontos auf das Notwendige