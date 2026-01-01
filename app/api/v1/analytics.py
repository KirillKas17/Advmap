"""API endpoints для B2B аналитики."""
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.analytics import AnalyticsService
from app.schemas.analytics import (
    StatisticsResponse,
    ExportResponse,
    ExportCreate,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)


@router.get("/statistics", response_model=StatisticsResponse)
def get_statistics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    filters: Optional[Dict] = None,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
):
    """Получить агрегированную статистику (B2B API)."""
    service = AnalyticsService(db)
    
    # Проверить API ключ
    client = service.check_api_access(x_api_key)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный или отсутствующий API ключ",
        )
    
    if not start_date:
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
    if not end_date:
        end_date = datetime.now(timezone.utc)
    
    stats = service.get_aggregated_statistics(
        start_date=start_date,
        end_date=end_date,
        filters=filters,
        company_id=client.company_id,
    )
    return stats


@router.post("/export", response_model=ExportResponse, status_code=status.HTTP_201_CREATED)
def create_export(
    export_data: ExportCreate,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
):
    """Создать экспорт данных (B2B API)."""
    service = AnalyticsService(db)
    
    # Проверить API ключ
    client = service.check_api_access(x_api_key)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный или отсутствующий API ключ",
        )
    
    export = service.create_export(
        client_id=client.id,
        export_type=export_data.export_type,
        data_range_start=export_data.data_range_start,
        data_range_end=export_data.data_range_end,
        filters=export_data.filters,
        company_id=client.company_id,
    )
    return export
