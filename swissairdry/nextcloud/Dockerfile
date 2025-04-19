FROM python:3.11-slim

WORKDIR /app

# Systemabhängigkeiten installieren
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python-Abhängigkeiten installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Anwendungsdateien kopieren
COPY . .

# Healthcheck konfigurieren
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["bash", "healthcheck.sh"]

# Umgebungsvariablen
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

# Port freigeben
EXPOSE 8000

# Anwendung starten
CMD ["python", "lib/main.py"]