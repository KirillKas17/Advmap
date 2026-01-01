"""Схемы гильдий."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class GuildCreate(BaseModel):
    """Схема создания гильдии."""
    name: str
    description: Optional[str] = None
    tag: Optional[str] = None
    banner_url: Optional[str] = None
    max_members: int = 50


class JoinGuildRequest(BaseModel):
    """Схема запроса на присоединение к гильдии."""
    pass  # Все данные берутся из URL


class GuildResponse(BaseModel):
    """Схема ответа с гильдией."""
    id: int
    name: str
    description: Optional[str] = None
    tag: Optional[str] = None
    banner_url: Optional[str] = None
    status: str
    max_members: int
    level: int
    experience: int
    total_achievements: int
    total_distance: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GuildMemberResponse(BaseModel):
    """Схема ответа с участником гильдии."""
    id: int
    guild_id: int
    user_id: int
    role: str
    contribution_score: int
    joined_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
