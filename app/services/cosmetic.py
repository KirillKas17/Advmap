"""Сервис работы с косметикой."""
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.cosmetic import Cosmetic, UserCosmetic, CosmeticCraftingRequirement, UserAvatar
from app.models.user import User
from app.models.artifact import UserArtifact

settings = get_settings()
logger = logging.getLogger(__name__)


class CosmeticService:
    """Сервис для работы с косметикой."""

    def __init__(self, db: Session):
        """Инициализация сервиса."""
        self.db = db

    def create_cosmetic(
        self,
        name: str,
        cosmetic_type: str,
        rarity: str,
        slot: Optional[str] = None,
        description: Optional[str] = None,
        icon_url: Optional[str] = None,
        preview_url: Optional[str] = None,
        customization_data: Optional[Dict] = None,
        is_tradeable: bool = True,
        is_craftable: bool = False,
        base_value: int = 0,
        company_id: Optional[int] = None,
    ) -> Cosmetic:
        """Создать новый косметический предмет."""
        cosmetic = Cosmetic(
            name=name,
            description=description,
            cosmetic_type=cosmetic_type,
            rarity=rarity,
            slot=slot,
            icon_url=icon_url,
            preview_url=preview_url,
            customization_data=customization_data,
            is_tradeable=is_tradeable,
            is_craftable=is_craftable,
            base_value=base_value,
            company_id=company_id,
        )
        self.db.add(cosmetic)
        self.db.commit()
        self.db.refresh(cosmetic)
        logger.info(f"Создана косметика: {cosmetic.id} ({cosmetic.name})")
        return cosmetic

    def get_user_cosmetics(
        self,
        user_id: int,
        cosmetic_type: Optional[str] = None,
        is_equipped: Optional[bool] = None,
        company_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[UserCosmetic]:
        """Получить косметику пользователя."""
        query = (
            self.db.query(UserCosmetic)
            .join(Cosmetic)
            .filter(
                UserCosmetic.user_id == user_id,
                Cosmetic.deleted_at.is_(None)
            )
        )

        if cosmetic_type:
            query = query.filter(Cosmetic.cosmetic_type == cosmetic_type)
        if is_equipped is not None:
            query = query.filter(UserCosmetic.is_equipped == is_equipped)
        if company_id is not None:
            query = query.filter(UserCosmetic.company_id == company_id)

        return query.order_by(UserCosmetic.obtained_at.desc()).offset(offset).limit(limit).all()

    def equip_cosmetic(
        self,
        user_id: int,
        cosmetic_id: int,
        company_id: Optional[int] = None,
    ) -> UserCosmetic:
        """Надеть косметику."""
        user_cosmetic = (
            self.db.query(UserCosmetic)
            .join(Cosmetic)
            .filter(
                UserCosmetic.user_id == user_id,
                UserCosmetic.cosmetic_id == cosmetic_id,
                Cosmetic.deleted_at.is_(None)
            )
        )
        if company_id is not None:
            user_cosmetic = user_cosmetic.filter(UserCosmetic.company_id == company_id)
        user_cosmetic = user_cosmetic.first()

        if not user_cosmetic:
            raise ValueError("Косметика не найдена у пользователя")

        # Снять другую косметику того же слота
        cosmetic = user_cosmetic.cosmetic
        if cosmetic.slot:
            other_equipped = (
                self.db.query(UserCosmetic)
                .join(Cosmetic)
                .filter(
                    UserCosmetic.user_id == user_id,
                    UserCosmetic.is_equipped.is_(True),
                    Cosmetic.slot == cosmetic.slot,
                    Cosmetic.deleted_at.is_(None)
                )
            )
            if company_id is not None:
                other_equipped = other_equipped.filter(UserCosmetic.company_id == company_id)
            for uc in other_equipped.all():
                uc.is_equipped = False

        user_cosmetic.is_equipped = True
        user_cosmetic.updated_at = datetime.now(timezone.utc)

        # Обновить конфигурацию аватара
        self._update_avatar_config(user_id, company_id)

        self.db.commit()
        self.db.refresh(user_cosmetic)
        logger.info(f"Косметика надета пользователем {user_id}: {cosmetic.name}")
        return user_cosmetic

    def unequip_cosmetic(
        self,
        user_id: int,
        cosmetic_id: int,
        company_id: Optional[int] = None,
    ) -> UserCosmetic:
        """Снять косметику."""
        user_cosmetic = (
            self.db.query(UserCosmetic)
            .filter(
                UserCosmetic.user_id == user_id,
                UserCosmetic.cosmetic_id == cosmetic_id
            )
        )
        if company_id is not None:
            user_cosmetic = user_cosmetic.filter(UserCosmetic.company_id == company_id)
        user_cosmetic = user_cosmetic.first()

        if not user_cosmetic:
            raise ValueError("Косметика не найдена у пользователя")

        user_cosmetic.is_equipped = False
        user_cosmetic.updated_at = datetime.now(timezone.utc)

        # Обновить конфигурацию аватара
        self._update_avatar_config(user_id, company_id)

        self.db.commit()
        self.db.refresh(user_cosmetic)
        return user_cosmetic

    def _update_avatar_config(
        self,
        user_id: int,
        company_id: Optional[int] = None,
    ) -> None:
        """Обновить конфигурацию аватара пользователя."""
        equipped_cosmetics = (
            self.db.query(UserCosmetic)
            .join(Cosmetic)
            .filter(
                UserCosmetic.user_id == user_id,
                UserCosmetic.is_equipped.is_(True),
                Cosmetic.deleted_at.is_(None)
            )
        )
        if company_id is not None:
            equipped_cosmetics = equipped_cosmetics.filter(UserCosmetic.company_id == company_id)
        equipped_cosmetics = equipped_cosmetics.all()

        avatar_config = {
            "cosmetics": [
                {
                    "cosmetic_id": uc.cosmetic_id,
                    "slot": uc.cosmetic.slot,
                    "type": uc.cosmetic.cosmetic_type,
                }
                for uc in equipped_cosmetics
            ]
        }

        user_avatar = (
            self.db.query(UserAvatar)
            .filter(UserAvatar.user_id == user_id)
        )
        if company_id is not None:
            user_avatar = user_avatar.filter(UserAvatar.company_id == company_id)
        user_avatar = user_avatar.first()

        if user_avatar:
            user_avatar.avatar_config = avatar_config
            user_avatar.updated_at = datetime.now(timezone.utc)
        else:
            user_avatar = UserAvatar(
                user_id=user_id,
                avatar_config=avatar_config,
                company_id=company_id,
            )
            self.db.add(user_avatar)

    def get_avatar_config(
        self,
        user_id: int,
        company_id: Optional[int] = None,
    ) -> Optional[Dict]:
        """Получить конфигурацию аватара пользователя."""
        query = self.db.query(UserAvatar).filter(UserAvatar.user_id == user_id)
        if company_id is not None:
            query = query.filter(UserAvatar.company_id == company_id)
        user_avatar = query.first()

        if user_avatar:
            return user_avatar.avatar_config
        return None

    def craft_cosmetic(
        self,
        user_id: int,
        cosmetic_id: int,
        company_id: Optional[int] = None,
    ) -> UserCosmetic:
        """Создать косметику через крафт."""
        cosmetic = (
            self.db.query(Cosmetic)
            .filter(
                Cosmetic.id == cosmetic_id,
                Cosmetic.is_active.is_(True),
                Cosmetic.deleted_at.is_(None)
            )
        )
        if company_id is not None:
            cosmetic = cosmetic.filter(Cosmetic.company_id == company_id)
        cosmetic = cosmetic.first()

        if not cosmetic or not cosmetic.is_craftable:
            raise ValueError("Косметика не может быть создана через крафт")

        # Проверить требования для крафта
        requirements = (
            self.db.query(CosmeticCraftingRequirement)
            .filter(CosmeticCraftingRequirement.cosmetic_id == cosmetic_id)
        )
        if company_id is not None:
            requirements = requirements.filter(CosmeticCraftingRequirement.company_id == company_id)
        requirements = requirements.all()

        # Проверить наличие всех требуемых предметов
        for req in requirements:
            if req.required_artifact_id:
                user_artifact = (
                    self.db.query(UserArtifact)
                    .filter(
                        UserArtifact.user_id == user_id,
                        UserArtifact.artifact_id == req.required_artifact_id
                    )
                )
                if company_id is not None:
                    user_artifact = user_artifact.filter(UserArtifact.company_id == company_id)
                user_artifact = user_artifact.first()
                
                if not user_artifact or user_artifact.quantity < req.required_quantity:
                    raise ValueError(f"Недостаточно артефактов для крафта")
            elif req.required_cosmetic_id:
                user_cosmetics = self.get_user_cosmetics(
                    user_id, company_id=company_id, limit=10000
                )
                cosmetic_count = sum(
                    1 for uc in user_cosmetics if uc.cosmetic_id == req.required_cosmetic_id
                )
                if cosmetic_count < req.required_quantity:
                    raise ValueError(f"Недостаточно косметики для крафта")

        # Удалить использованные предметы
        for req in requirements:
            if req.required_artifact_id:
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

        # Создать новую косметику
        user_cosmetic = UserCosmetic(
            user_id=user_id,
            cosmetic_id=cosmetic_id,
            is_equipped=False,
            obtained_at=datetime.now(timezone.utc),
            obtained_from="craft",
            company_id=company_id,
        )
        self.db.add(user_cosmetic)
        self.db.commit()
        self.db.refresh(user_cosmetic)
        logger.info(f"Косметика создана через крафт пользователем {user_id}: {cosmetic.name}")
        return user_cosmetic
