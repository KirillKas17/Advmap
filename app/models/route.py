"""Модели маршрутов и AI-планирования."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Float, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class RouteStatus(str, enum.Enum):
    """Статус маршрута."""
    DRAFT = "draft"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RouteType(str, enum.Enum):
    """Тип маршрута."""
    AI_GENERATED = "ai_generated"
    MANUAL = "manual"
    TEMPLATE = "template"


class Route(Base):
    """Модель маршрута."""

    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    route_type = Column(SQLEnum(RouteType), nullable=False, index=True)
    status = Column(SQLEnum(RouteStatus), default=RouteStatus.DRAFT, nullable=False, index=True)
    waypoints = Column(JSON, nullable=False)  # Список точек маршрута
    estimated_duration_hours = Column(Float, nullable=True)
    estimated_distance_km = Column(Float, nullable=True)
    ai_prompt = Column(Text, nullable=True)  # Промпт для AI генерации
    ai_response = Column(Text, nullable=True)  # Ответ AI
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    is_public = Column(Boolean, default=False, nullable=False)
    is_template = Column(Boolean, default=False, nullable=False)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="routes")
    progress = relationship("RouteProgress", back_populates="route", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Route(id={self.id}, name={self.name}, route_type={self.route_type})>"


class RouteProgress(Base):
    """Модель прогресса прохождения маршрута."""

    __tablename__ = "route_progress"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    current_waypoint_index = Column(Integer, default=0, nullable=False)
    visited_waypoints = Column(JSON, nullable=False)  # Индексы посещенных точек
    completion_percentage = Column(Float, default=0.0, nullable=False)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    route = relationship("Route", back_populates="progress")
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<RouteProgress(id={self.id}, route_id={self.route_id}, completion_percentage={self.completion_percentage})>"


class AIConversation(Base):
    """Модель разговора с AI-помощником."""

    __tablename__ = "ai_conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    conversation_type = Column(String(50), nullable=False, index=True)  # route_planning, recommendation, general
    messages = Column(JSON, nullable=False)  # История сообщений
    context_data = Column(JSON, nullable=True)  # Контекст для AI
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="ai_conversations")

    def __repr__(self) -> str:
        return f"<AIConversation(id={self.id}, user_id={self.user_id}, conversation_type={self.conversation_type})>"
