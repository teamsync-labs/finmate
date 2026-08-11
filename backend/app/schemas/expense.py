from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

VALID_EXPENSE_TYPES = {
    "general", "food", "transport",
    "housing", "utilities", "entertainment",
    "health", "education", "shopping", "other",
}


class ExpenseCreate(BaseModel):
    """Данные для создания расхода."""

    expense_name: str
    amount: float = 0.0
    type: str = "general"
    currency: str = "RUB"

    @field_validator("expense_name")
    @classmethod
    def validate_expense_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Expense name cannot be empty")
        if len(v) > 100:
            raise ValueError("Expense name must be 100 characters or less")
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in VALID_EXPENSE_TYPES:
            raise ValueError(
                "Invalid expense type. Must be one of: "
                f"{', '.join(sorted(VALID_EXPENSE_TYPES))}"
            )
        return v

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Amount cannot be negative")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if len(v) != 3 or not v.isalpha():
            raise ValueError("Currency must be a 3-letter ISO code")
        return v.upper()


class ExpenseUpdate(BaseModel):
    """Данные для частичного обновления расхода."""

    expense_name: Optional[str] = None
    amount: Optional[float] = None
    type: Optional[str] = None
    currency: Optional[str] = None

    @field_validator("expense_name")
    @classmethod
    def validate_expense_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Expense name cannot be empty")
            if len(v) > 100:
                raise ValueError("Expense name must be 100 characters or less")
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_EXPENSE_TYPES:
            raise ValueError(
                "Invalid expense type. Must be one of: "
                f"{', '.join(sorted(VALID_EXPENSE_TYPES))}"
            )
        return v

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("Amount cannot be negative")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v) != 3 or not v.isalpha():
                raise ValueError("Currency must be a 3-letter ISO code")
            v = v.upper()
        return v


class ExpenseResponse(BaseModel):
    """Ответ с данными расхода."""

    id: int
    user_id: int
    expense_name: str
    amount: float
    type: Optional[str] = None
    currency: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
