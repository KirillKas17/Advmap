"""Сервис работы с порталами и тотемами."""
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict

from geoalchemy2.shape import from_shape
from geopy.distance import distance
from shapely.geometry import Point
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.portal import Portal, PortalInteraction, PortalType, PortalStatus
from app.models.artifact import UserArtifact

settings = get_settings()
logger = logging.getLogger(__name__)


class PortalService:
    """Сервис для работы с порталами."""

    def __init__(self, db: Session):
        """Инициализация сервиса."""
        self.db = db

    def create_portal(
        self,
        name: str,
        portal_type: PortalType,
        latitude: float,
        longitude: float,
        description: Optional[str] = None,
        installed_by_user_id: Optional[int] = None,
        installed_artifact_id: Optional[int] = None,
        is_public: bool = True,
        company_id: Optional[int] = None,
    ) -> Portal:
        """Создать портал."""
        point = Point(longitude, latitude)
        portal = Portal(
            name=name,
            description=description,
            portal_type=portal_type,
            latitude=latitude,
            longitude=longitude,
            point=from_shape(point, srid=4326),
            installed_by_user_id=installed_by_user_id,
            installed_artifact_id=installed_artifact_id,
            installed_at=datetime.now(timezone.utc) if installed_by_user_id else None,
            is_public=is_public,
            company_id=company_id,
        )
        self.db.add(portal)
        self.db.commit()
        self.db.refresh(portal)
        logger.info(f"Создан портал: {portal.id} ({portal.name})")
        return portal

    def find_nearby_portals(
        self,
        latitude: float,
        longitude: float,
        radius_meters: float = 1000.0,
        company_id: Optional[int] = None,
        limit: int = 20,
    ) -> List[Portal]:
        """Найти порталы рядом с точкой."""
        point = Point(longitude, latitude)
        point_geom = from_shape(point, srid=4326)

        query = (
            self.db.query(Portal)
            .filter(
                func.ST_DWithin(
                    Portal.point,
                    point_geom,
                    radius_meters
                ),
                Portal.status == PortalStatus.ACTIVE,
                Portal.deleted_at.is_(None)
            )
        )

        if company_id is not None:
            query = query.filter(Portal.company_id == company_id)

        portals = query.limit(limit).all()

        # Сортировать по расстоянию
        portals_with_distance = []
        for portal in portals:
            dist = distance(
                (latitude, longitude),
                (portal.latitude, portal.longitude)
            ).meters
            portals_with_distance.append((portal, dist))

        portals_with_distance.sort(key=lambda x: x[1])
        return [p[0] for p in portals_with_distance]

    def interact_with_portal(
        self,
        portal_id: int,
        user_id: int,
        interaction_type: str,
        artifact_left_id: Optional[int] = None,
        artifact_taken_id: Optional[int] = None,
        company_id: Optional[int] = None,
    ) -> PortalInteraction:
        """Взаимодействовать с порталом."""
        portal = (
            self.db.query(Portal)
            .filter(
                Portal.id == portal_id,
                Portal.status == PortalStatus.ACTIVE,
                Portal.deleted_at.is_(None)
            )
        )
        if company_id is not None:
            portal = portal.filter(Portal.company_id == company_id)
        portal = portal.first()

        if not portal:
            raise ValueError("Портал не найден")

        reward_received = None

        if interaction_type == "leave_artifact" and artifact_left_id:
            # Оставить артефакт в портале
            user_artifact = (
                self.db.query(UserArtifact)
                .filter(
                    UserArtifact.user_id == user_id,
                    UserArtifact.artifact_id == artifact_left_id,
                    UserArtifact.quantity > 0
                )
            )
            if company_id is not None:
                user_artifact = user_artifact.filter(UserArtifact.company_id == company_id)
            user_artifact = user_artifact.first()

            if not user_artifact:
                raise ValueError("Артефакт не найден у пользователя")

            user_artifact.quantity -= 1
            if user_artifact.quantity <= 0:
                self.db.delete(user_artifact)

            portal.installed_artifact_id = artifact_left_id
            portal.installed_by_user_id = user_id
            portal.installed_at = datetime.now(timezone.utc)

        elif interaction_type == "take_artifact" and portal.installed_artifact_id:
            # Взять артефакт из портала
            existing = (
                self.db.query(UserArtifact)
                .filter(
                    UserArtifact.user_id == user_id,
                    UserArtifact.artifact_id == portal.installed_artifact_id
                )
                .first()
            )

            if existing:
                existing.quantity += 1
                user_artifact = existing
            else:
                user_artifact = UserArtifact(
                    user_id=user_id,
                    artifact_id=portal.installed_artifact_id,
                    quantity=1,
                    obtained_at=datetime.now(timezone.utc),
                    obtained_from="portal",
                    obtained_from_id=portal_id,
                    company_id=company_id,
                )
                self.db.add(user_artifact)

            portal.installed_artifact_id = None
            portal.installed_by_user_id = None
            portal.installed_at = None
            artifact_taken_id = portal.installed_artifact_id

        elif interaction_type == "activate":
            # Активировать портал (может дать награды)
            from app.services.marketplace import MarketplaceService
            marketplace_service = MarketplaceService(self.db)
            
            # Награда за активацию
            reward_coins = 10
            marketplace_service.add_currency(
                user_id,
                reward_coins,
                "coins",
                "portal_activation",
                f"Активация портала: {portal.name}",
                company_id
            )
            reward_received = {"coins": reward_coins}

        # Создать запись о взаимодействии
        interaction = PortalInteraction(
            portal_id=portal_id,
            user_id=user_id,
            interaction_type=interaction_type,
            artifact_left_id=artifact_left_id,
            artifact_taken_id=artifact_taken_id,
            reward_received=reward_received,
            company_id=company_id,
        )
        self.db.add(interaction)

        # Обновить статистику портала
        portal.interaction_count += 1
        portal.last_interaction_at = datetime.now(timezone.utc)
        portal.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(interaction)
        logger.info(f"Взаимодействие с порталом {portal_id} пользователем {user_id}: {interaction_type}")
        return interaction
