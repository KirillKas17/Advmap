"""Модель пользователя."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """Модель пользователя."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")
    geozone_visits = relationship("GeozoneVisit", back_populates="user", cascade="all, delete-orphan")
    area_discoveries = relationship("AreaDiscovery", back_populates="user", cascade="all, delete-orphan")
    location_sessions = relationship("LocationSession", back_populates="user", cascade="all, delete-orphan")
    home_work_locations = relationship("UserHomeWork", back_populates="user", cascade="all, delete-orphan")
    artifacts = relationship("UserArtifact", back_populates="user", cascade="all, delete-orphan")
    cosmetics = relationship("UserCosmetic", back_populates="user", cascade="all, delete-orphan")
    avatar_config = relationship("UserAvatar", back_populates="user", uselist=False, cascade="all, delete-orphan")
    currency = relationship("UserCurrency", back_populates="user", uselist=False, cascade="all, delete-orphan")
    quests = relationship("UserQuest", back_populates="user", cascade="all, delete-orphan")
    events = relationship("UserEvent", back_populates="user", cascade="all, delete-orphan")
    guild_memberships = relationship("GuildMember", back_populates="user", cascade="all, delete-orphan")
    creator_profile = relationship("Creator", back_populates="user", uselist=False, cascade="all, delete-orphan")
    routes = relationship("Route", back_populates="user", cascade="all, delete-orphan")
    ai_conversations = relationship("AIConversation", back_populates="user", cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
