from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, BigInteger, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
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
        nullable=False  # False по дуфолту но лучше явное чем нет.
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
    accounts = relationship(
        "Account",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    categories = relationship(
        "Category",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    transactions = relationship(
        "Transaction",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id})>"
