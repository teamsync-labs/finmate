"""
Тонкий async-клиент к локальной Ollama (dev-режим).

Зеркалит интерфейс services/yandex.py для двух операций, которые
Ollama умеет из коробки:

ocr_recognize(jpeg_bytes)— vision-модель (llava, Qwen3-VL и т.п.):
                    фото → текст чека (с включённым режимом размышления)
llm_chat(prompt)— чат-модель: prompt → текст (ожидаем JSON)

Ограничение: STT (голос → текст) Ollama не поддерживает — поэтому для
voice-канала в dev-режиме по-прежнему используется Yandex SpeechKit
(см. диспетчеризацию в services/transactions.py).
"""

from __future__ import annotations

import base64
import re

import ollama

from app.core.config import settings


def _strip_thinking_wrappers(text: str) -> str:
    """Убирает рассуждения thinking-моделей из содержимого ответа.

    Часть GGUF-сборок (например, Qwen3-VL-*-Thinking) кладёт
    chain-of-thought прямо в content в блоках <thinking>...</thinking>
    или .../.... Для OCR/LLM эти блоки не нужны.
    """

    text = re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.S)
    text = re.sub(r"<\|thinking\|>.*?</\|thinking\|>", "", text, flags=re.S)
    text = re.sub(r"^\.\.\.\s*", "", text, flags=re.M)
    return text.strip()


def _async_client() -> ollama.AsyncClient:
    """Async-клиент к локальному серверу Ollama."""

    return ollama.AsyncClient(
        host=settings.OLLAMA_BASE_URL,
        timeout=settings.OLLAMA_TIMEOUT_SECONDS,
    )


async def llm_chat(prompt: str) -> str:
    """Ollama (LLM): prompt → текст (ожидаем JSON-ответ).

    format="json" заставляет модель вернуть валидный JSON, а options
    повторяют параметры YandexGPT (temperature/max_tokens), чтобы
    поведение в dev-режиме было похоже на прод.
    """

    resp = await _async_client().chat(
        model=settings.OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={
            "temperature": 0.2,
            "num_predict": 800,
        },
        format="json",
    )
    return resp["message"]["content"]


async def ocr_recognize(jpeg_bytes: bytes) -> str:
    """
    Ollama (vision): фото (JPEG) → текст чека.

    Картинка передаётся base64-строкой в поле images сообщения —
    так же, как Yandex Vision принимает её в поле content.

    think=True: включает режим размышления у thinking-моделей
    (Qwen3-VL и т.п.). Без него такие модели могут не распознать
    изображение и вернуть пустой текст, хотя на обычном тексте
    работают. Рассуждения в <thinking>...</thinking> вырезаются
    ниже через _strip_thinking_wrappers.
    """

    image_b64 = base64.b64encode(jpeg_bytes).decode()
    resp = await _async_client().chat(
        model=settings.OLLAMA_OCR_MODEL,
        messages=[
            {
                "role": "user",
                "content": (
                    "Ты — программа распознавания текста (OCR). "
                    "Скопируй с изображения чека ВЕСЬ видимый текст "
                    "построчно, в исходном порядке, без изменений и "
                    "комментариев."
                ),
                "images": [image_b64],
            }
        ],
        options={"temperature": 0.0, "num_predict": 4096},
        # think=True,
    )
    return _strip_thinking_wrappers(resp["message"]["content"])
