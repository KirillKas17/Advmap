"""Схемы геозон."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class GeozoneCreate(BaseModel):
    """Схема создания геозоны."""

    name: str
    description: Optional[str] = None
    polygon_coordinates: List[List[float]]  # [[lon, lat], [lon, lat], ...]
    geozone_type: str  # landmark, city, region, custom


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
