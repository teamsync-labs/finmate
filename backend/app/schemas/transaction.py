"""Схемы разбора транзакций (голос / фото / текст)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.core.constants import DEFAULT_CURRENCY, DEFAULT_EXPENSE_TYPE


class TextTransactionRequest(BaseModel):
    """Тело запроса для текстового разбора."""

    text: str = Field(min_length=1, max_length=4000)


class ParsedTransaction(BaseModel):
    """Единый ответ боту: результат разбора одним из трёх каналов."""

    amount: float | None = None
    currency: str = DEFAULT_CURRENCY
    merchant: str | None = None
    category: str = DEFAULT_EXPENSE_TYPE
    items: list[str] = []
    raw_summary: str = ""
    # Сырые результаты распознавания (для voice/photo каналов).
    transcript: str | None = None
    raw_ocr_text: str | None = None
    # ID сохранённого расхода. None — если сумма не распознана
    # (в этом случае расход в БД не создаётся).
    expense_id: int | None = None
