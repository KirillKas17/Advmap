"""Модели верификации и статусов."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class VerificationStatus(str, enum.Enum):
    """Статус верификации."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVOKED = "revoked"


class UserStatus(str, enum.Enum):
    """Статус пользователя."""
    NEWBIE = "newbie"
    TRAVELER = "traveler"
    EXPLORER = "explorer"
    VERIFIED_TRAVELER = "verified_traveler"
    MASTER_EXPLORER = "master_explorer"
    LEGEND = "legend"


class VerificationRequest(Base):
    """Модель запроса на верификацию."""

    __tablename__ = "verification_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(SQLEnum(VerificationStatus), default=VerificationStatus.PENDING, nullable=False, index=True)
    requested_status = Column(SQLEnum(UserStatus), nullable=False)
    evidence_data = Column(Text, nullable=True)  # Доказательства для верификации
    rejection_reason = Column(Text, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    def __repr__(self) -> str:
        return f"<VerificationRequest(id={self.id}, user_id={self.user_id}, status={self.status})>"


class UserStatusHistory(Base):
    """Модель истории изменения статусов пользователя."""

    __tablename__ = "user_status_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    old_status = Column(SQLEnum(UserStatus), nullable=True)
    new_status = Column(SQLEnum(UserStatus), nullable=False)
    reason = Column(String(255), nullable=True)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Кто изменил (для админов)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    changer = relationship("User", foreign_keys=[changed_by])

    def __repr__(self) -> str:
        return f"<UserStatusHistory(id={self.id}, user_id={self.user_id}, new_status={self.new_status})>"
