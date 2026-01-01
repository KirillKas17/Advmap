"""Сервис работы с гильдиями."""
import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.guild import Guild, GuildMember, GuildAchievement, GuildRole, GuildStatus
from app.models.achievement import Achievement, UserAchievement

settings = get_settings()
logger = logging.getLogger(__name__)


class GuildService:
    """Сервис для работы с гильдиями."""

    def __init__(self, db: Session):
        """Инициализация сервиса."""
        self.db = db

    def create_guild(
        self,
        name: str,
        leader_id: int,
        description: Optional[str] = None,
        tag: Optional[str] = None,
        banner_url: Optional[str] = None,
        max_members: int = 50,
        company_id: Optional[int] = None,
    ) -> Guild:
        """Создать гильдию."""
        # Проверить уникальность имени и тега
        existing = (
            self.db.query(Guild)
            .filter(
                (Guild.name == name) | (Guild.tag == tag),
                Guild.deleted_at.is_(None)
            )
            .first()
        )
        if existing:
            raise ValueError("Гильдия с таким именем или тегом уже существует")

        guild = Guild(
            name=name,
            description=description,
            tag=tag,
            banner_url=banner_url,
            max_members=max_members,
            company_id=company_id,
        )
        self.db.add(guild)
        self.db.flush()

        # Добавить создателя как лидера
        leader = GuildMember(
            guild_id=guild.id,
            user_id=leader_id,
            role=GuildRole.LEADER,
            joined_at=datetime.now(timezone.utc),
            company_id=company_id,
        )
        self.db.add(leader)

        self.db.commit()
        self.db.refresh(guild)
        logger.info(f"Создана гильдия: {guild.id} ({guild.name}) лидером {leader_id}")
        return guild

    def join_guild(
        self,
        guild_id: int,
        user_id: int,
        company_id: Optional[int] = None,
    ) -> GuildMember:
        """Присоединиться к гильдии."""
        guild = (
            self.db.query(Guild)
            .filter(
                Guild.id == guild_id,
                Guild.status == GuildStatus.ACTIVE,
                Guild.deleted_at.is_(None)
            )
        )
        if company_id is not None:
            guild = guild.filter(Guild.company_id == company_id)
        guild = guild.first()

        if not guild:
            raise ValueError("Гильдия не найдена")

        # Проверить количество участников
        member_count = (
            self.db.query(func.count(GuildMember.id))
            .filter(GuildMember.guild_id == guild_id)
            .scalar() or 0
        )
        if member_count >= guild.max_members:
            raise ValueError("Гильдия переполнена")

        # Проверить, не состоит ли уже в гильдии
        existing = (
            self.db.query(GuildMember)
            .filter(
                GuildMember.user_id == user_id,
                GuildMember.guild_id == guild_id
            )
            .first()
        )
        if existing:
            raise ValueError("Вы уже состоите в этой гильдии")

        member = GuildMember(
            guild_id=guild_id,
            user_id=user_id,
            role=GuildRole.MEMBER,
            joined_at=datetime.now(timezone.utc),
            company_id=company_id,
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        logger.info(f"Пользователь {user_id} присоединился к гильдии {guild_id}")
        return member

    def update_member_role(
        self,
        guild_id: int,
        member_id: int,
        new_role: GuildRole,
        changed_by_user_id: int,
        company_id: Optional[int] = None,
    ) -> GuildMember:
        """Изменить роль участника гильдии."""
        # Проверить права
        changer = (
            self.db.query(GuildMember)
            .filter(
                GuildMember.guild_id == guild_id,
                GuildMember.user_id == changed_by_user_id,
                GuildMember.role.in_([GuildRole.LEADER, GuildRole.OFFICER])
            )
            .first()
        )
        if not changer:
            raise ValueError("Недостаточно прав для изменения роли")

        member = (
            self.db.query(GuildMember)
            .filter(
                GuildMember.id == member_id,
                GuildMember.guild_id == guild_id
            )
        )
        if company_id is not None:
            member = member.filter(GuildMember.company_id == company_id)
        member = member.first()

        if not member:
            raise ValueError("Участник не найден")

        member.role = new_role
        member.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(member)
        logger.info(f"Роль участника {member_id} изменена на {new_role}")
        return member

    def add_guild_achievement(
        self,
        guild_id: int,
        achievement_id: int,
        unlocked_by_user_id: int,
        company_id: Optional[int] = None,
    ) -> GuildAchievement:
        """Добавить достижение гильдии."""
        guild_achievement = GuildAchievement(
            guild_id=guild_id,
            achievement_id=achievement_id,
            unlocked_at=datetime.now(timezone.utc),
            unlocked_by_user_id=unlocked_by_user_id,
            company_id=company_id,
        )
        self.db.add(guild_achievement)

        # Обновить статистику гильдии
        guild = self.db.query(Guild).filter(Guild.id == guild_id).first()
        if guild:
            guild.total_achievements += 1
            guild.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(guild_achievement)
        logger.info(f"Достижение {achievement_id} добавлено гильдии {guild_id}")
        return guild_achievement
