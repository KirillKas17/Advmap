"""Модели геозон."""
from datetime import datetime
from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Geozone(Base):
    """Модель геозоны (полигон)."""

    __tablename__ = "geozones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    polygon = Column(Geometry("POLYGON", srid=4326), nullable=False, index=True)
    center_latitude = Column(String(50), nullable=False)
    center_longitude = Column(String(50), nullable=False)
    radius_meters = Column(Integer, nullable=True)
    geozone_type = Column(String(50), nullable=False, index=True)  # landmark, city, region, custom
    is_active = Column(Boolean, default=True, nullable=False)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    visits = relationship("GeozoneVisit", back_populates="geozone", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Geozone(id={self.id}, name={self.name}, type={self.geozone_type})>"


class GeozoneVisit(Base):
    """Модель посещения геозоны."""

    __tablename__ = "geozone_visits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    geozone_id = Column(Integer, ForeignKey("geozones.id"), nullable=False, index=True)
    visit_started_at = Column(DateTime, nullable=False, index=True)
    visit_ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_score = Column(Integer, nullable=True)  # 0-100
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="geozone_visits")
    geozone = relationship("Geozone", back_populates="visits")

    def __repr__(self) -> str:
        return f"<GeozoneVisit(id={self.id}, user_id={self.user_id}, geozone_id={self.geozone_id})>"
