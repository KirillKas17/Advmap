"""API endpoints для артефактов."""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.artifact import ArtifactService
from app.schemas.artifact import (
    ArtifactResponse,
    UserArtifactResponse,
    ArtifactCreate,
    ArtifactStatisticsResponse,
)

router = APIRouter(prefix="/artifact", tags=["artifact"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[ArtifactResponse])
def get_artifacts(
    rarity: Optional[str] = None,
    artifact_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить список артефактов."""
    from app.models.artifact import Artifact
    
    query = (
        db.query(Artifact)
        .filter(
            Artifact.is_active.is_(True),
            Artifact.deleted_at.is_(None)
        )
    )
    
    if rarity:
        query = query.filter(Artifact.rarity == rarity)
    if artifact_type:
        query = query.filter(Artifact.artifact_type == artifact_type)
    if current_user.company_id is not None:
        query = query.filter(Artifact.company_id == current_user.company_id)
    
    artifacts = query.offset(offset).limit(limit).all()
    return artifacts


@router.get("/my", response_model=List[UserArtifactResponse])
def get_my_artifacts(
    artifact_id: Optional[int] = None,
    rarity: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить мои артефакты."""
    service = ArtifactService(db)
    artifacts = service.get_user_artifacts(
        user_id=current_user.id,
        artifact_id=artifact_id,
        rarity=rarity,
        company_id=current_user.company_id,
        limit=limit,
        offset=offset,
    )
    return artifacts


@router.get("/statistics", response_model=ArtifactStatisticsResponse)
def get_artifact_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить статистику по артефактам."""
    service = ArtifactService(db)
    stats = service.get_artifact_statistics(
        user_id=current_user.id,
        company_id=current_user.company_id,
    )
    return stats


@router.post("/craft/{artifact_id}", response_model=UserArtifactResponse, status_code=status.HTTP_201_CREATED)
def craft_artifact(
    artifact_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Создать артефакт через крафт."""
    service = ArtifactService(db)
    try:
        user_artifact = service.craft_artifact(
            user_id=current_user.id,
            artifact_id=artifact_id,
            company_id=current_user.company_id,
        )
        return user_artifact
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Ошибка БД при крафте артефакта: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании артефакта",
        )
