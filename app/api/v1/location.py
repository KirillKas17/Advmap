"""API endpoints для геолокации."""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.location import LocationSession
from app.models.user import User
from app.schemas.location import (
    LocationPointCreate,
    LocationPointResponse,
    LocationSessionResponse,
    OfflineSyncRequest,
    BatchOfflineSyncRequest,
)
from app.services.geolocation import GeolocationService
from app.services.offline_sync import OfflineSyncService

router = APIRouter(prefix="/location", tags=["location"])


@router.post("/session", response_model=LocationSessionResponse, status_code=status.HTTP_201_CREATED)
def create_location_session(
    is_background: bool = False,
    is_offline: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Создать новую сессию геолокации."""
    service = GeolocationService(db)
    session = service.create_location_session(
        user_id=current_user.id,
        is_background=is_background,
        is_offline=is_offline,
        company_id=current_user.company_id,
    )
    return session


@router.post("/session/{session_id}/point", response_model=LocationPointResponse, status_code=status.HTTP_201_CREATED)
def add_location_point(
    session_id: int,
    point_data: LocationPointCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Добавить точку геолокации в сессию."""
    service = GeolocationService(db)

    # Проверить, что сессия принадлежит пользователю
    session = db.query(LocationSession).filter(LocationSession.id == session_id).first()
    if not session or session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сессия не найдена",
        )

    location_point = service.add_location_point(
        session_id=session_id,
        latitude=point_data.latitude,
        longitude=point_data.longitude,
        accuracy_meters=point_data.accuracy_meters,
        altitude_meters=point_data.altitude_meters,
        speed_ms=point_data.speed_ms,
        heading_degrees=point_data.heading_degrees,
        timestamp=point_data.timestamp,
        company_id=current_user.company_id,
    )
    return location_point


@router.post("/offline/sync", response_model=LocationSessionResponse, status_code=status.HTTP_201_CREATED)
def sync_offline_data(
    sync_data: OfflineSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Синхронизировать данные, собранные в офлайн режиме."""
    service = OfflineSyncService(db)

    points_data = [
        {
            "latitude": p.latitude,
            "longitude": p.longitude,
            "accuracy_meters": p.accuracy_meters,
            "altitude_meters": p.altitude_meters,
            "speed_ms": p.speed_ms,
            "heading_degrees": p.heading_degrees,
            "timestamp": p.timestamp or datetime.utcnow(),
        }
        for p in sync_data.points
    ]

    session = service.sync_offline_location_points(
        user_id=current_user.id,
        points_data=points_data,
        company_id=current_user.company_id,
    )

    if sync_data.session_started_at:
        session.session_started_at = sync_data.session_started_at
    if sync_data.session_ended_at:
        session.session_ended_at = sync_data.session_ended_at

    db.commit()
    db.refresh(session)

    return session


@router.post("/offline/batch-sync", response_model=List[LocationSessionResponse], status_code=status.HTTP_201_CREATED)
def batch_sync_offline_data(
    batch_data: BatchOfflineSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Пакетная синхронизация офлайн данных."""
    service = OfflineSyncService(db)

    sessions_data = []
    for session_data in batch_data.sessions:
        points_data = [
            {
                "latitude": p.latitude,
                "longitude": p.longitude,
                "accuracy_meters": p.accuracy_meters,
                "altitude_meters": p.altitude_meters,
                "speed_ms": p.speed_ms,
                "heading_degrees": p.heading_degrees,
                "timestamp": p.timestamp or datetime.utcnow(),
            }
            for p in session_data.points
        ]
        sessions_data.append(
            {
                "points": points_data,
                "session_started_at": session_data.session_started_at,
                "session_ended_at": session_data.session_ended_at,
            }
        )

    synced_sessions = service.batch_sync_offline_data(
        user_id=current_user.id,
        sessions_data=sessions_data,
        company_id=current_user.company_id,
    )

    return synced_sessions


@router.get("/points", response_model=List[LocationPointResponse])
def get_location_points(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить точки геолокации пользователя."""
    service = GeolocationService(db)
    points = service.get_user_location_points(
        user_id=current_user.id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        company_id=current_user.company_id,
    )
    return points


@router.get("/last", response_model=Optional[LocationPointResponse])
def get_last_location_point(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить последнюю точку геолокации пользователя."""
    service = GeolocationService(db)
    point = service.get_last_location_point(
        user_id=current_user.id,
        company_id=current_user.company_id,
    )
    return point
