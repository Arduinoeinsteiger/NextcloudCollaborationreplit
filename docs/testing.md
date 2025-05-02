# SwissAirDry Testsuite

Dieses Dokument beschreibt die Testsuite für das SwissAirDry-Projekt.

## Übersicht

Die SwissAirDry Testsuite enthält Tests für verschiedene Komponenten des Systems:

- API-Server-Tests
- QR-Code-Generator-Tests
- MQTT-Client-Tests

## Testausführung

Um alle Tests auszuführen, verwenden Sie:

```bash
cd swissairdry
python -m unittest discover
```

Um spezifische Tests auszuführen:

```bash
python -m unittest api.tests.test_qrcode_generator
```

## Testabdeckung

Um einen Testabdeckungsbericht zu erstellen:

```bash
pip install coverage
coverage run -m unittest discover
coverage report
coverage html  # Erstellt einen HTML-Bericht in htmlcov/
```

## Teststruktur

Die Tests sind wie folgt organisiert:

```
swissairdry/
└── api/
    └── tests/
        ├── __init__.py
        ├── test_qrcode_generator.py
        └── test_minimal_http_server.py
```

## QR-Code-Generator-Tests

Die Tests für den QR-Code-Generator (`test_qrcode_generator.py`) überprüfen:

- Grundlegende QR-Code-Generierung
- WLAN-Konfigurationsformat
- Gerätekonfigurationsformat
- HTML-Ausgabe
- PNG-Ausgabe
- QR-Code-Generator-Webseite

## Hinweise zur Testentwicklung

- **Mock-Objekte**: Verwenden Sie Mock-Objekte, um externe Abhängigkeiten zu isolieren
- **Testabdeckung**: Streben Sie eine Testabdeckung von mindestens 80% an
- **Dokumentation**: Dokumentieren Sie jeden Test und seine Testfälle
- **Unabhängigkeit**: Tests sollten unabhängig voneinander sein und keine gemeinsamen Zustände teilen
- **Überspringen**: Verwenden Sie `@unittest.skipIf` oder `@unittest.skipUnless`, um Tests zu überspringen, wenn Voraussetzungen nicht erfüllt sind

## Integration in CI/CD

Die Tests werden automatisch in der CI/CD-Pipeline ausgeführt. Ein fehlgeschlagener Test verhindert das Deployment.