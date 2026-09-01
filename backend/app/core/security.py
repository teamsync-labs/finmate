from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import (
    ACCESS_TOKEN_JTI_BYTES,
    AUTH_SCHEME_BEARER,
    REFRESH_TOKEN_BYTES,
    WWW_AUTHENTICATE_HEADER,
)
from app.core.database import get_db
from app.core.timeutils import utcnow
from app.models.refresh_token import RefreshToken
from app.models.user import User

security_scheme = HTTPBearer(auto_error=False)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": secrets.token_urlsafe(ACCESS_TOKEN_JTI_BYTES),
    })
    if "sub" in to_encode and not isinstance(to_encode["sub"], str):
        to_encode["sub"] = str(to_encode["sub"])
    return jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )


def hash_token(token: str) -> str:
    """SHA-256 хеш токена — только он хранится в БД."""

    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_refresh_token(db: Session, user_id: int) -> str:
    """
    Создаёт refresh-токен и сохраняет его хеш в БД.

    Возвращает raw-значение токена (отдаётся клиенту один раз);
    В БД хранится только SHA-256 хеш, поэтому даже при утечке БД
    сами токены не могут быть использованы.
    """

    raw = secrets.token_urlsafe(REFRESH_TOKEN_BYTES)
    record = RefreshToken(
        user_id=user_id,
        token_hash=hash_token(raw),
        expires_at=utcnow() + timedelta(
            minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
        ),
    )
    db.add(record)
    return raw


def get_current_user(
    credentials: Optional[
        HTTPAuthorizationCredentials
    ] = Depends(security_scheme),
    x_service_key: Optional[str] = Header(default=None),
    x_telegram_id: Optional[int] = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if x_service_key is not None:
        if (
            not settings.BOT_SERVICE_KEY
            or x_service_key != settings.BOT_SERVICE_KEY
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid service key",
            )
        if x_telegram_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="X-Telegram-Id header is required",
            )
        user = db.query(User).filter(
            User.telegram_id == x_telegram_id
        ).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not registered",
            )
        return user

    # Обычные клиенты: JWT Bearer (существующая логика).
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={WWW_AUTHENTICATE_HEADER: AUTH_SCHEME_BEARER},
    )
    if credentials is None:
        raise credentials_exception

    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": True},
        )
        user_id_str: Optional[str] = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except (InvalidTokenError, ValueError, TypeError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user
