from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

VALID_ACCOUNT_TYPES = {
    "cash", "bank",
    "credit", "investment",
    "savings"
}


class AccountCreate(BaseModel):
    name: str
    type: str
    balance: float = 0.0
    currency: str = "RUB"
    credit_limit: Optional[float] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in VALID_ACCOUNT_TYPES:
            raise ValueError(
                "Invalid account type. Must be one of: "
                f"{', '.join(sorted(VALID_ACCOUNT_TYPES))}"
            )
        return v

    @field_validator("balance")
    @classmethod
    def validate_balance(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Initial balance cannot be negative")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if len(v) != 3 or not v.isalpha():
            raise ValueError("Currency must be a 3-letter ISO code")
        return v.upper()


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    balance: Optional[float] = None
    is_archived: Optional[bool] = None
    credit_limit: Optional[float] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_ACCOUNT_TYPES:
            raise ValueError(
                "Invalid account type. Must be one of: "
                f"{', '.join(sorted(VALID_ACCOUNT_TYPES))}"
            )
        return v

    @field_validator("balance")
    @classmethod
    def validate_balance(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("Balance cannot be negative")
        return v


class AccountResponse(BaseModel):
    id: int
    user_id: int
    name: str
    type: str
    balance: float
    currency: str
    is_archived: bool
    credit_limit: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
