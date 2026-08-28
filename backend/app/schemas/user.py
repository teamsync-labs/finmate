from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TelegramAuth(BaseModel):
    """Данные для входа/регистрации через Telegram."""

    telegram_id: int
    username: Optional[str] = None


class UserSettings(BaseModel):
    """Настройки пользователя: валюта и язык."""

    currency: Optional[str] = "RUB"
    language: Optional[str] = "ru"


class UserResponse(BaseModel):
    """Ответ с данными пользователя."""

    id: int
    telegram_id: int
    username: Optional[str] = None
    settings: Optional[UserSettings] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    """Ответ аутентификации: токены + полные данные."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    id: int
    telegram_id: int
    username: Optional[str] = None


class RefreshRequest(BaseModel):
    """Запрос на обновление пары токенов по refresh-токену."""

    refresh_token: str


class LogoutRequest(BaseModel):
    """Запрос на выход: отзыв refresh-токена."""

    refresh_token: str
