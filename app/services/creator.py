"""Сервис платформы для создателей."""
import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.creator import Creator, CreatorPayment, QuestModeration, CreatorStatus, QuestModerationStatus
from app.models.event import Quest

settings = get_settings()
logger = logging.getLogger(__name__)


class CreatorService:
    """Сервис для работы с создателями контента."""

    def __init__(self, db: Session):
        """Инициализация сервиса."""
        self.db = db

    def apply_as_creator(
        self,
        user_id: int,
        display_name: Optional[str] = None,
        bio: Optional[str] = None,
        company_id: Optional[int] = None,
    ) -> Creator:
        """Подать заявку на статус создателя."""
        existing = (
            self.db.query(Creator)
            .filter(Creator.user_id == user_id)
            .first()
        )
        if existing:
            raise ValueError("Заявка уже подана")

        creator = Creator(
            user_id=user_id,
            status=CreatorStatus.PENDING,
            display_name=display_name,
            bio=bio,
            company_id=company_id,
        )
        self.db.add(creator)
        self.db.commit()
        self.db.refresh(creator)
        logger.info(f"Подана заявка на создателя пользователем {user_id}")
        return creator

    def approve_creator(
        self,
        creator_id: int,
        company_id: Optional[int] = None,
    ) -> Creator:
        """Одобрить заявку создателя."""
        creator = (
            self.db.query(Creator)
            .filter(Creator.id == creator_id)
        )
        if company_id is not None:
            creator = creator.filter(Creator.company_id == company_id)
        creator = creator.first()

        if not creator:
            raise ValueError("Создатель не найден")

        creator.status = CreatorStatus.APPROVED
        creator.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(creator)
        logger.info(f"Создатель одобрен: {creator_id}")
        return creator

    def create_premium_quest(
        self,
        creator_id: int,
        name: str,
        quest_type: str,
        requirements: dict,
        price: int,
        description: Optional[str] = None,
        rewards: Optional[dict] = None,
        company_id: Optional[int] = None,
    ) -> Quest:
        """Создать платный квест."""
        from app.models.event import QuestType
        
        creator = (
            self.db.query(Creator)
            .filter(
                Creator.id == creator_id,
                Creator.status == CreatorStatus.APPROVED
            )
        )
        if company_id is not None:
            creator = creator.filter(Creator.company_id == company_id)
        creator = creator.first()

        if not creator:
            raise ValueError("Создатель не найден или не одобрен")

        quest = Quest(
            name=name,
            description=description,
            quest_type=QuestType(quest_type),
            requirements=requirements,
            rewards=rewards or {},
            is_premium=True,
            price=price,
            creator_id=creator.user_id,
            company_id=company_id,
        )
        self.db.add(quest)
        self.db.flush()

        # Создать запись модерации
        moderation = QuestModeration(
            quest_id=quest.id,
            status=QuestModerationStatus.PENDING,
            company_id=company_id,
        )
        self.db.add(moderation)

        self.db.commit()
        self.db.refresh(quest)
        logger.info(f"Создан платный квест: {quest.id} создателем {creator_id}")
        return quest

    def process_quest_purchase(
        self,
        quest_id: int,
        buyer_id: int,
        company_id: Optional[int] = None,
    ) -> CreatorPayment:
        """Обработать покупку платного квеста."""
        quest = (
            self.db.query(Quest)
            .filter(
                Quest.id == quest_id,
                Quest.is_premium.is_(True),
                Quest.deleted_at.is_(None)
            )
        )
        if company_id is not None:
            quest = quest.filter(Quest.company_id == company_id)
        quest = quest.first()

        if not quest or not quest.creator_id:
            raise ValueError("Квест не найден или не является платным")

        creator = (
            self.db.query(Creator)
            .filter(Creator.user_id == quest.creator_id)
        )
        if company_id is not None:
            creator = creator.filter(Creator.company_id == company_id)
        creator = creator.first()

        if not creator:
            raise ValueError("Создатель не найден")

        # Вычислить платеж (например, 70% создателю, 30% платформе)
        platform_fee_percent = 0.3
        platform_fee = int(quest.price * platform_fee_percent)
        creator_earnings = quest.price - platform_fee

        payment = CreatorPayment(
            creator_id=creator.id,
            quest_id=quest_id,
            buyer_id=buyer_id,
            amount=quest.price,
            platform_fee=platform_fee,
            creator_earnings=creator_earnings,
            status="pending",
            company_id=company_id,
        )
        self.db.add(payment)

        # Обновить статистику создателя
        creator.total_quests_sold += 1
        creator.total_revenue += creator_earnings
        creator.updated_at = datetime.now(timezone.utc)

        # В реальной реализации здесь была бы обработка платежа
        payment.status = "completed"
        payment.paid_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(payment)
        logger.info(f"Обработан платеж за квест {quest_id}: создатель получит {creator_earnings}")
        return payment
