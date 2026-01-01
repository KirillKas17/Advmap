"""Модели геолокации."""
from datetime import datetime
from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class LocationSession(Base):
    """Модель сессии геолокации."""

    __tablename__ = "location_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_started_at = Column(DateTime, nullable=False, index=True)
    session_ended_at = Column(DateTime, nullable=True)
    is_background = Column(Boolean, default=False, nullable=False)
    is_offline = Column(Boolean, default=False, nullable=False)
    synced_at = Column(DateTime, nullable=True)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="location_sessions")
    points = relationship("LocationPoint", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<LocationSession(id={self.id}, user_id={self.user_id})>"


class LocationPoint(Base):
    """Модель точки геолокации."""

    __tablename__ = "location_points"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("location_sessions.id"), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    point = Column(Geometry("POINT", srid=4326), nullable=False, index=True)
    accuracy_meters = Column(Float, nullable=True)
    altitude_meters = Column(Float, nullable=True)
    speed_ms = Column(Float, nullable=True)
    heading_degrees = Column(Float, nullable=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    is_spoofed = Column(Boolean, default=False, nullable=False)
    spoofing_score = Column(Float, nullable=True)  # 0.0-1.0
    spoofing_reason = Column(String(255), nullable=True)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("LocationSession", back_populates="points")

    def __repr__(self) -> str:
        return f"<LocationPoint(id={self.id}, lat={self.latitude}, lon={self.longitude})>"
