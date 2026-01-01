"""Модели торговой площадки."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class ListingStatus(str, enum.Enum):
    """Статус объявления на торговой площадке."""
    ACTIVE = "active"
    SOLD = "sold"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ListingType(str, enum.Enum):
    """Тип предмета в объявлении."""
    ARTIFACT = "artifact"
    COSMETIC = "cosmetic"


class TransactionStatus(str, enum.Enum):
    """Статус транзакции."""
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class MarketplaceListing(Base):
    """Модель объявления на торговой площадке."""

    __tablename__ = "marketplace_listings"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    listing_type = Column(SQLEnum(ListingType), nullable=False, index=True)
    item_id = Column(Integer, nullable=False, index=True)  # ID артефакта или косметики
    quantity = Column(Integer, default=1, nullable=False)
    price = Column(Integer, nullable=False)  # Цена во внутренней валюте
    status = Column(SQLEnum(ListingStatus), default=ListingStatus.ACTIVE, nullable=False, index=True)
    description = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    seller = relationship("User", foreign_keys=[seller_id])
    transactions = relationship("Transaction", back_populates="listing")

    def __repr__(self) -> str:
        return f"<MarketplaceListing(id={self.id}, seller_id={self.seller_id}, listing_type={self.listing_type}, price={self.price})>"


class Transaction(Base):
    """Модель транзакции на торговой площадке."""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("marketplace_listings.id"), nullable=False, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    listing_type = Column(SQLEnum(ListingType), nullable=False)
    item_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    listing = relationship("MarketplaceListing", back_populates="transactions")
    buyer = relationship("User", foreign_keys=[buyer_id])
    seller_rel = relationship("User", foreign_keys=[seller_id])

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, buyer_id={self.buyer_id}, seller_id={self.seller_id}, price={self.price})>"


class UserCurrency(Base):
    """Модель внутренней валюты пользователя."""

    __tablename__ = "user_currency"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    coins = Column(Integer, default=0, nullable=False)  # Основная валюта
    gems = Column(Integer, default=0, nullable=False)  # Премиум валюта
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="currency")
    transactions = relationship("CurrencyTransaction", back_populates="user_currency")

    def __repr__(self) -> str:
        return f"<UserCurrency(id={self.id}, user_id={self.user_id}, coins={self.coins}, gems={self.gems})>"


class CurrencyTransaction(Base):
    """Модель транзакции валюты."""

    __tablename__ = "currency_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_currency_id = Column(Integer, ForeignKey("user_currency.id"), nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False, index=True)  # purchase, sale, reward, craft, quest
    amount = Column(Integer, nullable=False)  # Может быть отрицательным
    currency_type = Column(String(20), nullable=False)  # coins, gems
    description = Column(Text, nullable=True)
    related_id = Column(Integer, nullable=True)  # ID связанной сущности (transaction, quest и т.д.)
    company_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user_currency = relationship("UserCurrency", back_populates="transactions")

    def __repr__(self) -> str:
        return f"<CurrencyTransaction(id={self.id}, user_currency_id={self.user_currency_id}, amount={self.amount})>"
