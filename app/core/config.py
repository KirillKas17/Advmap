"""Конфигурация приложения."""
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # API
    api_v1_prefix: str = "/api/v1"

    # Geolocation
    geozone_buffer_meters: float = 50.0
    gps_spoofing_threshold_speed_ms: float = 100.0
    gps_spoofing_threshold_accuracy_meters: float = 1000.0

    # Background Location
    background_location_interval_seconds: int = 60
    offline_sync_batch_size: int = 100

    # Home/Work Detection
    home_work_min_visits: int = 5
    home_work_min_time_minutes: int = 30
    home_work_cluster_radius_meters: float = 200.0

    # CORS
    cors_origins: list[str] = ["*"]

    # Environment
    environment: str = "development"
    debug: bool = False


@lru_cache()
def get_settings() -> Settings:
    """Получить настройки приложения (кэшируется)."""
    return Settings()
