"""Чистое извлечение структуры из ответа LLM.

Задача слоя — сделать ответ YandexGPT стабильным:
- срезать ```json-обёртки и пояснения, достать JSON;
- нормализовать категорию в существующий VALID_EXPENSE_TYPES;
- fallback на сумму regex'ом, если LLM вернула её строкой.
"""

from __future__ import annotations

import json
import re

from app.core.constants import (
    DEFAULT_CURRENCY,
    DEFAULT_EXPENSE_TYPE,
    VALID_EXPENSE_TYPES,
)

# Русские/человеческие метки → enum из constants.py.
# Проверяем по нижнему регистру, поэтому можно смешивать регистры.
CATEGORY_ALIASES: dict[str, str] = {
    # food
    "продукты": "food", "продукт": "food", "еда": "food", "еды": "food",
    "продуктовый": "food", "супермаркет": "food", "магазин": "food",
    "бакалея": "food", "кафе": "food", "ресторан": "food", "кофе": "food",
    "обед": "food", "завтрак": "food", "ужин": "food", "food": "food",
    "groceries": "food", "cafe": "food", "restaurant": "food",
    # transport
    "транспорт": "transport", "проезд": "transport", "такси": "transport",
    "метро": "transport", "автобус": "transport", "бензин": "transport",
    "азс": "transport", "парковка": "transport", "transport": "transport",
    "taxi": "transport", "fuel": "transport", "gas": "transport",
    # housing
    "жильё": "housing", "жилье": "housing", "аренда": "housing",
    "квартплата": "housing", "ипотека": "housing", "housing": "housing",
    "rent": "housing", "mortgage": "housing",
    # utilities
    "коммунальные": "utilities", "коммуналка": "utilities", "жкх": "utilities",
    "свет": "utilities", "электричество": "utilities", "газ": "utilities",
    "вода": "utilities", "интернет": "utilities", "связь": "utilities",
    "телефон": "utilities", "utilities": "utilities",
    "electricity": "utilities", "water": "utilities", "internet": "utilities",
    # entertainment
    "развлечения": "entertainment", "развлечение": "entertainment",
    "кино": "entertainment", "досуг": "entertainment",
    "отдых": "entertainment",
    "игры": "entertainment",
    "хобби": "entertainment",
    "entertainment": "entertainment", "movies": "entertainment",
    "games": "entertainment",
    # health
    "здоровье": "health", "аптека": "health", "лекарства": "health",
    "лекарство": "health", "больница": "health", "врач": "health",
    "клиника": "health", "спортзал": "health", "health": "health",
    "pharmacy": "health", "medicine": "health", "doctor": "health",
    # education
    "образование": "education", "обучение": "education", "учёба": "education",
    "учеба": "education", "школа": "education", "курсы": "education",
    "университет": "education", "education": "education",
    "courses": "education", "books": "education", "книги": "education",
    # shopping
    "покупки": "shopping", "покупка": "shopping", "одежда": "shopping",
    "вещи": "shopping", "подарки": "shopping", "подарок": "shopping",
    "техника": "shopping", "электроника": "shopping", "обувь": "shopping",
    "shopping": "shopping", "clothes": "shopping", "gifts": "shopping",
    # прочее
    "другое": "other", "прочее": "other", "разное": "other", "other": "other",
    # общее
    "общее": "general", "general": "general",
}


def extract_json(text: str) -> dict:
    """Достаёт JSON из ответа LLM.

    Срезает ```json-обёртки и любые пояснения вокруг, ищет первую { ... }.
    """

    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.S)
    text = re.sub(r"\s*```$", "", text, flags=re.S)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            raise ValueError("LLM вернул не-JSON")
        data = json.loads(match.group())

    if not isinstance(data, dict):
        raise ValueError("LLM вернул не-JSON-объект")
    return data


def normalize_category(raw: str | None) -> str:
    """Нормализует категорию из LLM в допустимый VALID_EXPENSE_TYPES.

    Принимает русские метки («Продукты»), английские («food») и
    несуществующие значения. Fallback — DEFAULT_EXPENSE_TYPE.
    """

    if not raw:
        return DEFAULT_EXPENSE_TYPE
    key = raw.strip().lower()
    if key in VALID_EXPENSE_TYPES:
        return key
    mapped = CATEGORY_ALIASES.get(key)
    if mapped in VALID_EXPENSE_TYPES:
        return mapped
    return "other"


def parse_amount(raw) -> float | None:
    """Извлекает сумму из числа или строки (в т.ч. «134,90», «1 234.50»)."""

    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return round(float(raw), 2)
    match = re.search(
        r"(\d+(?:[.,]\d{1,2})?)",
        str(raw).replace(" ", "").replace("\u00a0", ""),
    )
    if not match:
        return None
    return round(float(match.group(1).replace(",", ".")), 2)


def _normalize_currency(raw) -> str:
    """Валидный 3-буквенный код валюты или DEFAULT_CURRENCY."""

    if isinstance(raw, str) and raw.isalpha() and len(raw) == 3:
        return raw.upper()
    return DEFAULT_CURRENCY


def _normalize_items(raw) -> list[str]:
    """Список позиций чека: только непустые строки."""

    if not isinstance(raw, list):
        return []
    items: list[str] = []
    for item in raw:
        if isinstance(item, str) and item.strip():
            items.append(item.strip())
    return items


def build_transaction(data: dict) -> dict:
    """Нормализует сырой JSON из LLM в поля ParsedTransaction."""

    merchant = data.get("merchant")
    return {
        "amount": parse_amount(data.get("amount")),
        "currency": _normalize_currency(data.get("currency")),
        "merchant": (
            merchant
            if isinstance(merchant, str) and merchant.strip()
            else None
        ),
        "category": normalize_category(data.get("category")),
        "items": _normalize_items(data.get("items")),
        "raw_summary": str(data.get("raw_summary") or "").strip(),
    }
