"""Сервис работы с квестами и событиями."""
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.event import Event, Quest, UserQuest, UserEvent, EventStatus, QuestStatus, QuestType
from app.models.achievement import UserAchievement
from app.models.geozone import GeozoneVisit
from app.models.location import LocationPoint, LocationSession
from app.models.artifact import UserArtifact
from app.services.marketplace import MarketplaceService

settings = get_settings()
logger = logging.getLogger(__name__)


class QuestService:
    """Сервис для работы с квестами и событиями."""

    def __init__(self, db: Session):
        """Инициализация сервиса."""
        self.db = db

    def create_event(
        self,
        name: str,
        event_type: str,
        start_date: datetime,
        end_date: datetime,
        description: Optional[str] = None,
        banner_url: Optional[str] = None,
        reward_data: Optional[Dict] = None,
        company_id: Optional[int] = None,
    ) -> Event:
        """Создать событие."""
        from app.models.event import EventType
        
        event = Event(
            name=name,
            description=description,
            banner_url=banner_url,
            event_type=EventType(event_type),
            start_date=start_date,
            end_date=end_date,
            reward_data=reward_data or {},
            company_id=company_id,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        logger.info(f"Создано событие: {event.id} ({event.name})")
        return event

    def create_quest(
        self,
        name: str,
        quest_type: QuestType,
        requirements: Dict,
        event_id: Optional[int] = None,
        description: Optional[str] = None,
        rewards: Optional[Dict] = None,
        is_repeatable: bool = False,
        max_completions: Optional[int] = None,
        expires_at: Optional[datetime] = None,
        is_premium: bool = False,
        price: Optional[int] = None,
        creator_id: Optional[int] = None,
        company_id: Optional[int] = None,
    ) -> Quest:
        """Создать квест."""
        quest = Quest(
            event_id=event_id,
            name=name,
            description=description,
            quest_type=quest_type,
            requirements=requirements,
            rewards=rewards or {},
            is_repeatable=is_repeatable,
            max_completions=max_completions,
            expires_at=expires_at,
            is_premium=is_premium,
            price=price,
            creator_id=creator_id,
            company_id=company_id,
        )
        self.db.add(quest)
        self.db.commit()
        self.db.refresh(quest)
        logger.info(f"Создан квест: {quest.id} ({quest.name})")
        return quest

    def get_available_quests(
        self,
        user_id: int,
        event_id: Optional[int] = None,
        company_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Quest]:
        """Получить доступные квесты для пользователя."""
        query = (
            self.db.query(Quest)
            .filter(
                Quest.is_active.is_(True),
                Quest.deleted_at.is_(None)
            )
        )

        if event_id:
            query = query.filter(Quest.event_id == event_id)
        if company_id is not None:
            query = query.filter(Quest.company_id == company_id)

        # Исключить уже завершенные не повторяемые квесты
        completed_quest_ids = (
            self.db.query(UserQuest.quest_id)
            .filter(
                UserQuest.user_id == user_id,
                UserQuest.status == QuestStatus.COMPLETED
            )
            .subquery()
        )

        query = query.filter(
            (Quest.is_repeatable.is_(True)) |
            (~Quest.id.in_(completed_quest_ids))
        )

        return query.order_by(Quest.created_at.desc()).offset(offset).limit(limit).all()

    def start_quest(
        self,
        user_id: int,
        quest_id: int,
        company_id: Optional[int] = None,
    ) -> UserQuest:
        """Начать выполнение квеста."""
        quest = (
            self.db.query(Quest)
            .filter(
                Quest.id == quest_id,
                Quest.is_active.is_(True),
                Quest.deleted_at.is_(None)
            )
        )
        if company_id is not None:
            quest = quest.filter(Quest.company_id == company_id)
        quest = quest.first()

        if not quest:
            raise ValueError("Квест не найден")

        if quest.is_premium and quest.price:
            # Проверить оплату для платных квестов
            marketplace_service = MarketplaceService(self.db)
            currency = marketplace_service._get_or_create_currency(user_id, company_id)
            if currency.coins < quest.price:
                raise ValueError("Недостаточно средств для покупки квеста")

            # Списать деньги
            currency.coins -= quest.price
            marketplace_service._add_currency_transaction(
                currency.id,
                -quest.price,
                "coins",
                "quest_purchase",
                quest_id,
                company_id
            )

        # Проверить, не начат ли уже квест
        existing = (
            self.db.query(UserQuest)
            .filter(
                UserQuest.user_id == user_id,
                UserQuest.quest_id == quest_id,
                UserQuest.status.in_([QuestStatus.AVAILABLE, QuestStatus.IN_PROGRESS])
            )
        )
        if company_id is not None:
            existing = existing.filter(UserQuest.company_id == company_id)
        existing = existing.first()

        if existing:
            if existing.status == QuestStatus.IN_PROGRESS:
                return existing
            existing.status = QuestStatus.IN_PROGRESS
            existing.started_at = datetime.now(timezone.utc)
            user_quest = existing
        else:
            user_quest = UserQuest(
                user_id=user_id,
                quest_id=quest_id,
                status=QuestStatus.IN_PROGRESS,
                progress=self._initialize_progress(quest),
                started_at=datetime.now(timezone.utc),
                company_id=company_id,
            )
            self.db.add(user_quest)

        self.db.commit()
        self.db.refresh(user_quest)
        logger.info(f"Квест начат пользователем {user_id}: {quest.name}")
        return user_quest

    def update_quest_progress(
        self,
        user_id: int,
        quest_id: int,
        company_id: Optional[int] = None,
    ) -> Optional[UserQuest]:
        """Обновить прогресс выполнения квеста."""
        user_quest = (
            self.db.query(UserQuest)
            .filter(
                UserQuest.user_id == user_id,
                UserQuest.quest_id == quest_id,
                UserQuest.status == QuestStatus.IN_PROGRESS
            )
        )
        if company_id is not None:
            user_quest = user_quest.filter(UserQuest.company_id == company_id)
        user_quest = user_quest.first()

        if not user_quest:
            return None

        quest = user_quest.quest
        if not quest or quest.deleted_at:
            return None

        # Вычислить текущий прогресс на основе типа квеста
        new_progress = self._calculate_progress(user_id, quest, company_id)

        user_quest.progress = new_progress
        user_quest.updated_at = datetime.now(timezone.utc)

        # Проверить, выполнен ли квест
        if self._is_quest_completed(quest, new_progress):
            user_quest.status = QuestStatus.COMPLETED
            user_quest.completed_at = datetime.now(timezone.utc)
            user_quest.completion_count += 1

            # Выдать награды
            self._give_quest_rewards(user_id, quest, company_id)

            logger.info(f"Квест выполнен пользователем {user_id}: {quest.name}")

        self.db.commit()
        self.db.refresh(user_quest)
        return user_quest

    def _initialize_progress(self, quest: Quest) -> Dict:
        """Инициализировать прогресс квеста."""
        progress = {}
        requirements = quest.requirements

        if quest.quest_type == QuestType.VISIT_LOCATIONS:
            progress["visited_locations"] = []
            progress["required_count"] = requirements.get("count", 1)
        elif quest.quest_type == QuestType.COLLECT_ARTIFACTS:
            progress["collected_artifacts"] = {}
            progress["required_count"] = requirements.get("count", 1)
        elif quest.quest_type == QuestType.TRAVEL_DISTANCE:
            progress["distance_traveled"] = 0.0
            progress["required_distance"] = requirements.get("distance_km", 0)
        elif quest.quest_type == QuestType.COMPLETE_ACHIEVEMENTS:
            progress["completed_achievements"] = []
            progress["required_count"] = requirements.get("count", 1)

        return progress

    def _calculate_progress(
        self,
        user_id: int,
        quest: Quest,
        company_id: Optional[int] = None,
    ) -> Dict:
        """Вычислить текущий прогресс квеста."""
        progress = {}

        if quest.quest_type == QuestType.VISIT_LOCATIONS:
            geozone_ids = quest.requirements.get("geozone_ids", [])
            visited = (
                self.db.query(func.count(GeozoneVisit.id))
                .filter(
                    GeozoneVisit.user_id == user_id,
                    GeozoneVisit.geozone_id.in_(geozone_ids) if geozone_ids else True
                )
            )
            if company_id is not None:
                visited = visited.filter(GeozoneVisit.company_id == company_id)
            progress["visited_count"] = visited.scalar() or 0
            progress["required_count"] = quest.requirements.get("count", 1)

        elif quest.quest_type == QuestType.COLLECT_ARTIFACTS:
            artifact_ids = quest.requirements.get("artifact_ids", [])
            if artifact_ids:
                collected = (
                    self.db.query(func.sum(UserArtifact.quantity))
                    .filter(
                        UserArtifact.user_id == user_id,
                        UserArtifact.artifact_id.in_(artifact_ids)
                    )
                )
                if company_id is not None:
                    collected = collected.filter(UserArtifact.company_id == company_id)
                collected = collected.scalar() or 0
            else:
                collected = (
                    self.db.query(func.count(func.distinct(UserArtifact.artifact_id)))
                    .filter(UserArtifact.user_id == user_id)
                )
                if company_id is not None:
                    collected = collected.filter(UserArtifact.company_id == company_id)
                collected = collected.scalar() or 0
            progress["collected_count"] = collected
            progress["required_count"] = quest.requirements.get("count", 1)

        elif quest.quest_type == QuestType.TRAVEL_DISTANCE:
            # Вычислить пройденное расстояние
            from app.services.achievement import AchievementService
            achievement_service = AchievementService(self.db)
            # Используем логику из achievement service для подсчета расстояния
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

            total_distance = 0.0
            if len(points) >= 2:
                from geopy.distance import distance as geopy_distance
                for i in range(len(points) - 1):
                    dist = geopy_distance(
                        (points[i].latitude, points[i].longitude),
                        (points[i + 1].latitude, points[i + 1].longitude)
                    ).meters
                    total_distance += dist

            progress["distance_traveled"] = total_distance / 1000.0  # В километрах
            progress["required_distance"] = quest.requirements.get("distance_km", 0)

        elif quest.quest_type == QuestType.COMPLETE_ACHIEVEMENTS:
            achievement_ids = quest.requirements.get("achievement_ids", [])
            completed = (
                self.db.query(func.count(UserAchievement.id))
                .filter(
                    UserAchievement.user_id == user_id,
                    UserAchievement.achievement_id.in_(achievement_ids) if achievement_ids else True
                )
            )
            if company_id is not None:
                completed = completed.filter(UserAchievement.company_id == company_id)
            progress["completed_count"] = completed.scalar() or 0
            progress["required_count"] = quest.requirements.get("count", 1)

        return progress

    def _is_quest_completed(self, quest: Quest, progress: Dict) -> bool:
        """Проверить, выполнен ли квест."""
        if quest.quest_type == QuestType.VISIT_LOCATIONS:
            return progress.get("visited_count", 0) >= progress.get("required_count", 1)
        elif quest.quest_type == QuestType.COLLECT_ARTIFACTS:
            return progress.get("collected_count", 0) >= progress.get("required_count", 1)
        elif quest.quest_type == QuestType.TRAVEL_DISTANCE:
            return progress.get("distance_traveled", 0) >= progress.get("required_distance", 0)
        elif quest.quest_type == QuestType.COMPLETE_ACHIEVEMENTS:
            return progress.get("completed_count", 0) >= progress.get("required_count", 1)
        return False

    def _give_quest_rewards(
        self,
        user_id: int,
        quest: Quest,
        company_id: Optional[int] = None,
    ) -> None:
        """Выдать награды за выполнение квеста."""
        rewards = quest.rewards or {}
        marketplace_service = MarketplaceService(self.db)

        if "coins" in rewards:
            marketplace_service.add_currency(
                user_id,
                rewards["coins"],
                "coins",
                "quest",
                f"Награда за квест: {quest.name}",
                company_id
            )

        if "gems" in rewards:
            marketplace_service.add_currency(
                user_id,
                rewards["gems"],
                "gems",
                "quest",
                f"Награда за квест: {quest.name}",
                company_id
            )

        # Выдать артефакты/косметику если указаны в наградах
        if "artifacts" in rewards:
            for artifact_id, quantity in rewards["artifacts"].items():
                existing = (
                    self.db.query(UserArtifact)
                    .filter(
                        UserArtifact.user_id == user_id,
                        UserArtifact.artifact_id == int(artifact_id)
                    )
                )
                if company_id is not None:
                    existing = existing.filter(UserArtifact.company_id == company_id)
                existing = existing.first()
                
                if existing:
                    existing.quantity += quantity
                else:
                    user_artifact = UserArtifact(
                        user_id=user_id,
                        artifact_id=int(artifact_id),
                        quantity=quantity,
                        obtained_at=datetime.now(timezone.utc),
                        obtained_from="quest",
                        obtained_from_id=quest.id,
                        company_id=company_id,
                    )
                    self.db.add(user_artifact)

        if "cosmetics" in rewards:
            from app.models.cosmetic import UserCosmetic
            for cosmetic_id in rewards["cosmetics"]:
                user_cosmetic = UserCosmetic(
                    user_id=user_id,
                    cosmetic_id=int(cosmetic_id),
                    is_equipped=False,
                    obtained_at=datetime.now(timezone.utc),
                    obtained_from="quest",
                    obtained_from_id=quest.id,
                    company_id=company_id,
                )
                self.db.add(user_cosmetic)
