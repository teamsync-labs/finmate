from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import (
    create_access_token,
)
from app.models.user import User
from app.schemas.user import (
    TelegramAuth, AuthResponse,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/telegram",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
)
def auth_telegram(
    payload: TelegramAuth,
    db: Session = Depends(get_db)
):
    """
    Аутентификация через Telegram.
    Если пользователь с таким telegram_id не найден — создаётся новый.
    """
    user = db.query(User).filter(
        User.telegram_id == payload.telegram_id
    ).first()

    if not user:
        user = User(
            telegram_id=payload.telegram_id,
            username=payload.username or str(payload.telegram_id),
            settings={"currency": "RUB", "language": "ru"},
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if payload.username:
        user.username = payload.username
        db.commit()

    access_token = create_access_token({"sub": user.id})
    return AuthResponse(
        access_token=access_token,
        id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
    )
