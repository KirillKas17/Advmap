"""Схемы пользователя."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Схема создания пользователя."""

    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None
    company_id: Optional[int] = None


class UserLogin(BaseModel):
    """Схема входа пользователя."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Схема ответа с данными пользователя."""

    id: int
    email: str
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    is_verified: bool
    company_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Схема ответа с токеном."""

    access_token: str
    token_type: str = "bearer"
