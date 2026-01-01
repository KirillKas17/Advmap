"""Модели платформы для создателей."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class CreatorStatus(str, enum.Enum):
    """Статус создателя."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class QuestModerationStatus(str, enum.Enum):
    """Статус модерации квеста."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class Creator(Base):
    """Модель создателя контента."""

    __tablename__ = "creators"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    status = Column(SQLEnum(CreatorStatus), default=CreatorStatus.PENDING, nullable=False, index=True)
    display_name = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    banner_url = Column(String(500), nullable=True)
    total_quests_created = Column(Integer, default=0, nullable=False)
    total_quests_sold = Column(Integer, default=0, nullable=False)
    total_revenue = Column(Integer, default=0, nullable=False)  # В внутренней валюте
    rating = Column(Float, default=0.0, nullable=False)
    total_ratings = Column(Integer, default=0, nullable=False)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="creator_profile")
    quests = relationship("Quest", foreign_keys="[Quest.creator_id]", back_populates="creator_rel", viewonly=True)
    payments = relationship("CreatorPayment", back_populates="creator", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Creator(id={self.id}, user_id={self.user_id}, status={self.status})>"


class CreatorPayment(Base):
    """Модель платежа создателю."""

    __tablename__ = "creator_payments"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("creators.id"), nullable=False, index=True)
    quest_id = Column(Integer, ForeignKey("quests.id"), nullable=False, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)  # Сумма платежа
    platform_fee = Column(Integer, nullable=False)  # Комиссия платформы
    creator_earnings = Column(Integer, nullable=False)  # Доход создателя
    status = Column(String(50), nullable=False, index=True)  # pending, completed, failed
    paid_at = Column(DateTime, nullable=True)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    creator = relationship("Creator", back_populates="payments")
    quest = relationship("Quest", foreign_keys=[quest_id])
    buyer = relationship("User", foreign_keys=[buyer_id])

    def __repr__(self) -> str:
        return f"<CreatorPayment(id={self.id}, creator_id={self.creator_id}, amount={self.amount})>"


class QuestModeration(Base):
    """Модель модерации квеста."""

    __tablename__ = "quest_moderations"

    id = Column(Integer, primary_key=True, index=True)
    quest_id = Column(Integer, ForeignKey("quests.id"), nullable=False, unique=True, index=True)
    status = Column(SQLEnum(QuestModerationStatus), default=QuestModerationStatus.PENDING, nullable=False, index=True)
    moderation_notes = Column(Text, nullable=True)
    moderated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    moderated_at = Column(DateTime, nullable=True)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    quest = relationship("Quest", foreign_keys=[quest_id], back_populates="moderation")
    moderator = relationship("User", foreign_keys=[moderated_by])

    def __repr__(self) -> str:
        return f"<QuestModeration(id={self.id}, quest_id={self.quest_id}, status={self.status})>"
