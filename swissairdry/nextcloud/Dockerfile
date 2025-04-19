FROM python:3.11-slim

WORKDIR /app

# Kopieren der Anforderungen und Installation der Abhängigkeiten
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Kopieren der App-Dateien
COPY lib /app/lib/
COPY templates /app/templates/
COPY static /app/static/

# Umgebungsvariablen
ENV PYTHONUNBUFFERED=1 
ENV PORT=8000

# Startskript für Gesundheitscheck
COPY --chmod=775 healthcheck.sh /

# Starten der Anwendung
WORKDIR /app/lib
ENTRYPOINT ["python", "main.py"]

# Gesundheitscheck für Container
HEALTHCHECK --interval=5s --timeout=3s --retries=3 CMD /healthcheck.sh