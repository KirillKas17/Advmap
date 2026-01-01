"""Роутер для всех API v1 endpoints."""
from fastapi import APIRouter

from app.api.v1 import (
    achievement, auth, geozone, home_work, location,
    artifact, cosmetic, marketplace, quest, guild,
    verification, creator, ai, portal, memory, analytics
)

api_router = APIRouter()

# Основные endpoints
api_router.include_router(auth.router)
api_router.include_router(location.router)
api_router.include_router(geozone.router)
api_router.include_router(achievement.router)
api_router.include_router(home_work.router)

# Версия 2.0: Вовлечение
api_router.include_router(artifact.router)
api_router.include_router(cosmetic.router)
api_router.include_router(marketplace.router)
api_router.include_router(quest.router)

# Версия 3.0: Социальный слой
api_router.include_router(guild.router)
api_router.include_router(verification.router)
api_router.include_router(creator.router)

# Версия 4.0: AI и продвинутые функции
api_router.include_router(ai.router)
api_router.include_router(portal.router)
api_router.include_router(memory.router)

# Версия 5.0: B2B
api_router.include_router(analytics.router)
