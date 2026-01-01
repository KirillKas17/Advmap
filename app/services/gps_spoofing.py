"""Сервис обнаружения спуфинга GPS."""
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.location import LocationPoint, LocationSession
from app.services.geolocation import GeolocationService

settings = get_settings()


class GPSSpoofingDetectionService:
    """Сервис для обнаружения спуфинга GPS."""

    def __init__(self, db: Session):
        """Инициализация сервиса."""
        self.db = db
        self.geolocation_service = GeolocationService(db)

    def detect_spoofing(
        self,
        latitude: float,
        longitude: float,
        accuracy_meters: Optional[float],
        speed_ms: Optional[float],
        timestamp: datetime,
        user_id: int,
        company_id: Optional[int] = None,
    ) -> tuple[bool, float, Optional[str]]:
        """
        Обнаружить спуфинг GPS.

        Returns:
            (is_spoofed, spoofing_score, reason)
        """
        spoofing_score = 0.0
        reasons = []

        # Проверка 1: Нереалистичная скорость
        if speed_ms is not None:
            if speed_ms > settings.gps_spoofing_threshold_speed_ms:
                speed_score = min(1.0, speed_ms / (settings.gps_spoofing_threshold_speed_ms * 2))
                spoofing_score += speed_score * 0.4
                reasons.append(f"Нереалистичная скорость: {speed_ms:.2f} м/с")

        # Проверка 2: Низкая точность
        if accuracy_meters is not None:
            if accuracy_meters > settings.gps_spoofing_threshold_accuracy_meters:
                accuracy_score = min(
                    1.0,
                    (accuracy_meters - settings.gps_spoofing_threshold_accuracy_meters)
                    / settings.gps_spoofing_threshold_accuracy_meters,
                )
                spoofing_score += accuracy_score * 0.3
                reasons.append(f"Низкая точность: {accuracy_meters:.2f} м")

        # Проверка 3: Резкие скачки местоположения
        last_point = self.geolocation_service.get_last_location_point(user_id, company_id)
        if last_point:
            time_diff = (timestamp - last_point.timestamp).total_seconds()
            if time_diff > 0:
                distance_meters = self.geolocation_service.calculate_distance_between_points(
                    last_point.latitude,
                    last_point.longitude,
                    latitude,
                    longitude,
                )
                if time_diff < 10:  # Меньше 10 секунд
                    max_realistic_distance = (last_point.speed_ms or 0) * time_diff + 100
                    if distance_meters > max_realistic_distance * 2:
                        jump_score = min(1.0, distance_meters / (max_realistic_distance * 10))
                        spoofing_score += jump_score * 0.3
                        reasons.append(
                            f"Резкий скачок: {distance_meters:.2f} м за {time_diff:.1f} с"
                        )

        # Нормализация score
        spoofing_score = min(1.0, spoofing_score)
        is_spoofed = spoofing_score > 0.5

        reason = "; ".join(reasons) if reasons else None

        return is_spoofed, spoofing_score, reason

    def verify_location_point(
        self,
        location_point: LocationPoint,
        user_id: int,
        company_id: Optional[int] = None,
    ) -> LocationPoint:
        """Проверить точку геолокации на спуфинг и обновить её."""
        is_spoofed, spoofing_score, reason = self.detect_spoofing(
            location_point.latitude,
            location_point.longitude,
            location_point.accuracy_meters,
            location_point.speed_ms,
            location_point.timestamp,
            user_id,
            company_id,
        )

        location_point.is_spoofed = is_spoofed
        location_point.spoofing_score = spoofing_score
        location_point.spoofing_reason = reason

        self.db.commit()
        self.db.refresh(location_point)

        return location_point

    def verify_location_session(
        self, session_id: int, company_id: Optional[int] = None
    ) -> List[LocationPoint]:
        """Проверить все точки сессии на спуфинг."""
        session = self.db.query(LocationSession).filter(LocationSession.id == session_id).first()
        if not session:
            return []

        points = session.points
        verified_points = []

        for point in points:
            verified_point = self.verify_location_point(point, session.user_id, company_id)
            verified_points.append(verified_point)

        return verified_points
