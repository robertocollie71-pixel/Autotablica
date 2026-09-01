from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db import Base


def now():
    return datetime.now(timezone.utc)


class Owner(Base):
    __tablename__ = "owners"

    id = Column(Integer, primary_key=True)
    first_name = Column(String(80), nullable=False)
    last_name = Column(String(80), nullable=False)
    phone = Column(String(32), unique=True, index=True, nullable=False)
    email = Column(String(120), nullable=True)
    consent_contact = Column(Boolean, default=False, nullable=False)
    facebook = Column(String(200), nullable=True)
    instagram = Column(String(200), nullable=True)
    x_handle = Column(String(200), nullable=True)
    linkedin = Column(String(200), nullable=True)
    tiktok = Column(String(200), nullable=True)
    city = Column(String(80), nullable=True)
    voivodeship = Column(String(40), nullable=True)
    created_at = Column(DateTime(timezone=True), default=now)

    vehicles = relationship("Vehicle", back_populates="owner")


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True)
    plate = Column(String(16), unique=True, index=True, nullable=False)
    vin = Column(String(32), nullable=True, index=True)
    owner_id = Column(Integer, ForeignKey("owners.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now)

    owner = relationship("Owner", back_populates="vehicles")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True)
    actor = Column(String(80), nullable=False)
    action = Column(String(80), nullable=False)
    plate = Column(String(16), nullable=True)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=now)
