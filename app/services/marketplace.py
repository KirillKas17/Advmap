"""Сервис торговой площадки."""
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.marketplace import (
    MarketplaceListing, Transaction, UserCurrency, CurrencyTransaction,
    ListingStatus, ListingType, TransactionStatus
)
from app.models.artifact import UserArtifact, Artifact
from app.models.cosmetic import UserCosmetic, Cosmetic

settings = get_settings()
logger = logging.getLogger(__name__)


class MarketplaceService:
    """Сервис для работы с торговой площадкой."""

    def __init__(self, db: Session):
        """Инициализация сервиса."""
        self.db = db

    def create_listing(
        self,
        seller_id: int,
        listing_type: ListingType,
        item_id: int,
        quantity: int,
        price: int,
        description: Optional[str] = None,
        expires_in_days: Optional[int] = None,
        company_id: Optional[int] = None,
    ) -> MarketplaceListing:
        """Создать объявление на торговой площадке."""
        # Проверить наличие предмета у продавца и что он tradeable
        if listing_type == ListingType.ARTIFACT:
            artifact = (
                self.db.query(Artifact)
                .filter(
                    Artifact.id == item_id,
                    Artifact.is_tradeable.is_(True),
                    Artifact.deleted_at.is_(None)
                )
            )
            if company_id is not None:
                artifact = artifact.filter(Artifact.company_id == company_id)
            artifact = artifact.first()

            if not artifact:
                raise ValueError("Артефакт не найден или не может быть продан")

            user_item = (
                self.db.query(UserArtifact)
                .filter(
                    UserArtifact.user_id == seller_id,
                    UserArtifact.artifact_id == item_id
                )
            )
            if company_id is not None:
                user_item = user_item.filter(UserArtifact.company_id == company_id)
            user_item = user_item.first()

            if not user_item or user_item.quantity < quantity:
                raise ValueError("Недостаточно артефактов для продажи")

        elif listing_type == ListingType.COSMETIC:
            cosmetic = (
                self.db.query(Cosmetic)
                .filter(
                    Cosmetic.id == item_id,
                    Cosmetic.is_tradeable.is_(True),
                    Cosmetic.deleted_at.is_(None)
                )
            )
            if company_id is not None:
                cosmetic = cosmetic.filter(Cosmetic.company_id == company_id)
            cosmetic = cosmetic.first()

            if not cosmetic:
                raise ValueError("Косметика не найдена или не может быть продана")

            user_item = (
                self.db.query(UserCosmetic)
                .filter(
                    UserCosmetic.user_id == seller_id,
                    UserCosmetic.cosmetic_id == item_id,
                    UserCosmetic.is_equipped.is_(False)
                )
            )
            if company_id is not None:
                user_item = user_item.filter(UserCosmetic.company_id == company_id)
            user_item = user_item.first()

            if not user_item:
                raise ValueError("Косметика не найдена или надета")

        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        listing = MarketplaceListing(
            seller_id=seller_id,
            listing_type=listing_type,
            item_id=item_id,
            quantity=quantity,
            price=price,
            description=description,
            expires_at=expires_at,
            company_id=company_id,
        )
        self.db.add(listing)
        self.db.commit()
        self.db.refresh(listing)
        logger.info(f"Создано объявление: {listing.id} продавцом {seller_id}")
        return listing

    def purchase_listing(
        self,
        listing_id: int,
        buyer_id: int,
        company_id: Optional[int] = None,
    ) -> Transaction:
        """Купить предмет по объявлению."""
        listing = (
            self.db.query(MarketplaceListing)
            .filter(
                MarketplaceListing.id == listing_id,
                MarketplaceListing.status == ListingStatus.ACTIVE
            )
        )
        if company_id is not None:
            listing = listing.filter(MarketplaceListing.company_id == company_id)
        listing = listing.first()

        if not listing:
            raise ValueError("Объявление не найдено или неактивно")

        if listing.seller_id == buyer_id:
            raise ValueError("Нельзя купить свой собственный предмет")

        if listing.expires_at and listing.expires_at < datetime.now(timezone.utc):
            listing.status = ListingStatus.EXPIRED
            self.db.commit()
            raise ValueError("Объявление истекло")

        # Проверить баланс покупателя
        buyer_currency = self._get_or_create_currency(buyer_id, company_id)
        if buyer_currency.coins < listing.price:
            raise ValueError("Недостаточно средств")

        # Создать транзакцию
        transaction = Transaction(
            listing_id=listing_id,
            buyer_id=buyer_id,
            seller_id=listing.seller_id,
            listing_type=listing.listing_type,
            item_id=listing.item_id,
            quantity=listing.quantity,
            price=listing.price,
            status=TransactionStatus.PENDING,
            company_id=company_id,
        )
        self.db.add(transaction)

        # Передать предмет покупателю
        if listing.listing_type == ListingType.ARTIFACT:
            buyer_item = (
                self.db.query(UserArtifact)
                .filter(
                    UserArtifact.user_id == buyer_id,
                    UserArtifact.artifact_id == listing.item_id
                )
            )
            if company_id is not None:
                buyer_item = buyer_item.filter(UserArtifact.company_id == company_id)
            buyer_item = buyer_item.first()

            if buyer_item:
                buyer_item.quantity += listing.quantity
                buyer_item.updated_at = datetime.now(timezone.utc)
            else:
                buyer_item = UserArtifact(
                    user_id=buyer_id,
                    artifact_id=listing.item_id,
                    quantity=listing.quantity,
                    obtained_at=datetime.now(timezone.utc),
                    obtained_from="trade",
                    obtained_from_id=transaction.id,
                    company_id=company_id,
                )
                self.db.add(buyer_item)

            # Удалить у продавца
            seller_item = (
                self.db.query(UserArtifact)
                .filter(
                    UserArtifact.user_id == listing.seller_id,
                    UserArtifact.artifact_id == listing.item_id
                )
            )
            if company_id is not None:
                seller_item = seller_item.filter(UserArtifact.company_id == company_id)
            seller_item = seller_item.first()

            if seller_item:
                seller_item.quantity -= listing.quantity
                if seller_item.quantity <= 0:
                    self.db.delete(seller_item)

        elif listing.listing_type == ListingType.COSMETIC:
            buyer_cosmetic = UserCosmetic(
                user_id=buyer_id,
                cosmetic_id=listing.item_id,
                is_equipped=False,
                obtained_at=datetime.now(timezone.utc),
                obtained_from="trade",
                obtained_from_id=transaction.id,
                company_id=company_id,
            )
            self.db.add(buyer_cosmetic)

            # Удалить у продавца
            seller_cosmetic = (
                self.db.query(UserCosmetic)
                .filter(
                    UserCosmetic.user_id == listing.seller_id,
                    UserCosmetic.cosmetic_id == listing.item_id
                )
            )
            if company_id is not None:
                seller_cosmetic = seller_cosmetic.filter(UserCosmetic.company_id == company_id)
            seller_cosmetic = seller_cosmetic.first()

            if seller_cosmetic:
                self.db.delete(seller_cosmetic)

        # Перевести деньги
        buyer_currency.coins -= listing.price
        self._add_currency_transaction(
            buyer_currency.id,
            -listing.price,
            "coins",
            "purchase",
            transaction.id,
            company_id
        )

        seller_currency = self._get_or_create_currency(listing.seller_id, company_id)
        seller_currency.coins += listing.price
        self._add_currency_transaction(
            seller_currency.id,
            listing.price,
            "coins",
            "sale",
            transaction.id,
            company_id
        )

        # Обновить статусы
        listing.status = ListingStatus.SOLD
        transaction.status = TransactionStatus.COMPLETED
        transaction.completed_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(transaction)
        logger.info(f"Транзакция завершена: {transaction.id}, покупатель {buyer_id}, продавец {listing.seller_id}")
        return transaction

    def get_listings(
        self,
        listing_type: Optional[ListingType] = None,
        seller_id: Optional[int] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        company_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[MarketplaceListing]:
        """Получить список объявлений."""
        query = (
            self.db.query(MarketplaceListing)
            .filter(MarketplaceListing.status == ListingStatus.ACTIVE)
        )

        if listing_type:
            query = query.filter(MarketplaceListing.listing_type == listing_type)
        if seller_id:
            query = query.filter(MarketplaceListing.seller_id == seller_id)
        if min_price:
            query = query.filter(MarketplaceListing.price >= min_price)
        if max_price:
            query = query.filter(MarketplaceListing.price <= max_price)
        if company_id is not None:
            query = query.filter(MarketplaceListing.company_id == company_id)

        # Фильтр истекших объявлений
        query = query.filter(
            (MarketplaceListing.expires_at.is_(None)) |
            (MarketplaceListing.expires_at > datetime.now(timezone.utc))
        )

        return query.order_by(MarketplaceListing.created_at.desc()).offset(offset).limit(limit).all()

    def _get_or_create_currency(
        self,
        user_id: int,
        company_id: Optional[int] = None,
    ) -> UserCurrency:
        """Получить или создать валюту пользователя."""
        currency = (
            self.db.query(UserCurrency)
            .filter(UserCurrency.user_id == user_id)
        )
        if company_id is not None:
            currency = currency.filter(UserCurrency.company_id == company_id)
        currency = currency.first()

        if not currency:
            currency = UserCurrency(
                user_id=user_id,
                coins=0,
                gems=0,
                company_id=company_id,
            )
            self.db.add(currency)
            self.db.commit()
            self.db.refresh(currency)

        return currency

    def _add_currency_transaction(
        self,
        user_currency_id: int,
        amount: int,
        currency_type: str,
        transaction_type: str,
        related_id: Optional[int] = None,
        description: Optional[str] = None,
        company_id: Optional[int] = None,
    ) -> CurrencyTransaction:
        """Добавить транзакцию валюты."""
        transaction = CurrencyTransaction(
            user_currency_id=user_currency_id,
            amount=amount,
            currency_type=currency_type,
            transaction_type=transaction_type,
            related_id=related_id,
            description=description,
            company_id=company_id,
        )
        self.db.add(transaction)
        return transaction

    def add_currency(
        self,
        user_id: int,
        amount: int,
        currency_type: str = "coins",
        transaction_type: str = "reward",
        description: Optional[str] = None,
        company_id: Optional[int] = None,
    ) -> UserCurrency:
        """Добавить валюту пользователю."""
        currency = self._get_or_create_currency(user_id, company_id)

        if currency_type == "coins":
            currency.coins += amount
        elif currency_type == "gems":
            currency.gems += amount

        trans = self._add_currency_transaction(
            currency.id,
            amount,
            currency_type,
            transaction_type,
            description=description,
            company_id=company_id,
        )
        trans.description = description

        currency.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(currency)
        logger.info(f"Добавлена валюта пользователю {user_id}: {amount} {currency_type}")
        return currency
