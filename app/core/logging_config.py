"""Конфигурация логирования."""
import logging
import sys
from typing import Optional

from app.core.config import get_settings

settings = get_settings()


def setup_logging(log_level: Optional[str] = None) -> None:
    """Настроить логирование для приложения."""
    if log_level is None:
        log_level = "DEBUG" if settings.debug else "INFO"

    # Формат логов
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Для продакшена можно использовать JSON формат
    if settings.environment == "production":
        log_format = '{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'

    # Настройка root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Настройка логгеров для библиотек
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Получить логгер с указанным именем."""
    return logging.getLogger(name)
