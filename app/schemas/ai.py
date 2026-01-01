"""Схемы AI-помощника."""
from datetime import datetime
from typing import Optional, Dict, List

from pydantic import BaseModel


class RouteCreate(BaseModel):
    """Схема создания маршрута."""
    prompt: str
    start_location: Optional[Dict] = None


class RouteResponse(BaseModel):
    """Схема ответа с маршрутом."""
    id: int
    user_id: int
    name: str
    description: Optional[str] = None
    route_type: str
    status: str
    waypoints: List[Dict]
    estimated_duration_hours: Optional[float] = None
    estimated_distance_km: Optional[float] = None
    ai_prompt: Optional[str] = None
    ai_response: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    """Схема ответа с рекомендацией."""
    geozone_id: int
    name: str
    description: Optional[str] = None
    distance_km: float
    type: str


class ConversationCreate(BaseModel):
    """Схема создания разговора."""
    conversation_type: str
    message: str
    context_data: Optional[Dict] = None


class MessageAdd(BaseModel):
    """Схема добавления сообщения."""
    message: str


class ConversationResponse(BaseModel):
    """Схема ответа с разговором."""
    id: int
    user_id: int
    conversation_type: str
    messages: List[Dict]
    context_data: Optional[Dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
