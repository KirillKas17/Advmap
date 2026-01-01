"""Роутер для всех API v1 endpoints."""
from fastapi import APIRouter

from app.api.v1 import achievement, auth, geozone, home_work, location

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(location.router)
api_router.include_router(geozone.router)
api_router.include_router(achievement.router)
api_router.include_router(home_work.router)
