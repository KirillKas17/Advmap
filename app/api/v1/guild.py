"""API endpoints для гильдий."""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.guild import GuildService
from app.schemas.guild import (
    GuildResponse,
    GuildMemberResponse,
    GuildCreate,
    JoinGuildRequest,
)

router = APIRouter(prefix="/guild", tags=["guild"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=GuildResponse, status_code=status.HTTP_201_CREATED)
def create_guild(
    guild_data: GuildCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Создать гильдию."""
    service = GuildService(db)
    try:
        guild = service.create_guild(
            name=guild_data.name,
            leader_id=current_user.id,
            description=guild_data.description,
            tag=guild_data.tag,
            banner_url=guild_data.banner_url,
            max_members=guild_data.max_members,
            company_id=current_user.company_id,
        )
        return guild
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Ошибка БД при создании гильдии: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании гильдии",
        )


@router.post("/{guild_id}/join", response_model=GuildMemberResponse, status_code=status.HTTP_201_CREATED)
def join_guild(
    guild_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Присоединиться к гильдии."""
    service = GuildService(db)
    try:
        member = service.join_guild(
            guild_id=guild_id,
            user_id=current_user.id,
            company_id=current_user.company_id,
        )
        return member
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/my", response_model=Optional[GuildMemberResponse])
def get_my_guild(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить мою гильдию."""
    from app.models.guild import GuildMember
    
    member = (
        db.query(GuildMember)
        .filter(GuildMember.user_id == current_user.id)
    )
    if current_user.company_id is not None:
        member = member.filter(GuildMember.company_id == current_user.company_id)
    member = member.first()
    
    return member


@router.get("/{guild_id}", response_model=GuildResponse)
def get_guild(
    guild_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить информацию о гильдии."""
    from app.models.guild import Guild, GuildStatus
    
    guild = (
        db.query(Guild)
        .filter(
            Guild.id == guild_id,
            Guild.deleted_at.is_(None)
        )
    )
    if current_user.company_id is not None:
        guild = guild.filter(Guild.company_id == current_user.company_id)
    guild = guild.first()
    
    if not guild:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Гильдия не найдена",
        )
    
    return guild
