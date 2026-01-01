"""Модель определения дома и работы пользователя."""
from datetime import datetime
from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserHomeWork(Base):
    """Модель определения дома/работы пользователя."""

    __tablename__ = "user_home_work"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    location_type = Column(String(20), nullable=False, index=True)  # home, work
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    point = Column(Geometry("POINT", srid=4326), nullable=False, index=True)
    radius_meters = Column(Float, default=200.0, nullable=False)
    confidence_score = Column(Float, nullable=False)  # 0.0-1.0
    total_visits = Column(Integer, default=0, nullable=False)
    total_time_minutes = Column(Integer, default=0, nullable=False)
    first_detected_at = Column(DateTime, nullable=False)
    last_updated_at = Column(DateTime, nullable=False)
    is_confirmed = Column(Boolean, default=False, nullable=False)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="home_work_locations")

    def __repr__(self) -> str:
        return f"<UserHomeWork(id={self.id}, user_id={self.user_id}, type={self.location_type})>"
