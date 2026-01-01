"""Схемы геозон."""
from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, field_validator


class GeozoneCreate(BaseModel):
    """Схема создания геозоны."""

    name: str = Field(..., min_length=1, max_length=255, description="Название геозоны")
    description: Optional[str] = None
    polygon_coordinates: List[List[float]] = Field(..., min_length=3, description="Координаты полигона [[lon, lat], ...]")
    geozone_type: str = Field(..., description="Тип геозоны: landmark, city, region, custom")

    @field_validator('polygon_coordinates')
    @classmethod
    def validate_polygon_coordinates(cls, v: List[List[float]]) -> List[List[float]]:
        """Валидация координат полигона."""
        if len(v) < 3:
            raise ValueError('Полигон должен содержать минимум 3 точки')
        for coord in v:
            if len(coord) != 2:
                raise ValueError('Каждая точка должна содержать 2 координаты [longitude, latitude]')
            lon, lat = coord
            if not (-180 <= lon <= 180):
                raise ValueError(f'Долгота {lon} должна быть в диапазоне от -180 до 180')
            if not (-90 <= lat <= 90):
                raise ValueError(f'Широта {lat} должна быть в диапазоне от -90 до 90')
        return v


class GeozoneResponse(BaseModel):
    """Схема ответа с геозоной."""

    id: int
    name: str
    description: Optional[str] = None
    center_latitude: str
    center_longitude: str
    geozone_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GeozoneVisitResponse(BaseModel):
    """Схема ответа с посещением геозоны."""

    id: int
    user_id: int
    geozone_id: int
    visit_started_at: datetime
    visit_ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    is_verified: bool
    verification_score: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AreaDiscoveryResponse(BaseModel):
    """Схема ответа с открытием области."""

    id: int
    user_id: int
    geozone_id: int
    discovery_status: str
    progress_percent: float
    time_spent_seconds: int
    area_covered_meters: float
    first_discovered_at: datetime
    last_updated_at: datetime
    created_at: datetime
    updated_at: datetime
    geozone: Optional[GeozoneResponse] = None

    class Config:
        from_attributes = True


class AreaDiscoveryEventResponse(BaseModel):
    """Схема события открытия области."""

    type: str
    area_type: str
    name: str
    geozone_id: int
    progress: float
    status: str
    old_status: Optional[str] = None
    reward: Dict[str, Any]

    class Config:
        from_attributes = True
