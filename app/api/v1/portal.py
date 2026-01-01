"""API endpoints для порталов."""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.portal import PortalService
from app.schemas.portal import (
    PortalResponse,
    PortalInteractionResponse,
    PortalCreate,
    PortalInteractionCreate,
)

router = APIRouter(prefix="/portal", tags=["portal"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=PortalResponse, status_code=status.HTTP_201_CREATED)
def create_portal(
    portal_data: PortalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Создать портал."""
    service = PortalService(db)
    portal = service.create_portal(
        name=portal_data.name,
        portal_type=portal_data.portal_type,
        latitude=portal_data.latitude,
        longitude=portal_data.longitude,
        description=portal_data.description,
        installed_by_user_id=current_user.id,
        installed_artifact_id=portal_data.installed_artifact_id,
        is_public=portal_data.is_public,
        company_id=current_user.company_id,
    )
    return portal


@router.get("/nearby", response_model=List[PortalResponse])
def get_nearby_portals(
    latitude: float,
    longitude: float,
    radius_meters: float = 1000.0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Найти порталы рядом."""
    service = PortalService(db)
    portals = service.find_nearby_portals(
        latitude=latitude,
        longitude=longitude,
        radius_meters=radius_meters,
        company_id=current_user.company_id,
        limit=limit,
    )
    return portals


@router.post("/{portal_id}/interact", response_model=PortalInteractionResponse, status_code=status.HTTP_201_CREATED)
def interact_with_portal(
    portal_id: int,
    interaction_data: PortalInteractionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Взаимодействовать с порталом."""
    service = PortalService(db)
    try:
        interaction = service.interact_with_portal(
            portal_id=portal_id,
            user_id=current_user.id,
            interaction_type=interaction_data.interaction_type,
            artifact_left_id=interaction_data.artifact_left_id,
            artifact_taken_id=interaction_data.artifact_taken_id,
            company_id=current_user.company_id,
        )
        return interaction
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
