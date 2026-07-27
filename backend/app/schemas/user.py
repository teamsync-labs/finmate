from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator

from app.core.config import settings


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < settings.PASSWORD_MIN_LENGTH:
            raise ValueError(
                "Password must be at least "
                f"{settings.PASSWORD_MIN_LENGTH} characters"
            )
        if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r"[A-Z]", v):
            raise ValueError(
                "Password must contain at least one uppercase letter"
            )
        if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r"[a-z]", v):
            raise ValueError(
                "Password must contain at least one lowercase letter"
            )
        if settings.PASSWORD_REQUIRE_DIGIT and not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserSettings(BaseModel):
    currency: Optional[str] = "RUB"
    language: Optional[str] = "ru"


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    settings: Optional[UserSettings] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
