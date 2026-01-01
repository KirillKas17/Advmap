"""API endpoints для косметики."""
import logging
from typing import List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.cosmetic import CosmeticService
from app.schemas.cosmetic import (
    CosmeticResponse,
    UserCosmeticResponse,
    CosmeticCreate,
    AvatarConfigResponse,
)

router = APIRouter(prefix="/cosmetic", tags=["cosmetic"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[CosmeticResponse])
def get_cosmetics(
    cosmetic_type: Optional[str] = None,
    rarity: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить список косметики."""
    from app.models.cosmetic import Cosmetic
    
    query = (
        db.query(Cosmetic)
        .filter(
            Cosmetic.is_active.is_(True),
            Cosmetic.deleted_at.is_(None)
        )
    )
    
    if cosmetic_type:
        query = query.filter(Cosmetic.cosmetic_type == cosmetic_type)
    if rarity:
        query = query.filter(Cosmetic.rarity == rarity)
    if current_user.company_id is not None:
        query = query.filter(Cosmetic.company_id == current_user.company_id)
    
    cosmetics = query.offset(offset).limit(limit).all()
    return cosmetics


@router.get("/my", response_model=List[UserCosmeticResponse])
def get_my_cosmetics(
    cosmetic_type: Optional[str] = None,
    is_equipped: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить мою косметику."""
    service = CosmeticService(db)
    cosmetics = service.get_user_cosmetics(
        user_id=current_user.id,
        cosmetic_type=cosmetic_type,
        is_equipped=is_equipped,
        company_id=current_user.company_id,
        limit=limit,
        offset=offset,
    )
    return cosmetics


@router.post("/equip/{cosmetic_id}", response_model=UserCosmeticResponse)
def equip_cosmetic(
    cosmetic_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Надеть косметику."""
    service = CosmeticService(db)
    try:
        user_cosmetic = service.equip_cosmetic(
            user_id=current_user.id,
            cosmetic_id=cosmetic_id,
            company_id=current_user.company_id,
        )
        return user_cosmetic
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/unequip/{cosmetic_id}", response_model=UserCosmeticResponse)
def unequip_cosmetic(
    cosmetic_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Снять косметику."""
    service = CosmeticService(db)
    try:
        user_cosmetic = service.unequip_cosmetic(
            user_id=current_user.id,
            cosmetic_id=cosmetic_id,
            company_id=current_user.company_id,
        )
        return user_cosmetic
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/avatar", response_model=AvatarConfigResponse)
def get_avatar_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить конфигурацию аватара."""
    service = CosmeticService(db)
    config = service.get_avatar_config(
        user_id=current_user.id,
        company_id=current_user.company_id,
    )
    return {"avatar_config": config or {}}


@router.post("/craft/{cosmetic_id}", response_model=UserCosmeticResponse, status_code=status.HTTP_201_CREATED)
def craft_cosmetic(
    cosmetic_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Создать косметику через крафт."""
    service = CosmeticService(db)
    try:
        user_cosmetic = service.craft_cosmetic(
            user_id=current_user.id,
            cosmetic_id=cosmetic_id,
            company_id=current_user.company_id,
        )
        return user_cosmetic
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Ошибка БД при крафте косметики: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании косметики",
        )
