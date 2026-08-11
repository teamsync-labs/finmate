from __future__ import annotations

from datetime import datetime, time, timezone

from pydantic import BaseModel, field_validator, model_validator


class ReportRequest(BaseModel):
    """Данные для формирования отчёта за период (две даты)."""

    date_from: str
    date_to: str

    @field_validator("date_from", "date_to")
    @classmethod
    def validate_date_string(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Date cannot be empty")
        try:
            datetime.fromisoformat(v)
        except ValueError as exc:
            raise ValueError(
                "Invalid date format. Expected ISO format, "
                "e.g. '2025-01-01' or '2025-01-01T10:30:00'"
            ) from exc
        return v

    @model_validator(mode="after")
    def check_period(self) -> "ReportRequest":
        if self.start_datetime > self.end_datetime:
            raise ValueError(
                "date_from must be earlier than or equal to date_to"
            )
        return self

    @property
    def start_datetime(self) -> datetime:
        """Начало периода (00:00:00 UTC дня date_from)."""
        parsed = datetime.fromisoformat(self.date_from)
        return datetime.combine(parsed.date(), time.min, tzinfo=timezone.utc)

    @property
    def end_datetime(self) -> datetime:
        """Конец периода (23:59:59.999999 UTC дня date_to)."""
        parsed = datetime.fromisoformat(self.date_to)
        return datetime.combine(parsed.date(), time.max, tzinfo=timezone.utc)


class ReportExpenseItem(BaseModel):
    """Один расход внутри отчёта."""

    id: int
    expense_name: str
    amount: float
    currency: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CategoryReport(BaseModel):
    """Расходы одной категории за период."""

    category: str
    total: float
    count: int
    expenses: list[ReportExpenseItem]


class ReportResponse(BaseModel):
    """Итоговый отчёт по расходам за период."""

    date_from: str
    date_to: str
    total_amount: float
    total_count: int
    categories: list[CategoryReport]
