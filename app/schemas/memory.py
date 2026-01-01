"""Схемы метавселенной воспоминаний."""
from datetime import datetime
from typing import Optional, List, Dict

from pydantic import BaseModel


class MemoryCreate(BaseModel):
    """Схема создания воспоминания."""
    title: str
    memory_type: str
    description: Optional[str] = None
    location_data: Optional[Dict] = None
    media_urls: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    emotion_score: Optional[float] = None
    related_geozone_id: Optional[int] = None
    related_achievement_id: Optional[int] = None
    related_event_id: Optional[int] = None
    is_public: bool = False
    is_favorite: bool = False


class MemoryResponse(BaseModel):
    """Схема ответа с воспоминанием."""
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    memory_type: str
    location_data: Optional[Dict] = None
    media_urls: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    emotion_score: Optional[float] = None
    is_public: bool
    is_favorite: bool
    related_geozone_id: Optional[int] = None
    related_achievement_id: Optional[int] = None
    related_event_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MemoryTimelineResponse(BaseModel):
    """Схема ответа с временной линией."""
    timeline: List[Dict]
