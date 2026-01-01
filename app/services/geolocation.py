"""Сервис геолокации."""
import logging
from datetime import datetime, timezone
from typing import List, Optional

from geoalchemy2.shape import from_shape, to_shape
from geopy.distance import distance
from shapely.geometry import Point
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.location import LocationPoint, LocationSession

settings = get_settings()
logger = logging.getLogger(__name__)


class GeolocationService:
    """Сервис для работы с геолокацией."""

    def __init__(self, db: Session):
        """Инициализация сервиса."""
        self.db = db

    def create_location_session(
        self,
        user_id: int,
        is_background: bool = False,
        is_offline: bool = False,
        company_id: Optional[int] = None,
    ) -> LocationSession:
        """Создать новую сессию геолокации."""
        session = LocationSession(
            user_id=user_id,
            session_started_at=datetime.now(timezone.utc),
            is_background=is_background,
            is_offline=is_offline,
            company_id=company_id,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def add_location_point(
        self,
        session_id: int,
        latitude: float,
        longitude: float,
        accuracy_meters: Optional[float] = None,
        altitude_meters: Optional[float] = None,
        speed_ms: Optional[float] = None,
        heading_degrees: Optional[float] = None,
        timestamp: Optional[datetime] = None,
        is_spoofed: bool = False,
        spoofing_score: Optional[float] = None,
        spoofing_reason: Optional[str] = None,
        company_id: Optional[int] = None,
    ) -> LocationPoint:
        """Добавить точку геолокации."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        point = Point(longitude, latitude)
        location_point = LocationPoint(
            session_id=session_id,
            latitude=latitude,
            longitude=longitude,
            point=from_shape(point, srid=4326),
            accuracy_meters=accuracy_meters,
            altitude_meters=altitude_meters,
            speed_ms=speed_ms,
            heading_degrees=heading_degrees,
            timestamp=timestamp,
            is_spoofed=is_spoofed,
            spoofing_score=spoofing_score,
            spoofing_reason=spoofing_reason,
            company_id=company_id,
        )
        self.db.add(location_point)
        self.db.commit()
        self.db.refresh(location_point)
        return location_point

    def get_user_location_points(
        self,
        user_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
        company_id: Optional[int] = None,
    ) -> List[LocationPoint]:
        """Получить точки геолокации пользователя с пагинацией."""
        query = (
            self.db.query(LocationPoint)
            .join(LocationSession)
            .filter(LocationSession.user_id == user_id)
        )

        if company_id is not None:
            query = query.filter(LocationPoint.company_id == company_id)

        if start_time:
            query = query.filter(LocationPoint.timestamp >= start_time)
        if end_time:
            query = query.filter(LocationPoint.timestamp <= end_time)

        return query.order_by(LocationPoint.timestamp.desc()).offset(offset).limit(limit).all()

    def get_last_location_point(
        self, user_id: int, company_id: Optional[int] = None
    ) -> Optional[LocationPoint]:
        """Получить последнюю точку геолокации пользователя."""
        query = (
            self.db.query(LocationPoint)
            .join(LocationSession)
            .filter(LocationSession.user_id == user_id)
        )

        if company_id is not None:
            query = query.filter(LocationPoint.company_id == company_id)

        return query.order_by(LocationPoint.timestamp.desc()).first()

    def calculate_distance_between_points(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Вычислить расстояние между двумя точками в метрах."""
        return distance((lat1, lon1), (lat2, lon2)).meters

    def end_location_session(
        self, session_id: int, synced_at: Optional[datetime] = None
    ) -> LocationSession:
        """Завершить сессию геолокации."""
        session = self.db.query(LocationSession).filter(LocationSession.id == session_id).first()
        if session:
            session.session_ended_at = datetime.now(timezone.utc)
            if synced_at:
                session.synced_at = synced_at
            self.db.commit()
            self.db.refresh(session)
        return session
