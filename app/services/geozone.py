"""Сервис работы с геозонами (полигонами)."""
import logging
from datetime import datetime, timezone
from typing import List, Optional

from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point, Polygon
from shapely.validation import make_valid
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.geozone import Geozone, GeozoneVisit

settings = get_settings()
logger = logging.getLogger(__name__)


class GeozoneService:
    """Сервис для работы с геозонами."""

    def __init__(self, db: Session):
        """Инициализация сервиса."""
        self.db = db

    def create_geozone(
        self,
        name: str,
        polygon_coordinates: List[List[float]],  # [[lon, lat], [lon, lat], ...]
        geozone_type: str,
        description: Optional[str] = None,
        company_id: Optional[int] = None,
    ) -> Geozone:
        """Создать геозону на основе полигона."""
        if len(polygon_coordinates) < 3:
            raise ValueError("Полигон должен содержать минимум 3 точки")

        polygon = Polygon(polygon_coordinates)
        # Валидация и исправление полигона
        if not polygon.is_valid:
            logger.warning(f"Полигон невалиден, исправление: {name}")
            polygon = make_valid(polygon)

        center = polygon.centroid
        center_lat = center.y
        center_lon = center.x

        geozone = Geozone(
            name=name,
            description=description,
            polygon=from_shape(polygon, srid=4326),
            center_latitude=str(center_lat),
            center_longitude=str(center_lon),
            geozone_type=geozone_type,
            company_id=company_id,
        )
        self.db.add(geozone)
        self.db.commit()
        self.db.refresh(geozone)
        return geozone

    def check_point_in_geozone(
        self, latitude: float, longitude: float, geozone_id: int
    ) -> bool:
        """Проверить, находится ли точка внутри геозоны."""
        geozone = self.db.query(Geozone).filter(Geozone.id == geozone_id).first()
        if not geozone:
            return False

        polygon = to_shape(geozone.polygon)
        point = Point(longitude, latitude)

        return polygon.contains(point)

    def find_geozones_by_point(
        self,
        latitude: float,
        longitude: float,
        geozone_type: Optional[str] = None,
        company_id: Optional[int] = None,
    ) -> List[Geozone]:
        """Найти все геозоны, содержащие данную точку."""
        point = Point(longitude, latitude)
        point_geom = from_shape(point, srid=4326)

        query = self.db.query(Geozone).filter(
            func.ST_Contains(Geozone.polygon, point_geom),
            Geozone.is_active.is_(True),
        )

        if geozone_type:
            query = query.filter(Geozone.geozone_type == geozone_type)

        if company_id is not None:
            query = query.filter(Geozone.company_id == company_id)

        return query.all()

    def create_geozone_visit(
        self,
        user_id: int,
        geozone_id: int,
        visit_started_at: Optional[datetime] = None,
        is_verified: bool = False,
        verification_score: Optional[int] = None,
        company_id: Optional[int] = None,
    ) -> GeozoneVisit:
        """Создать запись о посещении геозоны."""
        if visit_started_at is None:
            visit_started_at = datetime.now(timezone.utc)

        visit = GeozoneVisit(
            user_id=user_id,
            geozone_id=geozone_id,
            visit_started_at=visit_started_at,
            is_verified=is_verified,
            verification_score=verification_score,
            company_id=company_id,
        )
        self.db.add(visit)
        self.db.commit()
        self.db.refresh(visit)

        # Попытаться выдать артефакт при посещении геозоны
        try:
            from app.services.artifact import ArtifactService
            artifact_service = ArtifactService(self.db)
            dropped_artifact = artifact_service.try_drop_artifact_from_geozone(
                user_id=user_id,
                geozone_id=geozone_id,
                company_id=company_id,
            )
            if dropped_artifact:
                logger.info(f"Артефакт выпал при посещении геозоны {geozone_id} пользователем {user_id}")
        except Exception as e:
            logger.warning(f"Ошибка при выдаче артефакта: {e}")

        # Обновить прогресс квестов
        try:
            from app.services.quest import QuestService
            quest_service = QuestService(self.db)
            # Получить активные квесты пользователя
            from app.models.event import UserQuest, QuestStatus
            active_quests = (
                self.db.query(UserQuest)
                .filter(
                    UserQuest.user_id == user_id,
                    UserQuest.status == QuestStatus.IN_PROGRESS
                )
            )
            if company_id is not None:
                active_quests = active_quests.filter(UserQuest.company_id == company_id)
            for user_quest in active_quests.all():
                quest_service.update_quest_progress(
                    user_id=user_id,
                    quest_id=user_quest.quest_id,
                    company_id=company_id,
                )
        except Exception as e:
            logger.warning(f"Ошибка при обновлении прогресса квестов: {e}")

        return visit

    def end_geozone_visit(
        self, visit_id: int, visit_ended_at: Optional[datetime] = None
    ) -> GeozoneVisit:
        """Завершить посещение геозоны."""
        visit = self.db.query(GeozoneVisit).filter(GeozoneVisit.id == visit_id).first()
        if visit:
            if visit_ended_at is None:
                visit_ended_at = datetime.now(timezone.utc)
            visit.visit_ended_at = visit_ended_at
            if visit.visit_started_at:
                duration = (visit_ended_at - visit.visit_started_at).total_seconds()
                visit.duration_seconds = int(duration)
            self.db.commit()
            self.db.refresh(visit)
        return visit

    def get_user_geozone_visits(
        self,
        user_id: int,
        geozone_id: Optional[int] = None,
        company_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[GeozoneVisit]:
        """Получить посещения геозон пользователя с пагинацией."""
        query = self.db.query(GeozoneVisit).filter(GeozoneVisit.user_id == user_id)

        if geozone_id:
            query = query.filter(GeozoneVisit.geozone_id == geozone_id)

        if company_id is not None:
            query = query.filter(GeozoneVisit.company_id == company_id)

        return query.order_by(GeozoneVisit.visit_started_at.desc()).offset(offset).limit(limit).all()

    def get_geozone_by_id(
        self, geozone_id: int, company_id: Optional[int] = None
    ) -> Optional[Geozone]:
        """Получить геозону по ID с проверкой company_id и soft delete."""
        query = (
            self.db.query(Geozone)
            .filter(
                Geozone.id == geozone_id,
                Geozone.deleted_at.is_(None)
            )
        )
        if company_id is not None:
            query = query.filter(Geozone.company_id == company_id)
        return query.first()

    def get_all_active_geozones(
        self,
        geozone_type: Optional[str] = None,
        company_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Geozone]:
        """Получить все активные геозоны с фильтрацией по soft delete и пагинацией."""
        query = (
            self.db.query(Geozone)
            .filter(
                Geozone.is_active.is_(True),
                Geozone.deleted_at.is_(None)
            )
        )

        if geozone_type:
            query = query.filter(Geozone.geozone_type == geozone_type)

        if company_id is not None:
            query = query.filter(Geozone.company_id == company_id)

        return query.offset(offset).limit(limit).all()
