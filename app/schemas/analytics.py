"""Схемы B2B аналитики."""
from datetime import datetime
from typing import Optional, Dict

from pydantic import BaseModel


class StatisticsResponse(BaseModel):
    """Схема ответа со статистикой."""
    period: Dict
    visits: Dict
    location: Dict
    users: Dict


class ExportCreate(BaseModel):
    """Схема создания экспорта."""
    export_type: str
    data_range_start: datetime
    data_range_end: datetime
    filters: Optional[Dict] = None


class ExportResponse(BaseModel):
    """Схема ответа с экспортом."""
    id: int
    client_id: int
    export_type: str
    data_range_start: datetime
    data_range_end: datetime
    filters: Optional[Dict] = None
    file_url: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
