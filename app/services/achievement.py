"""Сервис достижений."""
import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.achievement import Achievement, UserAchievement
from app.models.geozone import GeozoneVisit
from app.models.location import LocationPoint, LocationSession

settings = get_settings()
logger = logging.getLogger(__name__)


class AchievementService:
    """Сервис для работы с достижениями."""

    def __init__(self, db: Session):
        """Инициализация сервиса."""
        self.db = db

    def create_achievement(
        self,
        name: str,
        achievement_type: str,
        description: Optional[str] = None,
        icon_url: Optional[str] = None,
        requirement_value: Optional[int] = None,
        geozone_id: Optional[int] = None,
        company_id: Optional[int] = None,
    ) -> Achievement:
        """Создать новое достижение."""
        achievement = Achievement(
            name=name,
            description=description,
            icon_url=icon_url,
            achievement_type=achievement_type,
            requirement_value=requirement_value,
            geozone_id=geozone_id,
            company_id=company_id,
        )
        self.db.add(achievement)
        self.db.commit()
        self.db.refresh(achievement)
        return achievement

    def check_and_unlock_achievements(
        self, user_id: int, company_id: Optional[int] = None
    ) -> List[UserAchievement]:
        """Проверить и разблокировать достижения пользователя."""
        unlocked_achievements = []

        # Получить все активные достижения с фильтрацией по company_id и soft delete
        query = (
            self.db.query(Achievement)
            .filter(
                Achievement.is_active.is_(True),
                Achievement.deleted_at.is_(None)
            )
        )

        if company_id is not None:
            query = query.filter(Achievement.company_id == company_id)

        achievements = query.all()

        for achievement in achievements:
            # Проверить, не разблокировано ли уже
            existing = (
                self.db.query(UserAchievement)
                .filter(
                    UserAchievement.user_id == user_id,
                    UserAchievement.achievement_id == achievement.id,
                )
                .first()
            )

            if existing:
                continue

            # Проверить условие разблокировки
            progress = self._calculate_achievement_progress(user_id, achievement, company_id)

            if progress >= (achievement.requirement_value or 1):
                user_achievement = UserAchievement(
                    user_id=user_id,
                    achievement_id=achievement.id,
                    unlocked_at=datetime.now(timezone.utc),
                    progress_value=progress,
                    company_id=company_id,
                )
                self.db.add(user_achievement)
                unlocked_achievements.append(user_achievement)
                logger.info(f"Разблокировано достижение: {achievement.name} для пользователя {user_id}")

        if unlocked_achievements:
            self.db.commit()
            for ua in unlocked_achievements:
                self.db.refresh(ua)

            # Обновить прогресс квестов при разблокировке достижений
            try:
                from app.services.quest import QuestService
                quest_service = QuestService(self.db)
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

        return unlocked_achievements

    def _calculate_achievement_progress(
        self, user_id: int, achievement: Achievement, company_id: Optional[int] = None
    ) -> int:
        """Вычислить прогресс достижения."""
        if achievement.achievement_type == "geozone":
            if achievement.geozone_id:
                query = (
                    self.db.query(func.count(GeozoneVisit.id))
                    .filter(
                        GeozoneVisit.user_id == user_id,
                        GeozoneVisit.geozone_id == achievement.geozone_id,
                    )
                )
                if company_id is not None:
                    query = query.filter(GeozoneVisit.company_id == company_id)
                return query.scalar() or 0

        elif achievement.achievement_type == "visits":
            query = self.db.query(func.count(GeozoneVisit.id)).filter(
                GeozoneVisit.user_id == user_id
            )
            if company_id is not None:
                query = query.filter(GeozoneVisit.company_id == company_id)
            return query.scalar() or 0

        elif achievement.achievement_type == "distance":
            # Подсчет пройденного расстояния в метрах
            from geopy.distance import distance as geopy_distance
            
            # Получить все точки геолокации пользователя
            points_query = (
                self.db.query(LocationPoint)
                .join(LocationSession)
                .filter(
                    LocationSession.user_id == user_id,
                    LocationPoint.is_spoofed.is_(False)
                )
                .order_by(LocationPoint.timestamp)
            )
            
            if company_id is not None:
                points_query = points_query.filter(LocationPoint.company_id == company_id)
            
            points = points_query.all()
            
            if len(points) < 2:
                return 0
            
            # Вычислить общее расстояние между последовательными точками
            total_distance_meters = 0.0
            for i in range(len(points) - 1):
                point1 = points[i]
                point2 = points[i + 1]
                dist = geopy_distance(
                    (point1.latitude, point1.longitude),
                    (point2.latitude, point2.longitude)
                ).meters
                total_distance_meters += dist
            
            return int(total_distance_meters)

        return 0

    def get_user_achievements(
        self,
        user_id: int,
        company_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[UserAchievement]:
        """Получить достижения пользователя с пагинацией."""
        query = self.db.query(UserAchievement).filter(UserAchievement.user_id == user_id)

        if company_id is not None:
            query = query.filter(UserAchievement.company_id == company_id)

        return query.order_by(UserAchievement.unlocked_at.desc()).offset(offset).limit(limit).all()

    def get_achievement_by_id(
        self, achievement_id: int, company_id: Optional[int] = None
    ) -> Optional[Achievement]:
        """Получить достижение по ID с проверкой company_id."""
        query = (
            self.db.query(Achievement)
            .filter(
                Achievement.id == achievement_id,
                Achievement.deleted_at.is_(None)
            )
        )
        if company_id is not None:
            query = query.filter(Achievement.company_id == company_id)
        return query.first()
