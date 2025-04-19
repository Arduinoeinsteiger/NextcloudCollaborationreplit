# SwissAirDry Installation Guide for Warp

This document provides detailed instructions for installing and configuring the SwissAirDry system on your server using Warp. The system consists of multiple components that work together to provide a comprehensive solution for managing drying equipment.

## System Requirements

- Docker and Docker Compose (version 1.29.0 or higher)
- Minimum 4GB RAM
- 20GB free disk space
- Internet connection for container downloads
- Open ports for services:
  - 5000: API Server
  - 1883: MQTT Broker
  - 9001: MQTT WebSocket
  - 5432: PostgreSQL (optional, internal only)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/swissairdry/swissairdry.git
cd swissairdry
```

### 2. Configure Environment Variables

Create a `.env` file by copying the example file and adjusting the values:

```bash
cp .env.example .env
```

Edit the `.env` file with your preferred text editor and set appropriate values for your environment:

```bash
# Essential settings to modify:
POSTGRES_PASSWORD=your_secure_password
MQTT_PASSWORD=your_mqtt_password
AUTH_SECRET_KEY=your_very_long_secure_random_key
```

### 3. Create Folder Structure

Create the required directories for persistent data:

```bash
mkdir -p swissairdry/mqtt/auth
mkdir -p data/postgres
mkdir -p data/mqtt
```

### 4. Configure MQTT Authentication (Optional but Recommended)

If you want to secure your MQTT broker with authentication:

```bash
# Create password file
docker run --rm -it eclipse-mosquitto mosquitto_passwd -c /mosquitto/config/passwd swissairdry
# You will be prompted to enter a password

# Copy the generated passwd file
docker cp <container_id>:/mosquitto/config/passwd swissairdry/mqtt/auth/
```

Then edit `swissairdry/mqtt/mosquitto.conf` to enable authentication:

```
# Uncomment these lines:
password_file /mosquitto/config/auth/passwd
allow_anonymous false
```

### 5. Start the Services

Launch the SwissAirDry stack:

```bash
docker-compose up -d
```

### 6. Verify Installation

Check that all services are running:

```bash
docker-compose ps
```

Access the API server at http://your-server-ip:5000 to verify it's working.

## Component Configuration

### API Server

The API server provides the core functionality and serves as the central hub for all components. It's configured through environment variables in the `.env` file.

Key settings:
- `API_PORT`: The port on which the API server listens (default: 5000)
- `API_HOST`: The host address to bind to (default: 0.0.0.0)
- `DATABASE_URL`: Connection string for the PostgreSQL database

### MQTT Broker

The MQTT broker handles real-time communication with IoT devices. Configuration is stored in `swissairdry/mqtt/mosquitto.conf`.

Key settings:
- `MQTT_PORT`: The port for MQTT communication (default: 1883)
- `MQTT_WS_PORT`: WebSocket port for browser clients (default: 9001)

### Database

PostgreSQL stores all persistent data. The database is automatically initialized during first startup.

Key settings:
- `POSTGRES_USER`: Database username (default: swissairdry)
- `POSTGRES_PASSWORD`: Database password (IMPORTANT: change this!)
- `POSTGRES_DB`: Database name (default: swissairdry)

## Nextcloud Integration

To integrate with Nextcloud, you need to install the SwissAirDry app in your Nextcloud instance.

1. Copy the `swissairdry/nextcloud/app` directory to your Nextcloud apps directory
2. Enable the app in Nextcloud settings
3. Configure the connection to your SwissAirDry API server

## ESP32 Device Setup

To configure ESP32 devices to work with the SwissAirDry system:

1. Flash the appropriate firmware to your ESP32 device (ESP32C6 recommended)
2. Configure the WiFi settings in the firmware
3. Set the MQTT broker address to point to your server
4. Assign a unique device ID to each device

## Troubleshooting

### Connection Issues

If devices cannot connect to the MQTT broker:
- Check that the MQTT port (1883) is open in your firewall
- Verify that the MQTT broker is running (`docker-compose ps`)
- Check the MQTT logs for authentication errors

### Database Problems

If the API server cannot connect to the database:
- Ensure the PostgreSQL container is running
- Check the database credentials in `.env`
- Verify the database connection in the API server logs

### Web Interface Unavailable

If the web interface is not accessible:
- Check that the API server is running
- Verify the API port (5000) is open in your firewall
- Check the API server logs for startup errors

## Updating

To update the SwissAirDry system:

```bash
git pull
docker-compose down
docker-compose pull
docker-compose up -d
```