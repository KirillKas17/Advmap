"""API endpoints для платформы создателей."""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.creator import CreatorService
from app.models.creator import Creator
from app.schemas.creator import (
    CreatorResponse,
    CreatorApplyRequest,
    PremiumQuestCreate,
)

router = APIRouter(prefix="/creator", tags=["creator"])
logger = logging.getLogger(__name__)


@router.post("/apply", response_model=CreatorResponse, status_code=status.HTTP_201_CREATED)
def apply_as_creator(
    request: CreatorApplyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Подать заявку на статус создателя."""
    service = CreatorService(db)
    try:
        creator = service.apply_as_creator(
            user_id=current_user.id,
            display_name=request.display_name,
            bio=request.bio,
            company_id=current_user.company_id,
        )
        return creator
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/me", response_model=Optional[CreatorResponse])
def get_my_creator_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить мой профиль создателя."""
    from app.models.creator import Creator
    
    creator = (
        db.query(Creator)
        .filter(Creator.user_id == current_user.id)
    )
    if current_user.company_id is not None:
        creator = creator.filter(Creator.company_id == current_user.company_id)
    creator = creator.first()
    
    return creator


@router.post("/quest/premium", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_premium_quest(
    quest_data: PremiumQuestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Создать платный квест."""
    from app.models.creator import CreatorStatus
    
    creator_service = CreatorService(db)
    
    # Проверить, является ли пользователь создателем
    creator = (
        db.query(Creator)
        .filter(
            Creator.user_id == current_user.id,
            Creator.status == CreatorStatus.APPROVED
        )
    )
    if current_user.company_id is not None:
        creator = creator.filter(Creator.company_id == current_user.company_id)
    creator = creator.first()
    
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не являетесь одобренным создателем",
        )
    
    try:
        quest = creator_service.create_premium_quest(
            creator_id=creator.id,
            name=quest_data.name,
            quest_type=quest_data.quest_type,
            requirements=quest_data.requirements,
            price=quest_data.price,
            description=quest_data.description,
            rewards=quest_data.rewards,
            company_id=current_user.company_id,
        )
        return {"quest_id": quest.id, "message": "Платный квест создан и отправлен на модерацию"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Ошибка БД при создании платного квеста: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании квеста",
        )
