"""Тонкий async-клиент к Yandex Cloud AI.

Не знает бизнес-логики: только «отправил байты/текст → получил текст/JSON».
Секреты (YANDEX_API_KEY, YANDEX_FOLDER_ID) живут только здесь и в конфиге.

Три метода по одному шаблону:
    stt_recognize(audio_bytes)  — SpeechKit: голос (ogg/opus) → текст
    ocr_recognize(jpeg_bytes)   — Vision: фото (JPEG) → текст чека
    llm_chat(prompt)            — YandexGPT: prompt → текст (ожидаем JSON)
"""

from __future__ import annotations

import base64

import httpx

from app.core.config import settings


async def _headers() -> dict[str, str]:
    """Общие заголовки для JSON-эндпоинтов Yandex (OCR / LLM)."""

    return {
        "Authorization": f"Api-Key {settings.YANDEX_API_KEY}",
        "x-folder-id": settings.YANDEX_FOLDER_ID,
        "Content-Type": "application/json",
    }


async def stt_recognize(audio_bytes: bytes) -> str:
    """SpeechKit: голос (ogg/opus) → текст.

    Sync REST (stt:recognize). Body — сырые байты аудио, не JSON.
    Лимит ~1 мин / 10 МБ — голосовые в Telegram обычно короче.
    """

    url = (
        f"{settings.YANDEX_STT_URL}?lang=ru-RU&format=oggopus"
    )
    headers = {
        "Authorization": f"Api-Key {settings.YANDEX_API_KEY}",
        "Content-Type": "audio/ogg",
    }
    async with httpx.AsyncClient(
        timeout=settings.YANDEX_AI_TIMEOUT_SECONDS
    ) as client:
        resp = await client.post(url, content=audio_bytes, headers=headers)
    resp.raise_for_status()
    return resp.json().get("result", "")


async def ocr_recognize(jpeg_bytes: bytes) -> str:
    """Vision: фото (JPEG) → текст чека."""

    body = {
        "mimeType": "JPEG",
        "languageCodes": ["ru", "en"],
        "model": "page",
        "content": base64.b64encode(jpeg_bytes).decode(),
    }
    async with httpx.AsyncClient(
        timeout=settings.YANDEX_AI_TIMEOUT_SECONDS
    ) as client:
        resp = await client.post(
            settings.YANDEX_OCR_URL,
            json=body,
            headers=await _headers(),
        )
    resp.raise_for_status()
    annotation = resp.json().get("result", {}).get("textAnnotation", {})
    return annotation.get("fullText", "")


async def llm_chat(prompt: str) -> str:
    """YandexGPT: prompt → текст (ожидаем JSON-ответ)."""

    model_uri = "gpt://{0}/{1}".format(
        settings.YANDEX_FOLDER_ID,
        settings.YANDEX_GPT_MODEL,
    )
    body = {
        "model": model_uri,
        "temperature": 0.2,
        "max_tokens": 800,
        "messages": [{"role": "user", "content": prompt}],
    }
    async with httpx.AsyncClient(
        timeout=settings.YANDEX_AI_TIMEOUT_SECONDS
    ) as client:
        resp = await client.post(
            settings.YANDEX_LLM_URL,
            json=body,
            headers=await _headers(),
        )
    resp.raise_for_status()
    try:
        return resp.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("Некорректный ответ YandexGPT") from exc
