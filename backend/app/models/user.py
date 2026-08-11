from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, BigInteger, JSON
from sqlalchemy.orm import relationship, validates

from app.core.database import Base


class User(Base):
    """Модель пользователей."""

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )
    telegram_id = Column(
        BigInteger,
        unique=True,
        index=True,
        nullable=False
    )
    username = Column(
        String(255),
        nullable=True
    )
    settings = Column(
        JSON,
        default=dict,
        nullable=True
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    expenses = relationship(
        "Expenses",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @validates("telegram_id")
    def _set_default_username(self, key, value):
        if self.username is None:
            self.username = str(value)
        return value

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id})>"
