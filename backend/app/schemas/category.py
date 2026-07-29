from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, field_validator

VALID_CATEGORY_TYPES = {"income", "expense"}


class CategoryCreate(BaseModel):
    name: str
    type: str
    parent_id: Optional[int] = None
    icon: Optional[str] = None
    color: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in VALID_CATEGORY_TYPES:
            raise ValueError(
                "Type must be one of: "
                f"{', '.join(sorted(VALID_CATEGORY_TYPES))}"
            )
        return v

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.match(r"^#[0-9a-fA-F]{6}$", v):
            raise ValueError("Color must be a valid hex color (e.g. #FF0000)")
        return v


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    parent_id: Optional[int] = None

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.match(r"^#[0-9a-fA-F]{6}$", v):
            raise ValueError("Color must be a valid hex color (e.g. #FF0000)")
        return v


class CategoryResponse(BaseModel):
    id: int
    user_id: int
    name: str
    type: str
    parent_id: Optional[int] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_system: bool = False

    model_config = {"from_attributes": True}
