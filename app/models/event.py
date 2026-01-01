"""Модели событий и квестов."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Float, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class EventType(str, enum.Enum):
    """Тип события."""
    SEASONAL = "seasonal"
    LIMITED = "limited"
    WEEKLY = "weekly"
    DAILY = "daily"
    SPECIAL = "special"


class EventStatus(str, enum.Enum):
    """Статус события."""
    UPCOMING = "upcoming"
    ACTIVE = "active"
    ENDED = "ended"
    CANCELLED = "cancelled"


class QuestStatus(str, enum.Enum):
    """Статус квеста."""
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class QuestType(str, enum.Enum):
    """Тип квеста."""
    VISIT_LOCATIONS = "visit_locations"
    COLLECT_ARTIFACTS = "collect_artifacts"
    TRAVEL_DISTANCE = "travel_distance"
    COMPLETE_ACHIEVEMENTS = "complete_achievements"
    CUSTOM = "custom"


class Event(Base):
    """Модель события."""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    banner_url = Column(String(500), nullable=True)
    event_type = Column(SQLEnum(EventType), nullable=False, index=True)
    status = Column(SQLEnum(EventStatus), default=EventStatus.UPCOMING, nullable=False, index=True)
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False, index=True)
    reward_data = Column(JSON, nullable=True)  # Награды за участие
    is_active = Column(Boolean, default=True, nullable=False)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    quests = relationship("Quest", back_populates="event", cascade="all, delete-orphan")
    user_events = relationship("UserEvent", back_populates="event", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, name={self.name}, event_type={self.event_type})>"


class Quest(Base):
    """Модель квеста."""

    __tablename__ = "quests"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    quest_type = Column(SQLEnum(QuestType), nullable=False, index=True)
    requirements = Column(JSON, nullable=False)  # Условия выполнения квеста
    rewards = Column(JSON, nullable=True)  # Награды за выполнение
    is_repeatable = Column(Boolean, default=False, nullable=False)
    max_completions = Column(Integer, nullable=True)  # Максимальное количество выполнений
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_premium = Column(Boolean, default=False, nullable=False)  # Платный квест
    price = Column(Integer, nullable=True)  # Цена для платных квестов
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Для платформы создателей
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    event = relationship("Event", back_populates="quests")
    creator_rel = relationship("Creator", foreign_keys=[creator_id], viewonly=True)
    creator_user = relationship("User", foreign_keys=[creator_id])
    user_quests = relationship("UserQuest", back_populates="quest", cascade="all, delete-orphan")
    moderation = relationship("QuestModeration", back_populates="quest", uselist=False, cascade="all, delete-orphan")
    creator_payments = relationship("CreatorPayment", foreign_keys="[CreatorPayment.quest_id]", viewonly=True)

    def __repr__(self) -> str:
        return f"<Quest(id={self.id}, name={self.name}, quest_type={self.quest_type})>"


class UserQuest(Base):
    """Модель прогресса квеста пользователя."""

    __tablename__ = "user_quests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    quest_id = Column(Integer, ForeignKey("quests.id"), nullable=False, index=True)
    status = Column(SQLEnum(QuestStatus), default=QuestStatus.AVAILABLE, nullable=False, index=True)
    progress = Column(JSON, nullable=False)  # Текущий прогресс выполнения
    completion_count = Column(Integer, default=0, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="quests")
    quest = relationship("Quest", back_populates="user_quests")

    def __repr__(self) -> str:
        return f"<UserQuest(id={self.id}, user_id={self.user_id}, quest_id={self.quest_id}, status={self.status})>"


class UserEvent(Base):
    """Модель участия пользователя в событии."""

    __tablename__ = "user_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    participation_score = Column(Integer, default=0, nullable=False)
    rewards_claimed = Column(JSON, nullable=True)  # Полученные награды
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="events")
    event = relationship("Event", back_populates="user_events")

    def __repr__(self) -> str:
        return f"<UserEvent(id={self.id}, user_id={self.user_id}, event_id={self.event_id})>"
