"""Сервис верификации пользователей."""
import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.verification import VerificationRequest, UserStatusHistory, VerificationStatus, UserStatus
from app.models.user import User
from app.models.geozone import GeozoneVisit
from app.models.location import LocationPoint, LocationSession
from app.models.achievement import UserAchievement

settings = get_settings()
logger = logging.getLogger(__name__)


class VerificationService:
    """Сервис для верификации пользователей."""

    def __init__(self, db: Session):
        """Инициализация сервиса."""
        self.db = db

    def request_verification(
        self,
        user_id: int,
        requested_status: UserStatus,
        evidence_data: Optional[str] = None,
        company_id: Optional[int] = None,
    ) -> VerificationRequest:
        """Запросить верификацию."""
        # Проверить, не подана ли уже заявка
        existing = (
            self.db.query(VerificationRequest)
            .filter(
                VerificationRequest.user_id == user_id,
                VerificationRequest.status == VerificationStatus.PENDING
            )
            .first()
        )
        if existing:
            raise ValueError("У вас уже есть активная заявка на верификацию")

        request = VerificationRequest(
            user_id=user_id,
            requested_status=requested_status,
            evidence_data=evidence_data,
            status=VerificationStatus.PENDING,
            company_id=company_id,
        )
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        logger.info(f"Запрошена верификация пользователем {user_id}: {requested_status}")
        return request

    def review_verification_request(
        self,
        request_id: int,
        reviewer_id: int,
        approved: bool,
        rejection_reason: Optional[str] = None,
        company_id: Optional[int] = None,
    ) -> VerificationRequest:
        """Рассмотреть заявку на верификацию."""
        request = (
            self.db.query(VerificationRequest)
            .filter(VerificationRequest.id == request_id)
        )
        if company_id is not None:
            request = request.filter(VerificationRequest.company_id == company_id)
        request = request.first()

        if not request:
            raise ValueError("Заявка не найдена")

        if request.status != VerificationStatus.PENDING:
            raise ValueError("Заявка уже рассмотрена")

        user = self.db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise ValueError("Пользователь не найден")

        if approved:
            # Проверить критерии для статуса
            if not self._check_status_criteria(user.id, request.requested_status, company_id):
                raise ValueError("Пользователь не соответствует критериям для этого статуса")

            request.status = VerificationStatus.APPROVED
            request.reviewed_by = reviewer_id
            request.reviewed_at = datetime.now(timezone.utc)

            # Обновить статус пользователя
            old_status = self._get_user_status(user.id)
            self._set_user_status(
                user.id,
                request.requested_status,
                f"Верификация одобрена",
                reviewer_id,
                company_id
            )

            logger.info(f"Верификация одобрена для пользователя {user.id}: {request.requested_status}")
        else:
            request.status = VerificationStatus.REJECTED
            request.rejection_reason = rejection_reason
            request.reviewed_by = reviewer_id
            request.reviewed_at = datetime.now(timezone.utc)
            logger.info(f"Верификация отклонена для пользователя {user.id}")

        self.db.commit()
        self.db.refresh(request)
        return request

    def _check_status_criteria(
        self,
        user_id: int,
        status: UserStatus,
        company_id: Optional[int] = None,
    ) -> bool:
        """Проверить критерии для статуса."""
        if status == UserStatus.VERIFIED_TRAVELER:
            # Критерии для проверенного путешественника
            # Минимум 50 посещений геозон
            visits_count = (
                self.db.query(func.count(GeozoneVisit.id))
                .filter(GeozoneVisit.user_id == user_id)
            )
            if company_id is not None:
                visits_count = visits_count.filter(GeozoneVisit.company_id == company_id)
            visits_count = visits_count.scalar() or 0

            # Минимум 10 достижений
            achievements_count = (
                self.db.query(func.count(UserAchievement.id))
                .filter(UserAchievement.user_id == user_id)
            )
            if company_id is not None:
                achievements_count = achievements_count.filter(UserAchievement.company_id == company_id)
            achievements_count = achievements_count.scalar() or 0

            return visits_count >= 50 and achievements_count >= 10

        elif status == UserStatus.MASTER_EXPLORER:
            # Критерии для мастера-исследователя
            visits_count = (
                self.db.query(func.count(GeozoneVisit.id))
                .filter(GeozoneVisit.user_id == user_id)
            )
            if company_id is not None:
                visits_count = visits_count.filter(GeozoneVisit.company_id == company_id)
            visits_count = visits_count.scalar() or 0

            achievements_count = (
                self.db.query(func.count(UserAchievement.id))
                .filter(UserAchievement.user_id == user_id)
            )
            if company_id is not None:
                achievements_count = achievements_count.filter(UserAchievement.company_id == company_id)
            achievements_count = achievements_count.scalar() or 0

            return visits_count >= 200 and achievements_count >= 50

        elif status == UserStatus.LEGEND:
            # Критерии для легенды
            visits_count = (
                self.db.query(func.count(GeozoneVisit.id))
                .filter(GeozoneVisit.user_id == user_id)
            )
            if company_id is not None:
                visits_count = visits_count.filter(GeozoneVisit.company_id == company_id)
            visits_count = visits_count.scalar() or 0

            achievements_count = (
                self.db.query(func.count(UserAchievement.id))
                .filter(UserAchievement.user_id == user_id)
            )
            if company_id is not None:
                achievements_count = achievements_count.filter(UserAchievement.company_id == company_id)
            achievements_count = achievements_count.scalar() or 0

            return visits_count >= 1000 and achievements_count >= 100

        return False

    def _get_user_status(self, user_id: int) -> Optional[UserStatus]:
        """Получить текущий статус пользователя."""
        # Определить статус на основе статистики
        visits_count = (
            self.db.query(func.count(GeozoneVisit.id))
            .filter(GeozoneVisit.user_id == user_id)
            .scalar() or 0
        )

        achievements_count = (
            self.db.query(func.count(UserAchievement.id))
            .filter(UserAchievement.user_id == user_id)
            .scalar() or 0
        )

        if visits_count >= 1000 and achievements_count >= 100:
            return UserStatus.LEGEND
        elif visits_count >= 200 and achievements_count >= 50:
            return UserStatus.MASTER_EXPLORER
        elif visits_count >= 50 and achievements_count >= 10:
            return UserStatus.VERIFIED_TRAVELER
        elif visits_count >= 20:
            return UserStatus.EXPLORER
        elif visits_count >= 5:
            return UserStatus.TRAVELER
        else:
            return UserStatus.NEWBIE

    def _set_user_status(
        self,
        user_id: int,
        new_status: UserStatus,
        reason: str,
        changed_by: Optional[int] = None,
        company_id: Optional[int] = None,
    ) -> None:
        """Установить статус пользователя."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return

        old_status = self._get_user_status(user_id)

        # Сохранить историю изменения статуса
        history = UserStatusHistory(
            user_id=user_id,
            old_status=old_status,
            new_status=new_status,
            reason=reason,
            changed_by=changed_by,
            company_id=company_id,
        )
        self.db.add(history)

        # Обновить флаг верификации если статус требует этого
        if new_status in [UserStatus.VERIFIED_TRAVELER, UserStatus.MASTER_EXPLORER, UserStatus.LEGEND]:
            user.is_verified = True

        self.db.commit()
        logger.info(f"Статус пользователя {user_id} изменен: {old_status} -> {new_status}")
