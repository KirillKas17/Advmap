"""Схемы достижений."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AchievementResponse(BaseModel):
    """Схема ответа с достижением."""

    id: int
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    achievement_type: str
    requirement_value: Optional[int] = None
    geozone_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserAchievementResponse(BaseModel):
    """Схема ответа с достижением пользователя."""

    id: int
    user_id: int
    achievement_id: int
    unlocked_at: datetime
    progress_value: int
    created_at: datetime
    updated_at: datetime
    achievement: Optional[AchievementResponse] = None

    class Config:
        from_attributes = True
