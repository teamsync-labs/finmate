from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String,
    Float, Boolean, DateTime,
    ForeignKey, func
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)
    balance = Column(Float, nullable=False, default=0.0)
    currency = Column(String(3), default="RUB")
    is_archived = Column(Boolean, default=False)
    credit_limit = Column(Float, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="accounts")
    transactions = relationship(
        "Transaction",
        back_populates="account",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    VALID_TYPES = {"cash", "bank", "credit", "investment", "savings"}

    def __repr__(self):
        return (
            f"<Account(id={self.id}, name={self.name},"
            f" balance={self.balance})>"
        )
