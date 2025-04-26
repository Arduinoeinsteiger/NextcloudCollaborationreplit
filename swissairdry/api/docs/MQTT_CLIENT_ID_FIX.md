# MQTT Client-ID-Konfliktbehebung für SwissAirDry

## Problem

In der SwissAirDry API traten MQTT-Client-ID-Konflikte auf, wenn mehrere Instanzen der API gleichzeitig liefen. Dies führte zu Fehlern wie:

```
MQTT-Verbindung nicht autorisiert (Code 7), Client-ID-Konflikt möglich
```

Jeder MQTT-Client benötigt eine eindeutige Client-ID. Wenn mehrere Clients die gleiche ID verwenden, verweigert der MQTT-Broker die Verbindung für die nachfolgenden Verbindungsversuche.

## Lösung

Die Client-ID-Generierung wurde in beiden API-Implementierungen (simple_app.py und mqtt_client.py) verbessert, um garantiert eindeutige Client-IDs zu erzeugen, selbst wenn mehrere Instanzen parallel laufen.

### 1. In swissairdry/api/mqtt_client.py

Die Client-ID-Generierung wurde mit mehreren Zufallsfaktoren erweitert:

```python
# Generiere eine garantiert eindeutige Client-ID mit mehreren Faktoren
unique_id = str(uuid.uuid4()).replace('-', '')[:8]
timestamp = int(time.time() * 1000)  # Millisekunden für noch mehr Einzigartigkeit
pid = os.getpid()  # Process-ID für Eindeutigkeit bei mehreren Prozessen
hostname = socket.gethostname()[:8]  # Hostname für Eindeutigkeit auf mehreren Hosts
random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

# Format: sard-{uuid}-{timestamp}-{pid}-{hostname}-{random}
self.client_id = f"sard-{unique_id}-{timestamp}-{pid}-{hostname}-{random_suffix}"
```

### 2. In swissairdry/api/simple_app.py

Ähnliche Verbesserungen wurden in der einfachen API-Implementierung vorgenommen:

```python
# Mehr Zufallsfaktoren für garantiert einzigartige Client-ID
uid = str(uuid.uuid4()).replace('-', '')[:8]
timestamp = int(time.time() * 1000)
pid = os.getpid()
hostname = socket.gethostname()[:8] if hasattr(socket, 'gethostname') else 'local'
random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

# Format: sard-simple-{uuid}-{timestamp}-{pid}-{hostname}-{random}
client_id = f"sard-simple-{uid}-{timestamp}-{pid}-{hostname}-{random_str}"
```

## Verwendete Faktoren für die Eindeutigkeit:

1. **UUID**: Zufälliger universell eindeutiger Bezeichner
2. **Timestamp**: Aktuelle Zeit in Millisekunden, garantiert Einzigartigkeit bei sequentiellen Starts
3. **Prozess-ID (PID)**: Eindeutig innerhalb eines Systems für gleichzeitig laufende Prozesse
4. **Hostname**: Eindeutig in Netzwerken und Multi-Container-Umgebungen
5. **Zufällige alphanumerische Zeichenfolge**: Zusätzliche Zufälligkeit für maximale Sicherheit

Die resultierende Client-ID ist so konzipiert, dass sie selbst in großen Netzwerken und Umgebungen mit vielen gleichzeitigen Verbindungen garantiert eindeutig ist.

## Wiederverbindungslogik

Zusätzlich wurde in der Haupt-API eine Wiederverbindungslogik implementiert, die bei einem erkannten Client-ID-Konflikt eine neue ID generiert und eine Wiederverbindung initiiert.

## Tests

Tests haben gezeigt, dass beide API-Instanzen jetzt erfolgreich parallel laufen können, ohne Client-ID-Konflikte zu verursachen. Die Logs zeigen, dass beide Clients unterschiedliche eindeutige IDs verwenden und sich erfolgreich mit dem MQTT-Broker verbinden.