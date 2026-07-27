from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class TransactionCreate(BaseModel):
    account_id: int
    category_id: Optional[int] = None
    type: str  # income, expense
    amount: float
    description: Optional[str] = None
    notes: Optional[str] = None
    date: date
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ("income", "expense"):
            raise ValueError("Type must be 'income' or 'expense'")
        return v

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v

    @field_validator("recurrence_rule")
    @classmethod
    def validate_recurrence_rule(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            simple_keywords = {"daily", "weekly", "monthly", "yearly"}
            if v not in simple_keywords:
                if not v.startswith("FREQ=") or "=" not in v:
                    raise ValueError(
                        "Recurrence rule must be a valid RRULE "
                        "(e.g. FREQ=MONTHLY;BYMONTHDAY=1) "
                        "or one of: daily, weekly, monthly, yearly"
                    )
        return v


class TransactionUpdate(BaseModel):
    category_id: Optional[int] = None
    type: Optional[str] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    date: Optional[date] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("income", "expense"):
            raise ValueError("Type must be 'income' or 'expense'")
        return v

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("Amount must be positive")
        return v


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    account_id: int
    category_id: Optional[int] = None
    type: str
    amount: float
    currency: str
    description: Optional[str] = None
    notes: Optional[str] = None
    date: date
    is_recurring: bool
    recurrence_rule: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
