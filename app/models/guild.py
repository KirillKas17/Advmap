"""Модели гильдий и клубов."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class GuildRole(str, enum.Enum):
    """Роль участника гильдии."""
    MEMBER = "member"
    OFFICER = "officer"
    LEADER = "leader"


class GuildStatus(str, enum.Enum):
    """Статус гильдии."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISBANDED = "disbanded"


class Guild(Base):
    """Модель гильдии."""

    __tablename__ = "guilds"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    tag = Column(String(10), nullable=True, unique=True)  # Короткий тег гильдии
    banner_url = Column(String(500), nullable=True)
    status = Column(SQLEnum(GuildStatus), default=GuildStatus.ACTIVE, nullable=False, index=True)
    max_members = Column(Integer, default=50, nullable=False)
    level = Column(Integer, default=1, nullable=False)
    experience = Column(Integer, default=0, nullable=False)
    total_achievements = Column(Integer, default=0, nullable=False)
    total_distance = Column(Float, default=0.0, nullable=False)  # Общее пройденное расстояние участниками
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    members = relationship("GuildMember", back_populates="guild", cascade="all, delete-orphan")
    achievements = relationship("GuildAchievement", back_populates="guild", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Guild(id={self.id}, name={self.name}, level={self.level})>"


class GuildMember(Base):
    """Модель участника гильдии."""

    __tablename__ = "guild_members"

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(Integer, ForeignKey("guilds.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(SQLEnum(GuildRole), default=GuildRole.MEMBER, nullable=False, index=True)
    contribution_score = Column(Integer, default=0, nullable=False)  # Вклад в гильдию
    joined_at = Column(DateTime, nullable=False, index=True)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    guild = relationship("Guild", back_populates="members")
    user = relationship("User", back_populates="guild_memberships")

    def __repr__(self) -> str:
        return f"<GuildMember(id={self.id}, guild_id={self.guild_id}, user_id={self.user_id}, role={self.role})>"


class GuildAchievement(Base):
    """Модель достижения гильдии."""

    __tablename__ = "guild_achievements"

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(Integer, ForeignKey("guilds.id"), nullable=False, index=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False, index=True)
    unlocked_at = Column(DateTime, nullable=False, index=True)
    unlocked_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    guild = relationship("Guild", back_populates="achievements")
    achievement = relationship("Achievement")
    unlocked_by = relationship("User", foreign_keys=[unlocked_by_user_id])

    def __repr__(self) -> str:
        return f"<GuildAchievement(id={self.id}, guild_id={self.guild_id}, achievement_id={self.achievement_id})>"
