"""Схемы пользователя."""
import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """Схема создания пользователя."""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100, description="Имя пользователя от 3 до 100 символов")
    password: str = Field(..., min_length=8, description="Пароль минимум 8 символов")
    full_name: Optional[str] = Field(None, max_length=255)
    company_id: Optional[int] = None

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Валидация сложности пароля."""
        if len(v) < 8:
            raise ValueError('Пароль должен содержать минимум 8 символов')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Пароль должен содержать хотя бы одну букву')
        if not re.search(r'[0-9]', v):
            raise ValueError('Пароль должен содержать хотя бы одну цифру')
        return v

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Валидация имени пользователя."""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Имя пользователя может содержать только буквы, цифры, дефисы и подчеркивания')
        return v


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
