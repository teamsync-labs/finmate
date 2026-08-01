from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TelegramAuth(BaseModel):
    """Схема для входа/регистрации через Telegram."""
    telegram_id: int
    username: Optional[str] = None


class UserSettings(BaseModel):
    currency: Optional[str] = "RUB"
    language: Optional[str] = "ru"


class UserResponse(BaseModel):
    id: int
    telegram_id: int
    username: Optional[str] = None
    settings: Optional[UserSettings] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    """Ответ аутентификации: токен + полные данные."""
    access_token: str
    token_type: str = "bearer"
    telegram_id: int
    username: Optional[str] = None
