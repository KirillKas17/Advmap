"""Схемы геолокации."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class LocationPointCreate(BaseModel):
    """Схема создания точки геолокации."""

    latitude: float
    longitude: float
    accuracy_meters: Optional[float] = None
    altitude_meters: Optional[float] = None
    speed_ms: Optional[float] = None
    heading_degrees: Optional[float] = None
    timestamp: Optional[datetime] = None


class LocationPointResponse(BaseModel):
    """Схема ответа с точкой геолокации."""

    id: int
    session_id: int
    latitude: float
    longitude: float
    accuracy_meters: Optional[float] = None
    altitude_meters: Optional[float] = None
    speed_ms: Optional[float] = None
    heading_degrees: Optional[float] = None
    timestamp: datetime
    is_spoofed: bool
    spoofing_score: Optional[float] = None
    spoofing_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LocationSessionResponse(BaseModel):
    """Схема ответа с сессией геолокации."""

    id: int
    user_id: int
    session_started_at: datetime
    session_ended_at: Optional[datetime] = None
    is_background: bool
    is_offline: bool
    synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OfflineSyncRequest(BaseModel):
    """Схема запроса синхронизации офлайн данных."""

    points: list[LocationPointCreate]
    session_started_at: Optional[datetime] = None
    session_ended_at: Optional[datetime] = None


class BatchOfflineSyncRequest(BaseModel):
    """Схема пакетной синхронизации офлайн данных."""

    sessions: list[OfflineSyncRequest]
