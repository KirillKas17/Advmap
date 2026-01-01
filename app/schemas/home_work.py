"""Схемы определения дома/работы."""
from datetime import datetime

from pydantic import BaseModel


class UserHomeWorkResponse(BaseModel):
    """Схема ответа с определенным домом/работой."""

    id: int
    user_id: int
    location_type: str  # home, work
    latitude: float
    longitude: float
    radius_meters: float
    confidence_score: float
    total_visits: int
    total_time_minutes: int
    first_detected_at: datetime
    last_updated_at: datetime
    is_confirmed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
