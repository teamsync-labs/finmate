"""Парсинг JSON-ответов LLM."""
import json
import re


def clean_json(raw: str) -> str:
    """
    Очищает ответ модели: убирает markdown-обёртку.

    Лишний текст и хвостовые запятые, оставляя только JSON.
    """

    if not isinstance(raw, str):
        return raw
    text = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")

    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]
    text = re.sub(r",\s*([}\]])", r"\1", text)

    return text.strip()


def formatting_values(values: str) -> dict | bool:
    """Парсит ответ модели в словарь расходов."""
    try:
        return json.loads(clean_json(values))
    except json.JSONDecodeError:
        return False
