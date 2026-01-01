"""Модели геозон."""
from datetime import datetime, timezone
from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Float, JSON
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
    geozone_type = Column(String(50), nullable=False, index=True)  # landmark, city, region, custom, forest, river, valley, park, farmland, mountain, lake, coastal, rural_settlement, infrastructure
    area_type = Column(String(50), nullable=True, index=True)  # Для Area POI: forest_area, river_basin, valley, national_park, farmland, mountain_range, lake_area, coastal_area, rural_settlement_area, infrastructure_area
    area_square_meters = Column(Float, nullable=True)  # Площадь области в квадратных метрах
    osm_id = Column(String(100), nullable=True, index=True)  # ID из OpenStreetMap
    osm_tags = Column(JSON, nullable=True)  # Теги из OSM
    is_active = Column(Boolean, default=True, nullable=False)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    visits = relationship("GeozoneVisit", back_populates="geozone", cascade="all, delete-orphan")
    area_discoveries = relationship("AreaDiscovery", back_populates="geozone", cascade="all, delete-orphan")

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
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="geozone_visits")
    geozone = relationship("Geozone", back_populates="visits")

    def __repr__(self) -> str:
        return f"<GeozoneVisit(id={self.id}, user_id={self.user_id}, geozone_id={self.geozone_id})>"


class AreaDiscovery(Base):
    """Модель открытия области (Area POI) пользователем."""

    __tablename__ = "area_discoveries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    geozone_id = Column(Integer, ForeignKey("geozones.id"), nullable=False, index=True)
    discovery_status = Column(String(20), nullable=False, index=True, default="discovered")  # discovered, explored, completed
    progress_percent = Column(Float, default=0.0, nullable=False)  # Процент открытой площади (0-100)
    time_spent_seconds = Column(Integer, default=0, nullable=False)  # Время, проведённое в зоне
    area_covered_meters = Column(Float, default=0.0, nullable=False)  # Покрытая площадь в м²
    first_discovered_at = Column(DateTime, nullable=False, index=True)
    last_updated_at = Column(DateTime, nullable=False, index=True)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="area_discoveries")
    geozone = relationship("Geozone", back_populates="area_discoveries")

    def __repr__(self) -> str:
        return f"<AreaDiscovery(id={self.id}, user_id={self.user_id}, geozone_id={self.geozone_id}, status={self.discovery_status})>"
