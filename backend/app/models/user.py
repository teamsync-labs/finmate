from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )
    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    settings = Column(JSON, default=dict, nullable=True)
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
        return f"<User(id={self.id}, email={self.email})>"
