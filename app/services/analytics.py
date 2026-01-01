"""Сервис B2B аналитики."""
import logging
import csv
import json
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict
from io import StringIO

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.analytics import BusinessClient, AnalyticsDashboard, AnalyticsExport, SubscriptionStatus
from app.models.location import LocationPoint, LocationSession
from app.models.geozone import GeozoneVisit
from app.models.user import User

settings = get_settings()
logger = logging.getLogger(__name__)


class AnalyticsService:
    """Сервис для B2B аналитики."""

    def __init__(self, db: Session):
        """Инициализация сервиса."""
        self.db = db

    def create_business_client(
        self,
        company_name: str,
        contact_email: str,
        contact_name: Optional[str] = None,
        subscription_tier: str = "basic",
        max_api_calls_per_day: int = 1000,
        company_id: Optional[int] = None,
    ) -> BusinessClient:
        """Создать бизнес-клиента."""
        import secrets
        api_key = f"b2b_{secrets.token_urlsafe(32)}"

        client = BusinessClient(
            company_name=company_name,
            contact_email=contact_email,
            contact_name=contact_name,
            subscription_tier=subscription_tier,
            api_key=api_key,
            max_api_calls_per_day=max_api_calls_per_day,
            company_id=company_id,
        )
        self.db.add(client)
        self.db.commit()
        self.db.refresh(client)
        logger.info(f"Создан бизнес-клиент: {client.id} ({company_name})")
        return client

    def check_api_access(
        self,
        api_key: str,
        company_id: Optional[int] = None,
    ) -> Optional[BusinessClient]:
        """Проверить доступ по API ключу."""
        client = (
            self.db.query(BusinessClient)
            .filter(
                BusinessClient.api_key == api_key,
                BusinessClient.subscription_status == SubscriptionStatus.ACTIVE
            )
        )
        if company_id is not None:
            client = client.filter(BusinessClient.company_id == company_id)
        client = client.first()

        if not client:
            return None

        # Проверить лимит API вызовов
        today = datetime.now(timezone.utc).date()
        if client.last_api_call_at and client.last_api_call_at.date() == today:
            if client.current_api_calls_today >= client.max_api_calls_per_day:
                raise ValueError("Превышен лимит API вызовов на сегодня")
            client.current_api_calls_today += 1
        else:
            client.current_api_calls_today = 1

        client.last_api_call_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(client)
        return client

    def get_aggregated_statistics(
        self,
        start_date: datetime,
        end_date: datetime,
        filters: Optional[Dict] = None,
        company_id: Optional[int] = None,
    ) -> Dict:
        """Получить агрегированную статистику."""
        filters = filters or {}

        # Статистика по посещениям геозон
        visits_query = (
            self.db.query(
                func.count(GeozoneVisit.id).label("total_visits"),
                func.count(func.distinct(GeozoneVisit.user_id)).label("unique_users"),
            )
            .filter(
                GeozoneVisit.visit_started_at >= start_date,
                GeozoneVisit.visit_started_at <= end_date
            )
        )
        if company_id is not None:
            visits_query = visits_query.filter(GeozoneVisit.company_id == company_id)
        if "geozone_ids" in filters:
            visits_query = visits_query.filter(GeozoneVisit.geozone_id.in_(filters["geozone_ids"]))

        visits_stats = visits_query.first()

        # Статистика по геолокации
        location_query = (
            self.db.query(
                func.count(LocationPoint.id).label("total_points"),
                func.count(func.distinct(LocationSession.user_id)).label("active_users"),
            )
            .join(LocationSession)
            .filter(
                LocationPoint.timestamp >= start_date,
                LocationPoint.timestamp <= end_date,
                LocationPoint.is_spoofed.is_(False)
            )
        )
        if company_id is not None:
            location_query = location_query.filter(LocationPoint.company_id == company_id)

        location_stats = location_query.first()

        # Статистика по пользователям
        users_query = (
            self.db.query(func.count(User.id).label("total_users"))
            .filter(
                User.created_at >= start_date,
                User.created_at <= end_date,
                User.deleted_at.is_(None)
            )
        )
        if company_id is not None:
            users_query = users_query.filter(User.company_id == company_id)
        users_stats = users_query.first()

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "visits": {
                "total_visits": visits_stats.total_visits or 0,
                "unique_users": visits_stats.unique_users or 0,
            },
            "location": {
                "total_points": location_stats.total_points or 0,
                "active_users": location_stats.active_users or 0,
            },
            "users": {
                "total_users": users_stats.total_users or 0,
            },
        }

    def create_export(
        self,
        client_id: int,
        export_type: str,
        data_range_start: datetime,
        data_range_end: datetime,
        filters: Optional[Dict] = None,
        company_id: Optional[int] = None,
    ) -> AnalyticsExport:
        """Создать экспорт данных."""
        export = AnalyticsExport(
            client_id=client_id,
            export_type=export_type,
            data_range_start=data_range_start,
            data_range_end=data_range_end,
            filters=filters or {},
            status="pending",
            company_id=company_id,
        )
        self.db.add(export)
        self.db.commit()
        self.db.refresh(export)

        # Обработать экспорт асинхронно (в реальной реализации - через Celery)
        try:
            file_url = self._process_export(export)
            export.file_url = file_url
            export.status = "completed"
            export.completed_at = datetime.now(timezone.utc)
        except Exception as e:
            export.status = "failed"
            export.error_message = str(e)
            logger.error(f"Ошибка при экспорте данных: {e}")

        self.db.commit()
        self.db.refresh(export)
        logger.info(f"Создан экспорт данных: {export.id} для клиента {client_id}")
        return export

    def _process_export(self, export: AnalyticsExport) -> str:
        """Обработать экспорт данных (заглушка)."""
        # В реальной реализации здесь была бы генерация файла и загрузка в S3/облако
        # Для MVP возвращаем URL заглушку
        
        data = self.get_aggregated_statistics(
            export.data_range_start,
            export.data_range_end,
            export.filters,
            export.company_id
        )

        if export.export_type == "csv":
            # Генерация CSV
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=["metric", "value"])
            writer.writeheader()
            writer.writerow({"metric": "total_visits", "value": data["visits"]["total_visits"]})
            writer.writerow({"metric": "unique_users", "value": data["visits"]["unique_users"]})
            # В реальной реализации файл был бы сохранен и возвращен URL
            return f"https://storage.example.com/exports/{export.id}.csv"
        elif export.export_type == "json":
            # В реальной реализации JSON файл был бы сохранен
            return f"https://storage.example.com/exports/{export.id}.json"
        else:
            raise ValueError(f"Неподдерживаемый тип экспорта: {export.export_type}")
