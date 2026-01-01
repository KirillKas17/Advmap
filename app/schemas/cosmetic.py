"""Схемы косметики."""
from datetime import datetime
from typing import Optional, Dict

from pydantic import BaseModel


class CosmeticCreate(BaseModel):
    """Схема создания косметики."""
    name: str
    cosmetic_type: str
    rarity: str
    slot: Optional[str] = None
    description: Optional[str] = None
    icon_url: Optional[str] = None
    preview_url: Optional[str] = None
    customization_data: Optional[Dict] = None
    is_tradeable: bool = True
    is_craftable: bool = False
    base_value: int = 0


class CosmeticResponse(BaseModel):
    """Схема ответа с косметикой."""
    id: int
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    preview_url: Optional[str] = None
    cosmetic_type: str
    rarity: str
    slot: Optional[str] = None
    customization_data: Optional[Dict] = None
    is_tradeable: bool
    is_craftable: bool
    base_value: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserCosmeticResponse(BaseModel):
    """Схема ответа с косметикой пользователя."""
    id: int
    user_id: int
    cosmetic_id: int
    is_equipped: bool
    obtained_at: datetime
    obtained_from: Optional[str] = None
    obtained_from_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    cosmetic: Optional[CosmeticResponse] = None

    class Config:
        from_attributes = True


class AvatarConfigResponse(BaseModel):
    """Схема конфигурации аватара."""
    avatar_config: Dict
