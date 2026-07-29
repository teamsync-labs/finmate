from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import (
    create_access_token,
)
from app.models.user import User
from app.schemas.user import (
    TelegramAuth, TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/telegram",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def auth_telegram(payload: TelegramAuth, db: Session = Depends(get_db)):
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
            username=payload.username,
            first_name=payload.first_name,
            last_name=payload.last_name,
            settings={"currency": "RUB", "language": "ru"},
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    user.username = payload.username
    user.first_name = payload.first_name
    user.last_name = payload.last_name
    db.commit()

    access_token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=access_token)
