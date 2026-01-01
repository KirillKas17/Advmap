"""Модели метавселенной воспоминаний."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Float, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class Memory(Base):
    """Модель воспоминания (память о путешествии)."""

    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    memory_type = Column(String(50), nullable=False, index=True)  # visit, journey, achievement, event
    location_data = Column(JSON, nullable=True)  # Данные о местоположении
    media_urls = Column(JSON, nullable=True)  # Ссылки на фото/видео
    tags = Column(JSON, nullable=True)  # Теги для категоризации
    emotion_score = Column(Float, nullable=True)  # Оценка эмоций (0.0-1.0)
    is_public = Column(Boolean, default=False, nullable=False)
    is_favorite = Column(Boolean, default=False, nullable=False)
    related_geozone_id = Column(Integer, ForeignKey("geozones.id"), nullable=True)
    related_achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=True)
    related_event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="memories")
    geozone = relationship("Geozone", foreign_keys=[related_geozone_id])
    achievement = relationship("Achievement", foreign_keys=[related_achievement_id])
    event = relationship("Event", foreign_keys=[related_event_id])
    timeline_entries = relationship("MemoryTimeline", back_populates="memory", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Memory(id={self.id}, user_id={self.user_id}, title={self.title})>"


class MemoryTimeline(Base):
    """Модель временной линии воспоминаний."""

    __tablename__ = "memory_timeline"

    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(Integer, ForeignKey("memories.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    position_x = Column(Float, nullable=True)  # Позиция в 3D пространстве
    position_y = Column(Float, nullable=True)
    position_z = Column(Float, nullable=True)
    rotation = Column(JSON, nullable=True)  # Вращение в 3D пространстве
    scale = Column(Float, default=1.0, nullable=False)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    memory = relationship("Memory", back_populates="timeline_entries")
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<MemoryTimeline(id={self.id}, memory_id={self.memory_id})>"
