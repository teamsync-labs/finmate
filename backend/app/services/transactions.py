"""Оркестратор разбора транзакций.

Собирает цепочки:
    voice → SpeechKit STT → LLM
    photo → Vision OCR   → LLM
    text  → LLM

Выбор AI-провайдера зависит от DEBUG:
    DEBUG=False (прод)  → Yandex Cloud (YandexGPT / Vision / SpeechKit)
    DEBUG=True  (dev)   → локальная Ollama (LLM + OCR), STT — Yandex
                          SpeechKit (Ollama не поддерживает голос)

Каждый слой легко тестировать отдельно: здесь не ходим в сеть напрямую,
а вызываем функции из services/yandex.py и services/ollama.py (их можно
замокать).
"""

from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageOps

from app.core.config import settings
from app.schemas.transaction import ParsedTransaction
from app.services import ollama, parser, yandex

# Категории, которые LLM может вернуть (совпадает с VALID_EXPENSE_TYPES).
_ALLOWED_CATEGORIES = (
    "general, food, transport, housing, utilities, entertainment, "
    "health, education, shopping, other"
)

_LLM_SYSTEM_PROMPT = (
    "Ты — ассистент финансового трекера. Из входного текста извлеки "
    "данные о расходе.\n"
    "Верни ТОЛЬКО JSON без пояснений и markdown-обёрток в формате:\n"
    '{"amount": число|null, "currency": "RUB", "merchant": строка|null, '
    '"category": одна из [' + _ALLOWED_CATEGORIES + '], '
    '"items": ["строка", ...], "raw_summary": "краткое описание расхода"}\n'
    "Если сумма не указана — amount: null. Если категория неясна — other."
)


def _build_prompt(source_kind: str, text: str) -> str:
    return (
        _LLM_SYSTEM_PROMPT
        + "\n\nИсточник: "
        + source_kind
        + ".\nВходной текст:\n"
        + text
    )


def _transaction_from_llm(raw_llm: str, **extra) -> ParsedTransaction:
    """Разбирает ответ LLM в ParsedTransaction (+ сырые распознавания)."""

    data = parser.extract_json(raw_llm)
    fields = parser.build_transaction(data)
    fields.update(extra)
    return ParsedTransaction(**fields)


# --- Диспетчеризация AI-провайдера -------------------------------------
# В dev-режиме (DEBUG=True) не ходим в облако Yandex, а используем
# локальную Ollama. Прод (DEBUG=False) — Yandex Cloud как раньше.


async def _llm_chat(prompt: str) -> str:
    """LLM: YandexGPT в проде, локальная Ollama в dev-режиме."""

    if settings.DEBUG:
        return await ollama.llm_chat(prompt)
    return await yandex.llm_chat(prompt)


async def _ocr_recognize(jpeg_bytes: bytes) -> str:
    """OCR: Yandex Vision в проде, vision-модель Ollama в dev-режиме."""

    if settings.DEBUG:
        return await ollama.ocr_recognize(jpeg_bytes)
    return await yandex.ocr_recognize(jpeg_bytes)


async def _stt_recognize(audio_bytes: bytes) -> str:
    """STT: всегда Yandex SpeechKit (Ollama не умеет распознавать голос)."""

    return await yandex.stt_recognize(audio_bytes)


def _to_jpeg(data: bytes) -> bytes:
    """Конвертирует фото в JPEG (Vision не любит WebP).

    Если изображение уже JPEG — возвращаем как есть, иначе
    конвертируем через Pillow и применяем EXIF-транспонирование.
    """

    try:
        image = Image.open(BytesIO(data))
    except Exception as exc:
        raise ValueError("Не удалось прочитать изображение") from exc

    if image.format == "JPEG":
        return data

    image = ImageOps.exif_transpose(image)
    image = image.convert("RGB")
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


async def process_voice(audio_bytes: bytes) -> ParsedTransaction:
    """Голос → текст (STT) → структура расхода (LLM)."""

    transcript = (await _stt_recognize(audio_bytes)).strip()
    if not transcript:
        return ParsedTransaction(transcript="")
    raw_llm = await _llm_chat(
        _build_prompt("голосовое сообщение", transcript)
    )
    return _transaction_from_llm(raw_llm, transcript=transcript)


async def process_photo(photo_bytes: bytes) -> ParsedTransaction:
    """Фото → JPEG → OCR → структура расхода (LLM)."""

    jpeg = _to_jpeg(photo_bytes)
    ocr_text = (await _ocr_recognize(jpeg)).strip()
    if not ocr_text:
        return ParsedTransaction(raw_ocr_text="")
    raw_llm = await _llm_chat(_build_prompt("текст чека", ocr_text))
    return _transaction_from_llm(raw_llm, raw_ocr_text=ocr_text)


async def process_text(text: str) -> ParsedTransaction:
    """Текст → структура расхода (LLM)."""

    raw_llm = await _llm_chat(_build_prompt("текст пользователя", text))
    return _transaction_from_llm(raw_llm)
