from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String,
    Float, DateTime,
    ForeignKey, func
)
from sqlalchemy.orm import relationship

from app.core.constants import (
    DEFAULT_CURRENCY,
    DEFAULT_EXPENSE_TYPE,
    MAX_CURRENCY_CODE_LENGTH,
    MAX_EXPENSE_NAME_LENGTH,
    MAX_EXPENSE_TYPE_LENGTH,
)
from app.core.database import Base


class Expenses(Base):
    """Модель расходов."""

    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    expense_name = Column(String(MAX_EXPENSE_NAME_LENGTH), nullable=False)
    amount = Column(Float, nullable=False, default=0.0)
    type = Column(
        String(MAX_EXPENSE_TYPE_LENGTH),
        nullable=True,
        default=DEFAULT_EXPENSE_TYPE,
    )
    currency = Column(String(MAX_CURRENCY_CODE_LENGTH), default=DEFAULT_CURRENCY)

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

    user = relationship("User", back_populates="expenses")
