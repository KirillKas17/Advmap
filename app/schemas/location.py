"""Схемы геолокации."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class LocationPointCreate(BaseModel):
    """Схема создания точки геолокации."""

    latitude: float = Field(..., ge=-90, le=90, description="Широта от -90 до 90")
    longitude: float = Field(..., ge=-180, le=180, description="Долгота от -180 до 180")
    accuracy_meters: Optional[float] = Field(None, ge=0, description="Точность в метрах")
    altitude_meters: Optional[float] = None
    speed_ms: Optional[float] = Field(None, ge=0, description="Скорость в м/с")
    heading_degrees: Optional[float] = Field(None, ge=0, le=360, description="Направление в градусах (0-360)")
    timestamp: Optional[datetime] = None

    @field_validator('latitude', 'longitude')
    @classmethod
    def validate_coordinates(cls, v: float, info) -> float:
        """Валидация координат."""
        field_name = info.field_name
        if field_name == 'latitude' and not (-90 <= v <= 90):
            raise ValueError('Широта должна быть в диапазоне от -90 до 90')
        if field_name == 'longitude' and not (-180 <= v <= 180):
            raise ValueError('Долгота должна быть в диапазоне от -180 до 180')
        return v


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
