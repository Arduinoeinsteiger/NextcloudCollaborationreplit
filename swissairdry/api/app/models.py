"""
SwissAirDry API - Datenbankmodelle

@author Swiss Air Dry Team <info@swissairdry.com>
@copyright 2023-2025 Swiss Air Dry Team
"""

import datetime
from typing import List, Optional, Dict, Any

import sqlalchemy
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from swissairdry.api.app.database import Base


class Device(Base):
    """
    Modell für Trocknungsgeräte.
    """
    __tablename__ = "devices"

    id = Column(String, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    type = Column(String, index=True)
    location = Column(String, nullable=True)
    status = Column(String, index=True, default="offline")
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True)
    api_key = Column(String, nullable=True)
    mqtt_topic = Column(String, nullable=True)
    firmware_version = Column(String, nullable=True)
    last_seen = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    configuration = Column(JSON, default={})
    config = Column(JSON, default={})
    meta_data = Column(JSON, default={})  # Umbenannt von metadata zu meta_data, da metadata ein reservierter Name ist

    # Beziehungen
    sensor_data = relationship("SensorData", back_populates="device", cascade="all, delete-orphan")
    customer = relationship("Customer", back_populates="devices")
    job = relationship("Job", back_populates="devices")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert das Modell in ein Dictionary.
        """
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "status": self.status,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "config": self.config,
            "meta_data": self.meta_data
        }


class SensorData(Base):
    """
    Modell für Sensordaten von Trocknungsgeräten.
    """
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, ForeignKey("devices.id", ondelete="CASCADE"), index=True)
    timestamp = Column(DateTime, default=func.now(), index=True)
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    power = Column(Float, nullable=True)
    energy = Column(Float, nullable=True)
    relay_state = Column(Boolean, nullable=True)
    runtime = Column(Integer, nullable=True)  # Laufzeit in Sekunden
    meta_data = Column(JSON, default={})  # Umbenannt von metadata zu meta_data, da metadata ein reservierter Name ist
    extra_data = Column(JSON, default={})  # Zusätzliche Sensordaten
    
    # Beziehungen
    device = relationship("Device", back_populates="sensor_data")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert das Modell in ein Dictionary.
        """
        return {
            "id": self.id,
            "device_id": self.device_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "power": self.power,
            "energy": self.energy,
            "relay_state": self.relay_state,
            "runtime": self.runtime,
            "meta_data": self.meta_data,
            "extra_data": self.extra_data
        }


class Customer(Base):
    """
    Modell für Kunden.
    """
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    city = Column(String, nullable=True)
    country = Column(String, nullable=True, default="Switzerland")
    notes = Column(String, nullable=True)
    external_id = Column(String, nullable=True, index=True)  # z.B. für Bexio-Integration
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Beziehungen
    devices = relationship("Device", back_populates="customer")
    jobs = relationship("Job", back_populates="customer")

    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert das Modell in ein Dictionary.
        """
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "postal_code": self.postal_code,
            "city": self.city,
            "country": self.country,
            "notes": self.notes,
            "external_id": self.external_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Job(Base):
    """
    Modell für Aufträge.
    """
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    location = Column(String, nullable=True)
    status = Column(String, index=True, default="new")
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    notes = Column(String, nullable=True)
    photos = Column(JSON, default=[])
    external_id = Column(String, nullable=True, index=True)  # z.B. für Bexio-Integration
    invoice_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Beziehungen
    customer = relationship("Customer", back_populates="jobs")
    devices = relationship("Device", back_populates="job")
    reports = relationship("Report", back_populates="job")

    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert das Modell in ein Dictionary.
        """
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "status": self.status,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "notes": self.notes,
            "photos": self.photos,
            "external_id": self.external_id,
            "invoice_id": self.invoice_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Report(Base):
    """
    Modell für Berichte.
    """
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    title = Column(String, index=True)
    content = Column(String)
    report_type = Column(String, default="standard")  # standard, final, damage, etc.
    author = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Beziehungen
    job = relationship("Job", back_populates="reports")

    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert das Modell in ein Dictionary.
        """
        return {
            "id": self.id,
            "job_id": self.job_id,
            "title": self.title,
            "content": self.content,
            "report_type": self.report_type,
            "author": self.author,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class EnergyCost(Base):
    """
    Modell für Energiekosten.
    """
    __tablename__ = "energy_costs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    rate_kwh = Column(Float)  # in CHF pro kWh
    valid_from = Column(DateTime, default=func.now())
    valid_to = Column(DateTime, nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert das Modell in ein Dictionary.
        """
        return {
            "id": self.id,
            "name": self.name,
            "rate_kwh": self.rate_kwh,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_to": self.valid_to.isoformat() if self.valid_to else None,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }