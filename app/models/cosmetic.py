"""Модели косметических предметов."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Float, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class Cosmetic(Base):
    """Модель косметического предмета."""

    __tablename__ = "cosmetics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    icon_url = Column(String(500), nullable=True)
    preview_url = Column(String(500), nullable=True)
    cosmetic_type = Column(String(50), nullable=False, index=True)  # avatar, hat, outfit, accessory, background
    rarity = Column(String(50), nullable=False, index=True)  # common, uncommon, rare, epic, legendary
    slot = Column(String(50), nullable=True)  # head, body, accessory, background
    customization_data = Column(JSON, nullable=True)  # Дополнительные данные для кастомизации
    is_active = Column(Boolean, default=True, nullable=False)
    is_tradeable = Column(Boolean, default=True, nullable=False)
    is_craftable = Column(Boolean, default=False, nullable=False)
    base_value = Column(Integer, default=0, nullable=False)  # Базовая стоимость
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    user_cosmetics = relationship("UserCosmetic", back_populates="cosmetic", cascade="all, delete-orphan")
    crafting_requirements = relationship("CosmeticCraftingRequirement", back_populates="cosmetic", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Cosmetic(id={self.id}, name={self.name}, type={self.cosmetic_type})>"


class UserCosmetic(Base):
    """Модель косметического предмета пользователя."""

    __tablename__ = "user_cosmetics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    cosmetic_id = Column(Integer, ForeignKey("cosmetics.id"), nullable=False, index=True)
    is_equipped = Column(Boolean, default=False, nullable=False)
    obtained_at = Column(DateTime, nullable=False, index=True)
    obtained_from = Column(String(100), nullable=True)  # achievement, purchase, trade, craft, event
    obtained_from_id = Column(Integer, nullable=True)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="cosmetics")
    cosmetic = relationship("Cosmetic", back_populates="user_cosmetics")

    def __repr__(self) -> str:
        return f"<UserCosmetic(id={self.id}, user_id={self.user_id}, cosmetic_id={self.cosmetic_id}, is_equipped={self.is_equipped})>"


class CosmeticCraftingRequirement(Base):
    """Модель требований для крафта косметики."""

    __tablename__ = "cosmetic_crafting_requirements"

    id = Column(Integer, primary_key=True, index=True)
    cosmetic_id = Column(Integer, ForeignKey("cosmetics.id"), nullable=False, index=True)
    required_artifact_id = Column(Integer, ForeignKey("artifacts.id"), nullable=True, index=True)
    required_cosmetic_id = Column(Integer, ForeignKey("cosmetics.id"), nullable=True, index=True)
    required_quantity = Column(Integer, default=1, nullable=False)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    cosmetic = relationship("Cosmetic", foreign_keys=[cosmetic_id], back_populates="crafting_requirements")
    required_artifact = relationship("Artifact", foreign_keys=[required_artifact_id])
    required_cosmetic = relationship("Cosmetic", foreign_keys=[required_cosmetic_id])

    def __repr__(self) -> str:
        return f"<CosmeticCraftingRequirement(id={self.id}, cosmetic_id={self.cosmetic_id})>"


class UserAvatar(Base):
    """Модель кастомизации аватара пользователя."""

    __tablename__ = "user_avatars"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    avatar_config = Column(JSON, nullable=False)  # Конфигурация аватара (equipped cosmetics)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="avatar_config")

    def __repr__(self) -> str:
        return f"<UserAvatar(id={self.id}, user_id={self.user_id})>"
