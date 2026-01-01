"""API endpoints для метавселенной воспоминаний."""
import logging
from typing import List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.memory import MemoryService
from app.schemas.memory import (
    MemoryResponse,
    MemoryCreate,
    MemoryTimelineResponse,
)

router = APIRouter(prefix="/memory", tags=["memory"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
def create_memory(
    memory_data: MemoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Создать воспоминание."""
    service = MemoryService(db)
    memory = service.create_memory(
        user_id=current_user.id,
        title=memory_data.title,
        memory_type=memory_data.memory_type,
        description=memory_data.description,
        location_data=memory_data.location_data,
        media_urls=memory_data.media_urls,
        tags=memory_data.tags,
        emotion_score=memory_data.emotion_score,
        related_geozone_id=memory_data.related_geozone_id,
        related_achievement_id=memory_data.related_achievement_id,
        related_event_id=memory_data.related_event_id,
        is_public=memory_data.is_public,
        is_favorite=memory_data.is_favorite,
        company_id=current_user.company_id,
    )
    return memory


@router.get("/my", response_model=List[MemoryResponse])
def get_my_memories(
    memory_type: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить мои воспоминания."""
    service = MemoryService(db)
    memories = service.get_user_memories(
        user_id=current_user.id,
        memory_type=memory_type,
        is_favorite=is_favorite,
        company_id=current_user.company_id,
        limit=limit,
        offset=offset,
    )
    return memories


@router.get("/timeline", response_model=MemoryTimelineResponse)
def get_memory_timeline(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить временную линию воспоминаний для 3D визуализации."""
    service = MemoryService(db)
    timeline = service.get_memory_timeline(
        user_id=current_user.id,
        company_id=current_user.company_id,
    )
    return {"timeline": timeline}
