"""Схемы платформы создателей."""
from datetime import datetime
from typing import Optional, Dict

from pydantic import BaseModel


class CreatorApplyRequest(BaseModel):
    """Схема заявки на статус создателя."""
    display_name: Optional[str] = None
    bio: Optional[str] = None


class CreatorResponse(BaseModel):
    """Схема ответа с создателем."""
    id: int
    user_id: int
    status: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None
    total_quests_created: int
    total_quests_sold: int
    total_revenue: int
    rating: float
    total_ratings: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PremiumQuestCreate(BaseModel):
    """Схема создания платного квеста."""
    name: str
    quest_type: str
    requirements: Dict
    price: int
    description: Optional[str] = None
    rewards: Optional[Dict] = None
