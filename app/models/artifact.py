"""Модели артефактов."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Float
from sqlalchemy.orm import relationship

from app.core.database import Base


class Artifact(Base):
    """Модель артефакта (коллекционного предмета)."""

    __tablename__ = "artifacts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    icon_url = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)
    rarity = Column(String(50), nullable=False, index=True)  # common, uncommon, rare, epic, legendary
    artifact_type = Column(String(50), nullable=False, index=True)  # regional, event, special, crafted
    geozone_id = Column(Integer, ForeignKey("geozones.id"), nullable=True, index=True)
    region_name = Column(String(255), nullable=True, index=True)  # Для региональных артефактов
    drop_chance = Column(Float, default=1.0, nullable=False)  # Вероятность выпадения (0.0-1.0)
    is_active = Column(Boolean, default=True, nullable=False)
    is_tradeable = Column(Boolean, default=True, nullable=False)
    is_craftable = Column(Boolean, default=False, nullable=False)
    base_value = Column(Integer, default=0, nullable=False)  # Базовая стоимость в внутренней валюте
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    user_artifacts = relationship("UserArtifact", back_populates="artifact", cascade="all, delete-orphan")
    crafting_requirements = relationship("ArtifactCraftingRequirement", back_populates="artifact", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Artifact(id={self.id}, name={self.name}, rarity={self.rarity})>"


class UserArtifact(Base):
    """Модель артефакта пользователя (инвентарь)."""

    __tablename__ = "user_artifacts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    artifact_id = Column(Integer, ForeignKey("artifacts.id"), nullable=False, index=True)
    quantity = Column(Integer, default=1, nullable=False)
    obtained_at = Column(DateTime, nullable=False, index=True)
    obtained_from = Column(String(100), nullable=True)  # geozone_visit, event, trade, craft
    obtained_from_id = Column(Integer, nullable=True)  # ID источника получения
    is_favorite = Column(Boolean, default=False, nullable=False)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="artifacts")
    artifact = relationship("Artifact", back_populates="user_artifacts")

    def __repr__(self) -> str:
        return f"<UserArtifact(id={self.id}, user_id={self.user_id}, artifact_id={self.artifact_id}, quantity={self.quantity})>"


class ArtifactCraftingRequirement(Base):
    """Модель требований для крафта артефакта."""

    __tablename__ = "artifact_crafting_requirements"

    id = Column(Integer, primary_key=True, index=True)
    artifact_id = Column(Integer, ForeignKey("artifacts.id"), nullable=False, index=True)
    required_artifact_id = Column(Integer, ForeignKey("artifacts.id"), nullable=False, index=True)
    required_quantity = Column(Integer, default=1, nullable=False)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    artifact = relationship("Artifact", foreign_keys=[artifact_id], back_populates="crafting_requirements")
    required_artifact = relationship("Artifact", foreign_keys=[required_artifact_id])

    def __repr__(self) -> str:
        return f"<ArtifactCraftingRequirement(id={self.id}, artifact_id={self.artifact_id}, required_artifact_id={self.required_artifact_id})>"
