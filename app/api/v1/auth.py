"""API endpoints для аутентификации."""
from datetime import timedelta
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()
logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    """Регистрация нового пользователя."""
    # Проверить, существует ли пользователь (с учетом soft delete)
    existing_user = (
        db.query(User)
        .filter(
            (User.email == user_data.email) | (User.username == user_data.username),
            User.deleted_at.is_(None)
        )
        .first()
    )
    if existing_user:
        logger.warning(f"Попытка регистрации с существующим email/username: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email или username уже существует",
        )

    # Создать пользователя
    try:
        hashed_password = get_password_hash(user_data.password)
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            company_id=user_data.company_id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Пользователь зарегистрирован: {user.id} ({user.email})")
        return user
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Ошибка при регистрации пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email или username уже существует",
        )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, credentials: UserLogin, db: Session = Depends(get_db)):
    """Вход пользователя."""
    user = (
        db.query(User)
        .filter(
            User.email == credentials.email,
            User.deleted_at.is_(None)
        )
        .first()
    )
    if not user or not verify_password(credentials.password, user.hashed_password):
        logger.warning(f"Неудачная попытка входа: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )

    if not user.is_active:
        logger.warning(f"Попытка входа в деактивированный аккаунт: {user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт деактивирован",
        )

    access_token = create_access_token(data={"sub": user.id})
    logger.info(f"Пользователь вошел в систему: {user.id} ({user.email})")
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Получить информацию о текущем пользователе."""
    return current_user
