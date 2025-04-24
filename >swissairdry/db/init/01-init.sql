-- SwissAirDry Datenbank-Initialisierungsskript

-- Erweiterungen
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "hstore";

-- Schema erstellen
CREATE SCHEMA IF NOT EXISTS swissairdry;

-- Benutzer-Tabelle
CREATE TABLE IF NOT EXISTS swissairdry.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Kunden-Tabelle
CREATE TABLE IF NOT EXISTS swissairdry.customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    city VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100) DEFAULT 'Schweiz',
    contact_person VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    notes TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Projekte-Tabelle
CREATE TABLE IF NOT EXISTS swissairdry.projects (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES swissairdry.customers(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) NOT NULL DEFAULT 'new',
    address TEXT,
    city VARCHAR(100),
    postal_code VARCHAR(20),
    created_by INTEGER REFERENCES swissairdry.users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Geräte-Tabelle
CREATE TABLE IF NOT EXISTS swissairdry.devices (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    model VARCHAR(100),
    firmware_version VARCHAR(50),
    hardware_version VARCHAR(50),
    mac_address VARCHAR(17),
    ip_address VARCHAR(45),
    mqtt_topic VARCHAR(255),
    last_online TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'offline',
    config JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Gerätezuordnungen zu Projekten
CREATE TABLE IF NOT EXISTS swissairdry.project_devices (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES swissairdry.projects(id) ON DELETE CASCADE,
    device_id INTEGER NOT NULL REFERENCES swissairdry.devices(id) ON DELETE CASCADE,
    installed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    removed_at TIMESTAMP WITH TIME ZONE,
    position VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (project_id, device_id, installed_at)
);

-- Sensordaten-Tabelle
CREATE TABLE IF NOT EXISTS swissairdry.sensor_data (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES swissairdry.devices(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sensor_type VARCHAR(50) NOT NULL,
    value FLOAT NOT NULL,
    unit VARCHAR(20),
    quality INTEGER DEFAULT 100,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Aufgaben/Tasks-Tabelle
CREATE TABLE IF NOT EXISTS swissairdry.tasks (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES swissairdry.projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    priority INTEGER DEFAULT 3,
    assigned_to INTEGER REFERENCES swissairdry.users(id),
    due_date TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Ereignisprotokoll/Event-Tabelle
CREATE TABLE IF NOT EXISTS swissairdry.events (
    id SERIAL PRIMARY KEY,
    device_id INTEGER REFERENCES swissairdry.devices(id) ON DELETE SET NULL,
    project_id INTEGER REFERENCES swissairdry.projects(id) ON DELETE SET NULL,
    event_type VARCHAR(50) NOT NULL,
    description TEXT,
    severity VARCHAR(20) DEFAULT 'info',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Dokumente-Tabelle (für Projekte)
CREATE TABLE IF NOT EXISTS swissairdry.documents (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES swissairdry.projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_type VARCHAR(100),
    file_size INTEGER,
    description TEXT,
    uploaded_by INTEGER REFERENCES swissairdry.users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Einstellungen-Tabelle
CREATE TABLE IF NOT EXISTS swissairdry.settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) NOT NULL UNIQUE,
    value TEXT,
    description TEXT,
    category VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Standort-Daten (für Gebäude/Etagen)
CREATE TABLE IF NOT EXISTS swissairdry.locations (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES swissairdry.projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    floor VARCHAR(50),
    room VARCHAR(100),
    description TEXT,
    coordinates JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Admin-Benutzer erstellen (Passwort: admin)
INSERT INTO swissairdry.users (username, email, password_hash, first_name, last_name, is_active, is_admin, role)
VALUES ('admin', 'admin@swissairdry.com', crypt('admin', gen_salt('bf')), 'System', 'Administrator', TRUE, TRUE, 'admin')
ON CONFLICT (username) DO NOTHING;

-- Standard-Einstellungen
INSERT INTO swissairdry.settings (key, value, description, category)
VALUES 
    ('mqtt.prefix', 'swissairdry/', 'MQTT Topic-Präfix für alle Geräte', 'system'),
    ('device.backup_interval', '86400', 'Backup-Intervall für Gerätekonfigurationen in Sekunden', 'system'),
    ('system.timezone', 'Europe/Zurich', 'Systemzeitzone', 'system'),
    ('notification.email_enabled', 'true', 'E-Mail-Benachrichtigungen aktivieren', 'notifications'),
    ('notification.push_enabled', 'true', 'Push-Benachrichtigungen aktivieren', 'notifications')
ON CONFLICT (key) DO NOTHING;

-- Erstellen von Indizes für bessere Performance
CREATE INDEX IF NOT EXISTS idx_sensor_data_device_id ON swissairdry.sensor_data(device_id);
CREATE INDEX IF NOT EXISTS idx_sensor_data_timestamp ON swissairdry.sensor_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_projects_customer_id ON swissairdry.projects(customer_id);
CREATE INDEX IF NOT EXISTS idx_project_devices_project_id ON swissairdry.project_devices(project_id);
CREATE INDEX IF NOT EXISTS idx_project_devices_device_id ON swissairdry.project_devices(device_id);
CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON swissairdry.tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON swissairdry.tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_events_device_id ON swissairdry.events(device_id);
CREATE INDEX IF NOT EXISTS idx_events_project_id ON swissairdry.events(project_id);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON swissairdry.events(created_at);

-- Berechtigungen einrichten
GRANT USAGE ON SCHEMA swissairdry TO swissairdry;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA swissairdry TO swissairdry;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA swissairdry TO swissairdry;
GRANT ALL PRIVILEGES ON SCHEMA swissairdry TO swissairdry;