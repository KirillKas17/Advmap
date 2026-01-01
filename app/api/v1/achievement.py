"""API endpoints для достижений."""
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.achievement import AchievementResponse, UserAchievementResponse
from app.services.achievement import AchievementService

router = APIRouter(prefix="/achievement", tags=["achievement"])


@router.get("/my", response_model=List[UserAchievementResponse])
def get_my_achievements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить мои достижения."""
    service = AchievementService(db)
    achievements = service.get_user_achievements(
        user_id=current_user.id,
        company_id=current_user.company_id,
    )
    return achievements


@router.post("/check", response_model=List[UserAchievementResponse])
def check_achievements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Проверить и разблокировать достижения."""
    service = AchievementService(db)
    unlocked = service.check_and_unlock_achievements(
        user_id=current_user.id,
        company_id=current_user.company_id,
    )
    return unlocked
