from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String,
)

from app.core.constants import MAX_TOKEN_HASH_LENGTH
from app.core.database import Base
from app.core.timeutils import utcnow


class RefreshToken(Base):
    """Refresh-токен для продления сессии без повторной авторизации.

    В БД хранится только SHA-256 хеш токена (``token_hash``) — само
    значение токена клиент получает один раз при выдаче.
    При каждом обновлении сессии старый токен отзывается (ротация),
    поэтому один refresh-токен можно использовать только один раз.
    """

    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash = Column(
        String(MAX_TOKEN_HASH_LENGTH),
        unique=True,
        index=True,
        nullable=False,
    )
    expires_at = Column(DateTime, nullable=False, index=True)
    revoked = Column(Boolean, default=False, nullable=False)
    replaced_by_token_hash = Column(String(64), nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(
        DateTime,
        default=utcnow,
        nullable=False,
    )

    def __repr__(self):
        return (
            f"<RefreshToken(id={self.id}, user_id={self.user_id}, "
            f"revoked={self.revoked})>"
        )
