"""Схемы торговой площадки."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ListingCreate(BaseModel):
    """Схема создания объявления."""
    listing_type: str = Field(..., description="artifact или cosmetic")
    item_id: int
    quantity: int = Field(..., ge=1)
    price: int = Field(..., ge=1)
    description: Optional[str] = None
    expires_in_days: Optional[int] = Field(None, ge=1, le=30)


class MarketplaceListingResponse(BaseModel):
    """Схема ответа с объявлением."""
    id: int
    seller_id: int
    listing_type: str
    item_id: int
    quantity: int
    price: int
    status: str
    description: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PurchaseRequest(BaseModel):
    """Схема запроса на покупку."""
    pass  # Все данные берутся из URL


class TransactionResponse(BaseModel):
    """Схема ответа с транзакцией."""
    id: int
    listing_id: int
    buyer_id: int
    seller_id: int
    listing_type: str
    item_id: int
    quantity: int
    price: int
    status: str
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CurrencyResponse(BaseModel):
    """Схема ответа с валютой."""
    id: int
    user_id: int
    coins: int
    gems: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AddCurrencyRequest(BaseModel):
    """Схема добавления валюты."""
    amount: int = Field(..., ge=1)
    currency_type: str = Field(..., description="coins или gems")
    transaction_type: str = "reward"
    description: Optional[str] = None
