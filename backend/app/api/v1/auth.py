from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.constants import (
    AUTH_SCHEME_BEARER,
    DEFAULT_CURRENCY,
    DEFAULT_LANGUAGE,
    WWW_AUTHENTICATE_HEADER,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_token,
)
from app.core.timeutils import utcnow
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.user import (
    TelegramAuth, AuthResponse,
    RefreshRequest, LogoutRequest,
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
    В ответе возвращается пара токенов: access-токен (JWT) и
    refresh-токен для продления сессии без повторной авторизации.
    """

    user = db.query(User).filter(
        User.telegram_id == payload.telegram_id
    ).first()

    if not user:
        user = User(
            telegram_id=payload.telegram_id,
            username=payload.username or str(payload.telegram_id),
            settings={
                "currency": DEFAULT_CURRENCY,
                "language": DEFAULT_LANGUAGE,
            },
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if payload.username:
        user.username = payload.username
        db.commit()

    access_token = create_access_token({"sub": user.id})
    refresh_token = create_refresh_token(db, user.id)
    db.commit()

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
    )


@router.post(
    "/refresh",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
)
def refresh_session(
    payload: RefreshRequest,
    db: Session = Depends(get_db)
):
    """
    Обновление сессии по refresh-токену.

    Ротация выполняется атомарно одним условным UPDATE
    (``revoked = False AND expires_at > now``). При конкурентных
    запросах с одним и тем же токеном (PostgreSQL, READ COMMITTED)
    только один из них сможет перевести строку в ``revoked=True`` —
    остальные обновят 0 строк и получат 401. Это исключает TOCTOU-гонку,
    при которой два запроса могли бы выдать две пары токенов.

    Если токен уже был отозван (повторное использование / реплей),
    считаем семейство скомпрометированным и отзываем все
    refresh-токены пользователя, чтобы атакующий не смог продлить
    чужую сессию.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={WWW_AUTHENTICATE_HEADER: AUTH_SCHEME_BEARER},
    )

    now = utcnow()
    token_hash = hash_token(payload.refresh_token)

    result = db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked.is_(False),
            RefreshToken.expires_at > now,
        )
        .values(
            revoked=True,
            revoked_at=now,
            last_used_at=now,
        )
        .execution_options(synchronize_session=False)
    )

    if result.rowcount == 0:
        # Токен не прошёл атомарный отзыв: не существует, истёк либо уже
        # использован. Если запись существует и уже отозвана — это реплей:
        # отзываем всё семейство токенов пользователя.
        existing = db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()
        if existing is not None and existing.revoked:
            db.execute(
                update(RefreshToken)
                .where(RefreshToken.user_id == existing.user_id)
                .values(revoked=True, revoked_at=utcnow())
            )
            db.commit()
        else:
            db.rollback()
        raise credentials_exception

    record = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash
    ).first()

    user = db.query(User).filter(User.id == record.user_id).first()
    if user is None:
        db.rollback()
        raise credentials_exception

    # Ротация: старый токен уже отозван атомарно, выдаём новую пару
    new_refresh_token = create_refresh_token(db, user.id)
    record.replaced_by_token_hash = hash_token(new_refresh_token)

    access_token = create_access_token({"sub": user.id})
    db.commit()

    return AuthResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    payload: LogoutRequest,
    db: Session = Depends(get_db)
):
    """
    Выход из аккаунта: отзыв refresh-токена.

    После вызова токен больше нельзя использовать для обновления сессии.
    """

    record = db.query(RefreshToken).filter(
        RefreshToken.token_hash == hash_token(payload.refresh_token)
    ).first()

    if record is not None and not record.revoked:
        record.revoked = True
        record.revoked_at = utcnow()
        db.commit()
