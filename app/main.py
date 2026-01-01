"""Главный файл приложения."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Travel Game Platform API",
    description="Универсальная платформа для геймификации путешествий с геолокацией",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключить роутеры
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/")
def root():
    """Корневой endpoint."""
    return {
        "message": "Travel Game Platform API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    """Проверка здоровья приложения."""
    return {"status": "ok"}
