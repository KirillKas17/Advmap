"""Модели порталов и тотемов."""
from datetime import datetime, timezone
from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class PortalType(str, enum.Enum):
    """Тип портала."""
    TOTEM = "totem"
    PORTAL = "portal"
    BEACON = "beacon"


class PortalStatus(str, enum.Enum):
    """Статус портала."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DESTROYED = "destroyed"


class Portal(Base):
    """Модель портала/тотема на карте."""

    __tablename__ = "portals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    portal_type = Column(SQLEnum(PortalType), nullable=False, index=True)
    status = Column(SQLEnum(PortalStatus), default=PortalStatus.ACTIVE, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    point = Column(Geometry("POINT", srid=4326), nullable=False, index=True)
    installed_artifact_id = Column(Integer, ForeignKey("artifacts.id"), nullable=True)
    installed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    installed_at = Column(DateTime, nullable=True)
    interaction_count = Column(Integer, default=0, nullable=False)
    last_interaction_at = Column(DateTime, nullable=True)
    is_public = Column(Boolean, default=True, nullable=False)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    artifact = relationship("Artifact", foreign_keys=[installed_artifact_id])
    installer = relationship("User", foreign_keys=[installed_by_user_id])
    interactions = relationship("PortalInteraction", back_populates="portal", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Portal(id={self.id}, name={self.name}, portal_type={self.portal_type})>"


class PortalInteraction(Base):
    """Модель взаимодействия с порталом."""

    __tablename__ = "portal_interactions"

    id = Column(Integer, primary_key=True, index=True)
    portal_id = Column(Integer, ForeignKey("portals.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    interaction_type = Column(String(50), nullable=False)  # visit, activate, leave_artifact, take_artifact
    artifact_left_id = Column(Integer, ForeignKey("artifacts.id"), nullable=True)
    artifact_taken_id = Column(Integer, ForeignKey("artifacts.id"), nullable=True)
    reward_received = Column(JSON, nullable=True)  # Полученные награды
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    portal = relationship("Portal", back_populates="interactions")
    user = relationship("User", foreign_keys=[user_id])
    artifact_left = relationship("Artifact", foreign_keys=[artifact_left_id])
    artifact_taken = relationship("Artifact", foreign_keys=[artifact_taken_id])

    def __repr__(self) -> str:
        return f"<PortalInteraction(id={self.id}, portal_id={self.portal_id}, user_id={self.user_id})>"
