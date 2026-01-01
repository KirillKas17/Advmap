"""Сервис автоматического определения дома и работы."""
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from geoalchemy2.shape import from_shape
from geopy.distance import distance
from shapely.geometry import Point
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.location import LocationPoint, LocationSession
from app.models.user_home_work import UserHomeWork

settings = get_settings()
logger = logging.getLogger(__name__)


class HomeWorkDetectionService:
    """Сервис для автоматического определения дома и работы."""

    def __init__(self, db: Session):
        """Инициализация сервиса."""
        self.db = db

    def cluster_location_points(
        self, points: List[LocationPoint], radius_meters: float
    ) -> List[List[LocationPoint]]:
        """Кластеризовать точки геолокации по близости."""
        if not points:
            return []

        clusters: List[List[LocationPoint]] = []
        used_points = set()

        for point in points:
            if point.id in used_points:
                continue

            cluster = [point]
            used_points.add(point.id)

            for other_point in points:
                if other_point.id in used_points:
                    continue

                dist = distance(
                    (point.latitude, point.longitude),
                    (other_point.latitude, other_point.longitude),
                ).meters

                if dist <= radius_meters:
                    cluster.append(other_point)
                    used_points.add(other_point.id)

            clusters.append(cluster)

        return clusters

    def calculate_cluster_center(self, cluster: List[LocationPoint]) -> Tuple[float, float]:
        """Вычислить центр кластера."""
        if not cluster:
            raise ValueError("Кластер не может быть пустым")

        total_lat = sum(p.latitude for p in cluster)
        total_lon = sum(p.longitude for p in cluster)
        count = len(cluster)

        return total_lat / count, total_lon / count

    def analyze_location_for_home_work(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        company_id: Optional[int] = None,
    ) -> List[UserHomeWork]:
        """
        Проанализировать геолокацию пользователя и определить дом/работу.

        Алгоритм:
        1. Получить все точки геолокации за период
        2. Кластеризовать точки по близости
        3. Для каждого кластера вычислить:
           - Общее количество посещений
           - Общее время пребывания
           - Время суток посещений
        4. Определить дом (ночные посещения, долгое время)
        5. Определить работу (дневные посещения в будни, регулярность)
        """
        if start_date is None:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now(timezone.utc)

        # Получить все точки геолокации
        sessions = (
            self.db.query(LocationSession)
            .filter(
                LocationSession.user_id == user_id,
                LocationSession.session_started_at >= start_date,
                LocationSession.session_started_at <= end_date,
            )
            .all()
        )

        if company_id is not None:
            sessions = [s for s in sessions if s.company_id == company_id]

        all_points: List[LocationPoint] = []
        for session in sessions:
            all_points.extend(session.points)

        if not all_points:
            return []

        # Кластеризовать точки
        clusters = self.cluster_location_points(
            all_points, settings.home_work_cluster_radius_meters
        )

        detected_locations: List[UserHomeWork] = []

        for cluster in clusters:
            if len(cluster) < settings.home_work_min_visits:
                continue

            center_lat, center_lon = self.calculate_cluster_center(cluster)

            # Анализ времени посещений
            visit_times = [p.timestamp for p in cluster]
            visit_times.sort()

            # Вычислить общее время
            total_time_minutes = 0
            if len(visit_times) > 1:
                time_span = (visit_times[-1] - visit_times[0]).total_seconds() / 60
                total_time_minutes = int(time_span)

            # Определить тип локации по времени суток
            night_visits = sum(1 for t in visit_times if 22 <= t.hour or t.hour <= 6)
            day_visits = sum(1 for t in visit_times if 8 <= t.hour <= 18)
            weekend_visits = sum(1 for t in visit_times if t.weekday() >= 5)

            # Определить тип
            location_type = None
            confidence = 0.0

            # Дом: ночные посещения, долгое время, не только будни
            if (
                night_visits >= settings.home_work_min_visits
                and total_time_minutes >= settings.home_work_min_time_minutes
                and weekend_visits > 0
            ):
                location_type = "home"
                confidence = min(
                    1.0,
                    (night_visits / len(cluster)) * 0.5
                    + (total_time_minutes / (settings.home_work_min_time_minutes * 2)) * 0.3
                    + (weekend_visits / len(cluster)) * 0.2,
                )

            # Работа: дневные посещения в будни, регулярность
            elif (
                day_visits >= settings.home_work_min_visits
                and total_time_minutes >= settings.home_work_min_time_minutes
                and weekend_visits / len(cluster) < 0.2
            ):
                location_type = "work"
                confidence = min(
                    1.0,
                    (day_visits / len(cluster)) * 0.5
                    + (total_time_minutes / (settings.home_work_min_time_minutes * 2)) * 0.3
                    + ((len(cluster) - weekend_visits) / len(cluster)) * 0.2,
                )

            if location_type and confidence > 0.5:
                # Проверить, не существует ли уже такая локация
                existing = (
                    self.db.query(UserHomeWork)
                    .filter(
                        UserHomeWork.user_id == user_id,
                        UserHomeWork.location_type == location_type,
                    )
                    .first()
                )

                if existing:
                    # Обновить существующую
                    existing.latitude = center_lat
                    existing.longitude = center_lon
                    existing.point = from_shape(Point(center_lon, center_lat), srid=4326)
                    existing.confidence_score = max(existing.confidence_score, confidence)
                    existing.total_visits += len(cluster)
                    existing.total_time_minutes += total_time_minutes
                    existing.last_updated_at = datetime.now(timezone.utc)
                    detected_locations.append(existing)
                else:
                    # Создать новую
                    new_location = UserHomeWork(
                        user_id=user_id,
                        location_type=location_type,
                        latitude=center_lat,
                        longitude=center_lon,
                        point=from_shape(Point(center_lon, center_lat), srid=4326),
                        radius_meters=settings.home_work_cluster_radius_meters,
                        confidence_score=confidence,
                        total_visits=len(cluster),
                        total_time_minutes=total_time_minutes,
                        first_detected_at=visit_times[0],
                        last_updated_at=datetime.now(timezone.utc),
                        company_id=company_id,
                    )
                    self.db.add(new_location)
                    detected_locations.append(new_location)

        self.db.commit()
        for location in detected_locations:
            self.db.refresh(location)

        logger.info(f"Определено {len(detected_locations)} локаций для пользователя {user_id}")
        return detected_locations

    def get_user_home_work(
        self, user_id: int, location_type: Optional[str] = None, company_id: Optional[int] = None
    ) -> List[UserHomeWork]:
        """Получить определенные дом/работу пользователя."""
        query = self.db.query(UserHomeWork).filter(UserHomeWork.user_id == user_id)

        if location_type:
            query = query.filter(UserHomeWork.location_type == location_type)

        if company_id is not None:
            query = query.filter(UserHomeWork.company_id == company_id)

        return query.all()
