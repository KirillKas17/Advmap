"""Сервис работы с артефактами."""
import logging
import random
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.artifact import Artifact, UserArtifact, ArtifactCraftingRequirement
from app.models.geozone import GeozoneVisit
from app.models.location import LocationPoint, LocationSession

settings = get_settings()
logger = logging.getLogger(__name__)


class ArtifactService:
    """Сервис для работы с артефактами."""

    def __init__(self, db: Session):
        """Инициализация сервиса."""
        self.db = db

    def create_artifact(
        self,
        name: str,
        description: Optional[str],
        rarity: str,
        artifact_type: str,
        geozone_id: Optional[int] = None,
        region_name: Optional[str] = None,
        drop_chance: float = 1.0,
        is_tradeable: bool = True,
        is_craftable: bool = False,
        base_value: int = 0,
        icon_url: Optional[str] = None,
        image_url: Optional[str] = None,
        company_id: Optional[int] = None,
    ) -> Artifact:
        """Создать новый артефакт."""
        artifact = Artifact(
            name=name,
            description=description,
            rarity=rarity,
            artifact_type=artifact_type,
            geozone_id=geozone_id,
            region_name=region_name,
            drop_chance=drop_chance,
            is_tradeable=is_tradeable,
            is_craftable=is_craftable,
            base_value=base_value,
            icon_url=icon_url,
            image_url=image_url,
            company_id=company_id,
        )
        self.db.add(artifact)
        self.db.commit()
        self.db.refresh(artifact)
        logger.info(f"Создан артефакт: {artifact.id} ({artifact.name})")
        return artifact

    def get_artifact_by_id(
        self, artifact_id: int, company_id: Optional[int] = None
    ) -> Optional[Artifact]:
        """Получить артефакт по ID."""
        query = (
            self.db.query(Artifact)
            .filter(
                Artifact.id == artifact_id,
                Artifact.is_active.is_(True),
                Artifact.deleted_at.is_(None)
            )
        )
        if company_id is not None:
            query = query.filter(Artifact.company_id == company_id)
        return query.first()

    def get_user_artifacts(
        self,
        user_id: int,
        artifact_id: Optional[int] = None,
        rarity: Optional[str] = None,
        company_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[UserArtifact]:
        """Получить артефакты пользователя."""
        query = (
            self.db.query(UserArtifact)
            .join(Artifact)
            .filter(
                UserArtifact.user_id == user_id,
                Artifact.deleted_at.is_(None)
            )
        )

        if artifact_id:
            query = query.filter(UserArtifact.artifact_id == artifact_id)
        if rarity:
            query = query.filter(Artifact.rarity == rarity)
        if company_id is not None:
            query = query.filter(UserArtifact.company_id == company_id)

        return query.order_by(UserArtifact.obtained_at.desc()).offset(offset).limit(limit).all()

    def try_drop_artifact_from_geozone(
        self,
        user_id: int,
        geozone_id: int,
        company_id: Optional[int] = None,
    ) -> Optional[UserArtifact]:
        """
        Попытаться выдать артефакт при посещении геозоны.
        
        Returns:
            UserArtifact если артефакт выпал, None если не выпал
        """
        # Получить артефакты для этой геозоны
        artifacts_query = (
            self.db.query(Artifact)
            .filter(
                Artifact.geozone_id == geozone_id,
                Artifact.is_active.is_(True),
                Artifact.deleted_at.is_(None)
            )
        )
        if company_id is not None:
            artifacts_query = artifacts_query.filter(Artifact.company_id == company_id)

        artifacts = artifacts_query.all()

        if not artifacts:
            return None

        # Выбрать артефакт на основе вероятности выпадения
        for artifact in artifacts:
            if random.random() <= artifact.drop_chance:
                # Проверить, есть ли уже у пользователя
                existing = (
                    self.db.query(UserArtifact)
                    .filter(
                        UserArtifact.user_id == user_id,
                        UserArtifact.artifact_id == artifact.id
                    )
                    .first()
                )

                if existing:
                    existing.quantity += 1
                    existing.updated_at = datetime.now(timezone.utc)
                    user_artifact = existing
                else:
                    user_artifact = UserArtifact(
                        user_id=user_id,
                        artifact_id=artifact.id,
                        quantity=1,
                        obtained_at=datetime.now(timezone.utc),
                        obtained_from="geozone_visit",
                        obtained_from_id=geozone_id,
                        company_id=company_id,
                    )
                    self.db.add(user_artifact)

                self.db.commit()
                self.db.refresh(user_artifact)
                logger.info(f"Артефакт выпал пользователю {user_id}: {artifact.name}")
                return user_artifact

        return None

    def craft_artifact(
        self,
        user_id: int,
        artifact_id: int,
        company_id: Optional[int] = None,
    ) -> Optional[UserArtifact]:
        """Создать артефакт через крафт."""
        artifact = self.get_artifact_by_id(artifact_id, company_id)
        if not artifact or not artifact.is_craftable:
            raise ValueError("Артефакт не может быть создан через крафт")

        # Проверить требования для крафта
        requirements = (
            self.db.query(ArtifactCraftingRequirement)
            .filter(ArtifactCraftingRequirement.artifact_id == artifact_id)
        )
        if company_id is not None:
            requirements = requirements.filter(ArtifactCraftingRequirement.company_id == company_id)
        requirements = requirements.all()

        # Проверить наличие всех требуемых артефактов
        user_artifacts = {
            ua.artifact_id: ua.quantity
            for ua in self.get_user_artifacts(user_id, company_id=company_id, limit=10000)
        }

        for req in requirements:
            if user_artifacts.get(req.required_artifact_id, 0) < req.required_quantity:
                raise ValueError(f"Недостаточно артефактов для крафта: требуется {req.required_quantity}")

        # Удалить использованные артефакты
        for req in requirements:
            user_artifact = (
                self.db.query(UserArtifact)
                .filter(
                    UserArtifact.user_id == user_id,
                    UserArtifact.artifact_id == req.required_artifact_id
                )
                .first()
            )
            if user_artifact:
                user_artifact.quantity -= req.required_quantity
                if user_artifact.quantity <= 0:
                    self.db.delete(user_artifact)

        # Создать новый артефакт
        existing = (
            self.db.query(UserArtifact)
            .filter(
                UserArtifact.user_id == user_id,
                UserArtifact.artifact_id == artifact_id
            )
            .first()
        )

        if existing:
            existing.quantity += 1
            existing.updated_at = datetime.now(timezone.utc)
            user_artifact = existing
        else:
            user_artifact = UserArtifact(
                user_id=user_id,
                artifact_id=artifact_id,
                quantity=1,
                obtained_at=datetime.now(timezone.utc),
                obtained_from="craft",
                company_id=company_id,
            )
            self.db.add(user_artifact)

        self.db.commit()
        self.db.refresh(user_artifact)
        logger.info(f"Артефакт создан через крафт пользователем {user_id}: {artifact.name}")
        return user_artifact

    def get_artifact_statistics(
        self,
        user_id: int,
        company_id: Optional[int] = None,
    ) -> dict:
        """Получить статистику по артефактам пользователя."""
        query = (
            self.db.query(
                func.count(UserArtifact.id).label("total_artifacts"),
                func.sum(UserArtifact.quantity).label("total_quantity")
            )
            .join(Artifact)
            .filter(
                UserArtifact.user_id == user_id,
                Artifact.deleted_at.is_(None)
            )
        )
        if company_id is not None:
            query = query.filter(UserArtifact.company_id == company_id)

        stats = query.first()

        # Статистика по редкости
        rarity_stats = (
            self.db.query(
                Artifact.rarity,
                func.sum(UserArtifact.quantity).label("count")
            )
            .join(UserArtifact)
            .filter(
                UserArtifact.user_id == user_id,
                Artifact.deleted_at.is_(None)
            )
        )
        if company_id is not None:
            rarity_stats = rarity_stats.filter(UserArtifact.company_id == company_id)
        rarity_stats = rarity_stats.group_by(Artifact.rarity).all()

        return {
            "total_artifacts": stats.total_artifacts or 0,
            "total_quantity": stats.total_quantity or 0,
            "by_rarity": {rarity: count for rarity, count in rarity_stats},
        }
