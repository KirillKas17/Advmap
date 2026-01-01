"""Схемы артефактов."""
from datetime import datetime
from typing import Optional, Dict

from pydantic import BaseModel


class ArtifactCreate(BaseModel):
    """Схема создания артефакта."""
    name: str
    description: Optional[str] = None
    rarity: str
    artifact_type: str
    geozone_id: Optional[int] = None
    region_name: Optional[str] = None
    drop_chance: float = 1.0
    is_tradeable: bool = True
    is_craftable: bool = False
    base_value: int = 0
    icon_url: Optional[str] = None
    image_url: Optional[str] = None


class ArtifactResponse(BaseModel):
    """Схема ответа с артефактом."""
    id: int
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    image_url: Optional[str] = None
    rarity: str
    artifact_type: str
    geozone_id: Optional[int] = None
    region_name: Optional[str] = None
    drop_chance: float
    is_tradeable: bool
    is_craftable: bool
    base_value: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserArtifactResponse(BaseModel):
    """Схема ответа с артефактом пользователя."""
    id: int
    user_id: int
    artifact_id: int
    quantity: int
    obtained_at: datetime
    obtained_from: Optional[str] = None
    obtained_from_id: Optional[int] = None
    is_favorite: bool
    created_at: datetime
    updated_at: datetime
    artifact: Optional[ArtifactResponse] = None

    class Config:
        from_attributes = True


class ArtifactStatisticsResponse(BaseModel):
    """Схема статистики по артефактам."""
    total_artifacts: int
    total_quantity: int
    by_rarity: Dict[str, int]
