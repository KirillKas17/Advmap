"""Схемы порталов."""
from datetime import datetime
from typing import Optional, Dict

from pydantic import BaseModel


class PortalCreate(BaseModel):
    """Схема создания портала."""
    name: str
    portal_type: str
    latitude: float
    longitude: float
    description: Optional[str] = None
    installed_artifact_id: Optional[int] = None
    is_public: bool = True


class PortalResponse(BaseModel):
    """Схема ответа с порталом."""
    id: int
    name: str
    description: Optional[str] = None
    portal_type: str
    status: str
    latitude: float
    longitude: float
    installed_artifact_id: Optional[int] = None
    installed_by_user_id: Optional[int] = None
    installed_at: Optional[datetime] = None
    interaction_count: int
    last_interaction_at: Optional[datetime] = None
    is_public: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PortalInteractionCreate(BaseModel):
    """Схема создания взаимодействия с порталом."""
    interaction_type: str
    artifact_left_id: Optional[int] = None
    artifact_taken_id: Optional[int] = None


class PortalInteractionResponse(BaseModel):
    """Схема ответа с взаимодействием."""
    id: int
    portal_id: int
    user_id: int
    interaction_type: str
    artifact_left_id: Optional[int] = None
    artifact_taken_id: Optional[int] = None
    reward_received: Optional[Dict] = None
    created_at: datetime

    class Config:
        from_attributes = True
