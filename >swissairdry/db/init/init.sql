-- SwissAirDry Datenbank-Initialisierungsskript
-- Dieses Skript wird beim ersten Start des Datenbank-Containers ausgeführt

-- Schemen erstellen
CREATE SCHEMA IF NOT EXISTS swissairdry;

-- Erweiterungen
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Berechtigungen
GRANT ALL PRIVILEGES ON SCHEMA swissairdry TO swissairdry;

-- Tabellen erstellen
SET search_path TO swissairdry;

-- Benutzer
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API-Schlüssel
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_value VARCHAR(64) UNIQUE NOT NULL,
    description VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE
);

-- Kunden
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    address VARCHAR(255),
    city VARCHAR(50),
    postal_code VARCHAR(20),
    country VARCHAR(50) DEFAULT 'Schweiz',
    contact_person VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(50),
    notes TEXT,
    bexio_id VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Gerätetypen
CREATE TABLE IF NOT EXISTS device_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL,
    description TEXT,
    manufacturer VARCHAR(50),
    model VARCHAR(50),
    power_consumption NUMERIC(8, 2), -- in Watt
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Geräte
CREATE TABLE IF NOT EXISTS devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    serial_number VARCHAR(50) UNIQUE NOT NULL,
    device_type_id UUID NOT NULL REFERENCES device_types(id),
    firmware_version VARCHAR(20),
    last_maintenance_date TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'available',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Aufträge
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(100) NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(id),
    address VARCHAR(255),
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    expected_end_date TIMESTAMP WITH TIME ZONE,
    actual_end_date TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL DEFAULT 'planned',
    description TEXT,
    assigned_to UUID REFERENCES users(id),
    bexio_job_id VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Gerätezuweisungen
CREATE TABLE IF NOT EXISTS device_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id UUID NOT NULL REFERENCES devices(id),
    job_id UUID NOT NULL REFERENCES jobs(id),
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(device_id, job_id)
);

-- Sensor-Messwerte
CREATE TABLE IF NOT EXISTS sensor_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id UUID NOT NULL REFERENCES devices(id),
    temperature NUMERIC(5, 2),
    humidity NUMERIC(5, 2),
    air_pressure NUMERIC(7, 2),
    air_quality NUMERIC(5, 2),
    power_consumption NUMERIC(8, 2),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Warnungen
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id UUID NOT NULL REFERENCES devices(id),
    job_id UUID NOT NULL REFERENCES jobs(id),
    type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID REFERENCES users(id)
);

-- Bilder/Dokumente
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(id),
    name VARCHAR(100) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    description TEXT,
    uploaded_by UUID REFERENCES users(id),
    uploaded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Energieverbrauchsprotokoll
CREATE TABLE IF NOT EXISTS energy_consumption (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id UUID NOT NULL REFERENCES devices(id),
    job_id UUID NOT NULL REFERENCES jobs(id),
    date DATE NOT NULL,
    consumption_kwh NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ESP Gerätekonfigurationen
CREATE TABLE IF NOT EXISTS esp_configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id UUID NOT NULL REFERENCES devices(id),
    mqtt_topic VARCHAR(100) NOT NULL,
    report_interval INTEGER NOT NULL DEFAULT 300, -- in Sekunden
    sensor_pins JSONB,
    display_enabled BOOLEAN DEFAULT false,
    ota_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- OTA-Update-Historie
CREATE TABLE IF NOT EXISTS ota_updates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id UUID NOT NULL REFERENCES devices(id),
    firmware_version VARCHAR(20) NOT NULL,
    update_status VARCHAR(20) NOT NULL,
    initiated_by UUID REFERENCES users(id),
    update_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Standard-Benutzer erstellen (Admin)
-- Passwort: admin (später zu ändern)
INSERT INTO users (username, email, password_hash, first_name, last_name, role)
VALUES ('admin', 'admin@vgnc.org', crypt('admin', gen_salt('bf')), 'Admin', 'User', 'admin')
ON CONFLICT (username) DO NOTHING;

-- Indizes erstellen
CREATE INDEX IF NOT EXISTS idx_devices_serial_number ON devices(serial_number);
CREATE INDEX IF NOT EXISTS idx_sensor_data_device_id ON sensor_data(device_id);
CREATE INDEX IF NOT EXISTS idx_sensor_data_timestamp ON sensor_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_device_assignments_job_id ON device_assignments(job_id);
CREATE INDEX IF NOT EXISTS idx_jobs_customer_id ON jobs(customer_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);