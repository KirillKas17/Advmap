"""Схемы верификации."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class VerificationRequestCreate(BaseModel):
    """Схема создания запроса на верификацию."""
    requested_status: str
    evidence_data: Optional[str] = None


class VerificationRequestResponse(BaseModel):
    """Схема ответа с запросом на верификацию."""
    id: int
    user_id: int
    status: str
    requested_status: str
    evidence_data: Optional[str] = None
    rejection_reason: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserStatusResponse(BaseModel):
    """Схема ответа со статусом пользователя."""
    status: str
