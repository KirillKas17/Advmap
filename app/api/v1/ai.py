"""API endpoints для AI-помощника."""
import logging
from typing import List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.ai_service import AIService
from app.schemas.ai import (
    RouteResponse,
    RouteCreate,
    RecommendationResponse,
    ConversationResponse,
    ConversationCreate,
    MessageAdd,
)

router = APIRouter(prefix="/ai", tags=["ai"])
logger = logging.getLogger(__name__)


@router.post("/route/generate", response_model=RouteResponse, status_code=status.HTTP_201_CREATED)
def generate_route(
    route_data: RouteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Сгенерировать маршрут с помощью AI."""
    service = AIService(db)
    route = service.generate_route(
        user_id=current_user.id,
        prompt=route_data.prompt,
        start_location=route_data.start_location,
        company_id=current_user.company_id,
    )
    return route


@router.get("/recommendations", response_model=List[RecommendationResponse])
def get_recommendations(
    latitude: float,
    longitude: float,
    radius_km: float = 5.0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить контекстные рекомендации."""
    service = AIService(db)
    recommendations = service.get_contextual_recommendations(
        user_id=current_user.id,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        company_id=current_user.company_id,
    )
    return recommendations


@router.post("/conversation", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Создать разговор с AI."""
    service = AIService(db)
    conversation = service.create_conversation(
        user_id=current_user.id,
        conversation_type=conversation_data.conversation_type,
        initial_message=conversation_data.message,
        context_data=conversation_data.context_data,
        company_id=current_user.company_id,
    )
    return conversation


@router.post("/conversation/{conversation_id}/message", response_model=ConversationResponse)
def add_message(
    conversation_id: int,
    message_data: MessageAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Добавить сообщение в разговор."""
    service = AIService(db)
    try:
        conversation = service.add_message_to_conversation(
            conversation_id=conversation_id,
            message=message_data.message,
            company_id=current_user.company_id,
        )
        return conversation
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
