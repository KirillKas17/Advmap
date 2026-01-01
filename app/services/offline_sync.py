"""Сервис синхронизации офлайн данных."""
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.location import LocationPoint, LocationSession
from app.services.geolocation import GeolocationService
from app.services.gps_spoofing import GPSSpoofingDetectionService

settings = get_settings()


class OfflineSyncService:
    """Сервис для синхронизации данных, собранных в офлайн режиме."""

    def __init__(self, db: Session):
        """Инициализация сервиса."""
        self.db = db
        self.geolocation_service = GeolocationService(db)
        self.spoofing_service = GPSSpoofingDetectionService(db)

    def sync_offline_location_points(
        self,
        user_id: int,
        points_data: List[dict],
        company_id: Optional[int] = None,
    ) -> LocationSession:
        """
        Синхронизировать точки геолокации, собранные в офлайн режиме.

        Args:
            user_id: ID пользователя
            points_data: Список словарей с данными точек:
                {
                    "latitude": float,
                    "longitude": float,
                    "accuracy_meters": float,
                    "altitude_meters": float,
                    "speed_ms": float,
                    "heading_degrees": float,
                    "timestamp": datetime или ISO string
                }
            company_id: ID компании (для мультитенантности)

        Returns:
            LocationSession: Созданная или обновленная сессия
        """
        if not points_data:
            raise ValueError("Список точек не может быть пустым")

        # Сортировать точки по времени
        sorted_points = sorted(
            points_data,
            key=lambda x: (
                x["timestamp"]
                if isinstance(x["timestamp"], datetime)
                else datetime.fromisoformat(x["timestamp"])
            ),
        )

        first_timestamp = (
            sorted_points[0]["timestamp"]
            if isinstance(sorted_points[0]["timestamp"], datetime)
            else datetime.fromisoformat(sorted_points[0]["timestamp"])
        )
        last_timestamp = (
            sorted_points[-1]["timestamp"]
            if isinstance(sorted_points[-1]["timestamp"], datetime)
            else datetime.fromisoformat(sorted_points[-1]["timestamp"])
        )

        # Создать сессию для офлайн данных
        session = self.geolocation_service.create_location_session(
            user_id=user_id,
            is_background=True,
            is_offline=True,
            company_id=company_id,
        )

        # Добавить все точки
        synced_points = []
        for point_data in sorted_points:
            timestamp = (
                point_data["timestamp"]
                if isinstance(point_data["timestamp"], datetime)
                else datetime.fromisoformat(point_data["timestamp"])
            )

            # Проверить на спуфинг перед добавлением
            is_spoofed, spoofing_score, reason = self.spoofing_service.detect_spoofing(
                latitude=point_data["latitude"],
                longitude=point_data["longitude"],
                accuracy_meters=point_data.get("accuracy_meters"),
                speed_ms=point_data.get("speed_ms"),
                timestamp=timestamp,
                user_id=user_id,
                company_id=company_id,
            )

            location_point = self.geolocation_service.add_location_point(
                session_id=session.id,
                latitude=point_data["latitude"],
                longitude=point_data["longitude"],
                accuracy_meters=point_data.get("accuracy_meters"),
                altitude_meters=point_data.get("altitude_meters"),
                speed_ms=point_data.get("speed_ms"),
                heading_degrees=point_data.get("heading_degrees"),
                timestamp=timestamp,
                is_spoofed=is_spoofed,
                spoofing_score=spoofing_score,
                spoofing_reason=reason,
                company_id=company_id,
            )
            synced_points.append(location_point)

        # Обновить сессию
        session.session_started_at = first_timestamp
        session.session_ended_at = last_timestamp
        session.synced_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(session)

        return session

    def batch_sync_offline_data(
        self,
        user_id: int,
        sessions_data: List[dict],
        company_id: Optional[int] = None,
    ) -> List[LocationSession]:
        """
        Пакетная синхронизация нескольких сессий офлайн данных.

        Args:
            user_id: ID пользователя
            sessions_data: Список словарей с данными сессий:
                {
                    "points": [...],
                    "session_started_at": datetime,
                    "session_ended_at": datetime
                }
            company_id: ID компании

        Returns:
            List[LocationSession]: Список созданных сессий
        """
        synced_sessions = []

        for session_data in sessions_data:
            points = session_data.get("points", [])
            if not points:
                continue

            session = self.sync_offline_location_points(
                user_id=user_id,
                points_data=points,
                company_id=company_id,
            )

            # Обновить временные метки сессии, если указаны
            if "session_started_at" in session_data:
                session.session_started_at = (
                    session_data["session_started_at"]
                    if isinstance(session_data["session_started_at"], datetime)
                    else datetime.fromisoformat(session_data["session_started_at"])
                )
            if "session_ended_at" in session_data:
                session.session_ended_at = (
                    session_data["session_ended_at"]
                    if isinstance(session_data["session_ended_at"], datetime)
                    else datetime.fromisoformat(session_data["session_ended_at"])
                )

            self.db.commit()
            self.db.refresh(session)
            synced_sessions.append(session)

        return synced_sessions
