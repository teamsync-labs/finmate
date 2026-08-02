from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String,
    Float, DateTime,
    ForeignKey, func
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Expenses(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    expense_name = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False, default=0.0)
    type = Column(String(20), nullable=True, default='general')
    currency = Column(String(3), default="RUB")

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
