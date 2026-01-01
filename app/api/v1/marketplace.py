"""API endpoints для торговой площадки."""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.marketplace import ListingType
from app.services.marketplace import MarketplaceService
from app.schemas.marketplace import (
    MarketplaceListingResponse,
    TransactionResponse,
    ListingCreate,
    PurchaseRequest,
    CurrencyResponse,
    AddCurrencyRequest,
)

router = APIRouter(prefix="/marketplace", tags=["marketplace"])
logger = logging.getLogger(__name__)


@router.post("/listings", response_model=MarketplaceListingResponse, status_code=status.HTTP_201_CREATED)
def create_listing(
    listing_data: ListingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Создать объявление на торговой площадке."""
    service = MarketplaceService(db)
    try:
        listing = service.create_listing(
            seller_id=current_user.id,
            listing_type=ListingType(listing_data.listing_type),
            item_id=listing_data.item_id,
            quantity=listing_data.quantity,
            price=listing_data.price,
            description=listing_data.description,
            expires_in_days=listing_data.expires_in_days,
            company_id=current_user.company_id,
        )
        return listing
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Ошибка БД при создании объявления: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании объявления",
        )


@router.get("/listings", response_model=List[MarketplaceListingResponse])
def get_listings(
    listing_type: Optional[str] = None,
    seller_id: Optional[int] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить список объявлений."""
    service = MarketplaceService(db)
    listings = service.get_listings(
        listing_type=ListingType(listing_type) if listing_type else None,
        seller_id=seller_id,
        min_price=min_price,
        max_price=max_price,
        company_id=current_user.company_id,
        limit=limit,
        offset=offset,
    )
    return listings


@router.post("/listings/{listing_id}/purchase", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def purchase_listing(
    listing_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Купить предмет по объявлению."""
    service = MarketplaceService(db)
    try:
        transaction = service.purchase_listing(
            listing_id=listing_id,
            buyer_id=current_user.id,
            company_id=current_user.company_id,
        )
        return transaction
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Ошибка БД при покупке: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при покупке",
        )


@router.get("/currency", response_model=CurrencyResponse)
def get_currency(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить баланс валюты."""
    service = MarketplaceService(db)
    currency = service._get_or_create_currency(
        user_id=current_user.id,
        company_id=current_user.company_id,
    )
    return currency


@router.post("/currency/add", response_model=CurrencyResponse)
def add_currency(
    request: AddCurrencyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Добавить валюту пользователю (для тестирования/наград)."""
    service = MarketplaceService(db)
    currency = service.add_currency(
        user_id=current_user.id,
        amount=request.amount,
        currency_type=request.currency_type,
        transaction_type=request.transaction_type,
        description=request.description,
        company_id=current_user.company_id,
    )
    return currency
