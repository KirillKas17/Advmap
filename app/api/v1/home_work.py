"""API endpoints для определения дома/работы."""
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.home_work import UserHomeWorkResponse
from app.services.home_work import HomeWorkDetectionService

router = APIRouter(prefix="/home-work", tags=["home-work"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[UserHomeWorkResponse])
def get_home_work_locations(
    location_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить определенные дом/работу пользователя."""
    service = HomeWorkDetectionService(db)
    locations = service.get_user_home_work(
        user_id=current_user.id,
        location_type=location_type,
        company_id=current_user.company_id,
    )
    return locations


@router.post("/analyze", response_model=List[UserHomeWorkResponse])
def analyze_home_work(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Проанализировать геолокацию и определить дом/работу."""
    service = HomeWorkDetectionService(db)
    detected_locations = service.analyze_location_for_home_work(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        company_id=current_user.company_id,
    )
    return detected_locations
