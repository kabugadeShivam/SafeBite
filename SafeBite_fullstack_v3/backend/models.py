from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    location = Column(String(300), nullable=False)
    state = Column(String(100), nullable=False, index=True)
    region = Column(String(150), nullable=False, index=True)
    registration_id = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(String(30), default="ACTIVE", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    devices = relationship("Device", back_populates="restaurant", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="restaurant", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="restaurant")


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), unique=True, nullable=False, index=True)
    device_type = Column(String(100), nullable=False)
    status = Column(String(30), default="OFFLINE", nullable=False)
    last_seen_at = Column(DateTime)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)

    restaurant = relationship("Restaurant", back_populates="devices")
    sensor_readings = relationship("SensorReading", back_populates="device")
    alerts = relationship("Alert", back_populates="device")


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    door_open = Column(Boolean, default=False, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)

    device = relationship("Device", back_populates="sensor_readings")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    batch_number = Column(String(100))
    manufacturing_date = Column(String(50))
    expiry_date = Column(String(50))
    status = Column(String(40), default="SAFE", nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)

    restaurant = relationship("Restaurant", back_populates="products")


class AIDetection(Base):
    __tablename__ = "ai_detections"

    id = Column(Integer, primary_key=True, index=True)
    detection_type = Column(String(100), nullable=False)
    confidence = Column(Float)
    description = Column(Text)
    image_path = Column(String(500))
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(100), nullable=False)
    severity = Column(String(30), nullable=False)
    risk_score = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)
    source = Column(String(50), default="IOT", nullable=False)
    status = Column(String(40), default="OPEN", nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    sensor_reading_id = Column(Integer, ForeignKey("sensor_readings.id"), nullable=True)

    restaurant = relationship("Restaurant", back_populates="alerts")
    device = relationship("Device", back_populates="alerts")
    investigation = relationship("Investigation", back_populates="alert", uselist=False)


class GovernmentOfficer(Base):
    __tablename__ = "government_officers"

    id = Column(Integer, primary_key=True, index=True)
    officer_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="REGIONAL_OFFICER", nullable=False)
    state = Column(String(100), nullable=False)
    region = Column(String(150), nullable=False, index=True)
    status = Column(String(30), default="ACTIVE", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    investigations = relationship(
        "Investigation",
        back_populates="officer",
        foreign_keys="Investigation.officer_id",
    )


class Investigation(Base):
    __tablename__ = "investigations"
    __table_args__ = (UniqueConstraint("alert_id", name="uq_investigation_alert"),)

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    officer_id = Column(Integer, ForeignKey("government_officers.id"), nullable=False)
    findings = Column(Text, default="", nullable=False)
    action_taken = Column(Text, default="", nullable=False)
    corrective_action = Column(Text, default="", nullable=False)
    status = Column(String(50), default="IN_PROGRESS", nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    submitted_at = Column(DateTime)
    verified_at = Column(DateTime)
    verified_by = Column(Integer, ForeignKey("government_officers.id"))

    alert = relationship("Alert", back_populates="investigation")
    officer = relationship(
        "GovernmentOfficer",
        back_populates="investigations",
        foreign_keys=[officer_id],
    )
    evidence = relationship("Evidence", back_populates="investigation", cascade="all, delete-orphan")


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    investigation_id = Column(Integer, ForeignKey("investigations.id"), nullable=False)
    original_filename = Column(String(255), nullable=False)
    stored_path = Column(String(500), nullable=False)
    content_type = Column(String(100))
    sha256 = Column(String(64), nullable=False, index=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    uploaded_by = Column(Integer, ForeignKey("government_officers.id"), nullable=False)

    investigation = relationship("Investigation", back_populates="evidence")


class BlockchainRecord(Base):
    __tablename__ = "blockchain_records"

    id = Column(Integer, primary_key=True, index=True)
    record_type = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(Integer, nullable=False)
    actor_id = Column(Integer)
    payload_hash = Column(String(64), nullable=False)
    previous_hash = Column(String(64), nullable=False)
    record_hash = Column(String(64), unique=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    blockchain_tx_id = Column(String(200))
    verification_status = Column(String(50), default="LOCAL_HASH_CHAIN", nullable=False)
