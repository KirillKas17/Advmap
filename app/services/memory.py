"""Сервис метавселенной воспоминаний."""
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.memory import Memory, MemoryTimeline

settings = get_settings()
logger = logging.getLogger(__name__)


class MemoryService:
    """Сервис для работы с воспоминаниями."""

    def __init__(self, db: Session):
        """Инициализация сервиса."""
        self.db = db

    def create_memory(
        self,
        user_id: int,
        title: str,
        memory_type: str,
        description: Optional[str] = None,
        location_data: Optional[Dict] = None,
        media_urls: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        emotion_score: Optional[float] = None,
        related_geozone_id: Optional[int] = None,
        related_achievement_id: Optional[int] = None,
        related_event_id: Optional[int] = None,
        is_public: bool = False,
        is_favorite: bool = False,
        company_id: Optional[int] = None,
    ) -> Memory:
        """Создать воспоминание."""
        memory = Memory(
            user_id=user_id,
            title=title,
            description=description,
            memory_type=memory_type,
            location_data=location_data or {},
            media_urls=media_urls or [],
            tags=tags or [],
            emotion_score=emotion_score,
            is_public=is_public,
            is_favorite=is_favorite,
            related_geozone_id=related_geozone_id,
            related_achievement_id=related_achievement_id,
            related_event_id=related_event_id,
            company_id=company_id,
        )
        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)

        # Создать запись в timeline для 3D визуализации
        timeline_entry = MemoryTimeline(
            memory_id=memory.id,
            user_id=user_id,
            position_x=location_data.get("x", 0.0) if location_data else 0.0,
            position_y=location_data.get("y", 0.0) if location_data else 0.0,
            position_z=location_data.get("z", 0.0) if location_data else 0.0,
            company_id=company_id,
        )
        self.db.add(timeline_entry)
        self.db.commit()
        self.db.refresh(memory)
        logger.info(f"Создано воспоминание: {memory.id} пользователем {user_id}")
        return memory

    def get_user_memories(
        self,
        user_id: int,
        memory_type: Optional[str] = None,
        is_favorite: Optional[bool] = None,
        company_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Memory]:
        """Получить воспоминания пользователя."""
        query = (
            self.db.query(Memory)
            .filter(
                Memory.user_id == user_id,
                Memory.deleted_at.is_(None)
            )
        )

        if memory_type:
            query = query.filter(Memory.memory_type == memory_type)
        if is_favorite is not None:
            query = query.filter(Memory.is_favorite == is_favorite)
        if company_id is not None:
            query = query.filter(Memory.company_id == company_id)

        return query.order_by(Memory.created_at.desc()).offset(offset).limit(limit).all()

    def get_memory_timeline(
        self,
        user_id: int,
        company_id: Optional[int] = None,
    ) -> List[Dict]:
        """Получить временную линию воспоминаний для 3D визуализации."""
        query = (
            self.db.query(MemoryTimeline)
            .join(Memory)
            .filter(
                MemoryTimeline.user_id == user_id,
                Memory.deleted_at.is_(None)
            )
        )
        if company_id is not None:
            query = query.filter(MemoryTimeline.company_id == company_id)

        timeline_entries = query.order_by(MemoryTimeline.created_at).all()

        result = []
        for entry in timeline_entries:
            memory = entry.memory
            if not memory:
                continue
            result.append({
                "memory_id": memory.id,
                "title": memory.title,
                "description": memory.description,
                "memory_type": memory.memory_type,
                "position": {
                    "x": entry.position_x,
                    "y": entry.position_y,
                    "z": entry.position_z,
                },
                "rotation": entry.rotation or {},
                "scale": entry.scale,
                "media_urls": memory.media_urls or [],
                "created_at": memory.created_at.isoformat(),
            })

        return result
