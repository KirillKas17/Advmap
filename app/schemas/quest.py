"""Схемы событий и квестов."""
from datetime import datetime
from typing import Optional, Dict, List

from pydantic import BaseModel


class EventCreate(BaseModel):
    """Схема создания события."""
    name: str
    event_type: str
    start_date: datetime
    end_date: datetime
    description: Optional[str] = None
    banner_url: Optional[str] = None
    reward_data: Optional[Dict] = None


class EventResponse(BaseModel):
    """Схема ответа с событием."""
    id: int
    name: str
    description: Optional[str] = None
    banner_url: Optional[str] = None
    event_type: str
    status: str
    start_date: datetime
    end_date: datetime
    reward_data: Optional[Dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuestCreate(BaseModel):
    """Схема создания квеста."""
    name: str
    quest_type: str
    requirements: Dict
    event_id: Optional[int] = None
    description: Optional[str] = None
    rewards: Optional[Dict] = None
    is_repeatable: bool = False
    max_completions: Optional[int] = None
    expires_at: Optional[datetime] = None
    is_premium: bool = False
    price: Optional[int] = None


class QuestResponse(BaseModel):
    """Схема ответа с квестом."""
    id: int
    event_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    quest_type: str
    requirements: Dict
    rewards: Optional[Dict] = None
    is_repeatable: bool
    max_completions: Optional[int] = None
    expires_at: Optional[datetime] = None
    is_premium: bool
    price: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserQuestResponse(BaseModel):
    """Схема ответа с квестом пользователя."""
    id: int
    user_id: int
    quest_id: int
    status: str
    progress: Dict
    completion_count: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    quest: Optional[QuestResponse] = None

    class Config:
        from_attributes = True
