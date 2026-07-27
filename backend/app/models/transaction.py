# noqa: F401

from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String,
    Float, Boolean, DateTime,
    ForeignKey, Date, func
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.account import Account


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    account_id = Column(
        Integer,
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    category_id = Column(
        Integer, ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    type = Column(String(10), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="RUB")
    description = Column(String(500), nullable=True)
    notes = Column(String(500), nullable=True)
    date = Column(Date, nullable=False, index=True)
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(String(255), nullable=True)
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

    user = relationship("User", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")
    category = relationship("Category", foreign_keys=[category_id])

    VALID_TYPES = {"income", "expense"}

    def __repr__(self):
        return (
            f"<Transaction(id={self.id}, amount={self.amount},"
            f" type={self.type})>"
        )

    def apply_to_balance(
            self,
            account: "Account",
            sign: int = 1
    ) -> None:
        """Применить транзакцию к балансу счёта.

        Args:
            account: Счёт для обновления.
            sign: 1 — применить, -1 — отменить.
        """
        if self.type == "income":
            account.balance += self.amount * sign
        else:
            account.balance -= self.amount * sign
