"""API endpoints для событий и квестов."""
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.quest import QuestService
from app.schemas.quest import (
    EventResponse,
    QuestResponse,
    UserQuestResponse,
    EventCreate,
    QuestCreate,
)

router = APIRouter(prefix="/quest", tags=["quest"])
logger = logging.getLogger(__name__)


@router.get("/events", response_model=List[EventResponse])
def get_events(
    event_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить список событий."""
    from app.models.event import Event, EventStatus
    
    query = (
        db.query(Event)
        .filter(
            Event.is_active.is_(True),
            Event.deleted_at.is_(None),
            Event.status == EventStatus.ACTIVE
        )
    )
    
    if event_type:
        query = query.filter(Event.event_type == event_type)
    if current_user.company_id is not None:
        query = query.filter(Event.company_id == current_user.company_id)
    
    events = query.order_by(Event.start_date.desc()).offset(offset).limit(limit).all()
    return events


@router.get("/available", response_model=List[QuestResponse])
def get_available_quests(
    event_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить доступные квесты."""
    service = QuestService(db)
    quests = service.get_available_quests(
        user_id=current_user.id,
        event_id=event_id,
        company_id=current_user.company_id,
        limit=limit,
        offset=offset,
    )
    return quests


@router.get("/my", response_model=List[UserQuestResponse])
def get_my_quests(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить мои квесты."""
    from app.models.event import UserQuest, QuestStatus
    
    query = (
        db.query(UserQuest)
        .filter(UserQuest.user_id == current_user.id)
    )
    
    if status:
        query = query.filter(UserQuest.status == QuestStatus(status))
    if current_user.company_id is not None:
        query = query.filter(UserQuest.company_id == current_user.company_id)
    
    quests = query.order_by(UserQuest.created_at.desc()).offset(offset).limit(limit).all()
    return quests


@router.post("/start/{quest_id}", response_model=UserQuestResponse)
def start_quest(
    quest_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Начать выполнение квеста."""
    service = QuestService(db)
    try:
        user_quest = service.start_quest(
            user_id=current_user.id,
            quest_id=quest_id,
            company_id=current_user.company_id,
        )
        return user_quest
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Ошибка БД при начале квеста: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при начале квеста",
        )


@router.post("/update-progress/{quest_id}", response_model=UserQuestResponse)
def update_quest_progress(
    quest_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Обновить прогресс выполнения квеста."""
    service = QuestService(db)
    user_quest = service.update_quest_progress(
        user_id=current_user.id,
        quest_id=quest_id,
        company_id=current_user.company_id,
    )
    
    if not user_quest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Квест не найден или не начат",
        )
    
    return user_quest
