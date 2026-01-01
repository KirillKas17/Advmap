"""Модели B2B аналитики."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Float, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class DashboardType(str, enum.Enum):
    """Тип дашборда."""
    TOURISM = "tourism"
    RETAIL = "retail"
    MARKETING = "marketing"
    CUSTOM = "custom"


class SubscriptionStatus(str, enum.Enum):
    """Статус подписки."""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"


class BusinessClient(Base):
    """Модель бизнес-клиента (B2B)."""

    __tablename__ = "business_clients"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    contact_email = Column(String(255), nullable=False)
    contact_name = Column(String(255), nullable=True)
    subscription_status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False, index=True)
    subscription_tier = Column(String(50), nullable=False)  # basic, premium, enterprise
    api_key = Column(String(255), nullable=True, unique=True, index=True)
    max_api_calls_per_day = Column(Integer, default=1000, nullable=False)
    current_api_calls_today = Column(Integer, default=0, nullable=False)
    last_api_call_at = Column(DateTime, nullable=True)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    dashboards = relationship("AnalyticsDashboard", back_populates="client", cascade="all, delete-orphan")
    exports = relationship("AnalyticsExport", back_populates="client", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<BusinessClient(id={self.id}, company_name={self.company_name}, subscription_tier={self.subscription_tier})>"


class AnalyticsDashboard(Base):
    """Модель аналитического дашборда."""

    __tablename__ = "analytics_dashboards"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("business_clients.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    dashboard_type = Column(SQLEnum(DashboardType), nullable=False, index=True)
    config = Column(JSON, nullable=False)  # Конфигурация дашборда
    filters = Column(JSON, nullable=True)  # Фильтры данных
    is_active = Column(Boolean, default=True, nullable=False)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    client = relationship("BusinessClient", back_populates="dashboards")

    def __repr__(self) -> str:
        return f"<AnalyticsDashboard(id={self.id}, client_id={self.client_id}, name={self.name})>"


class AnalyticsExport(Base):
    """Модель экспорта аналитических данных."""

    __tablename__ = "analytics_exports"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("business_clients.id"), nullable=False, index=True)
    export_type = Column(String(50), nullable=False)  # csv, json, excel
    data_range_start = Column(DateTime, nullable=False)
    data_range_end = Column(DateTime, nullable=False)
    filters = Column(JSON, nullable=True)
    file_url = Column(String(500), nullable=True)
    status = Column(String(50), nullable=False, index=True)  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    client = relationship("BusinessClient", back_populates="exports")

    def __repr__(self) -> str:
        return f"<AnalyticsExport(id={self.id}, client_id={self.client_id}, export_type={self.export_type})>"
