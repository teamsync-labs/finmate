"""Клиент Ollama: обработка текста, фото и голосовых сообщений."""

import base64
from io import BytesIO

from ollama import AsyncClient

from bot_constants import SYSTEM_PROMPT
from config import OLLAMA_API_URL, OLLAMA_MODEL

client = AsyncClient(host=OLLAMA_API_URL)


async def process_text(text: str) -> str:
    """Обрабатывает текстовое сообщение через LLM."""
    response = await client.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    )
    return response.message.content


async def process_photo(
    buffer: BytesIO,
    filename: str,
    prompt: str,
) -> str:
    """Обрабатывает фото чека через LLM."""
    image_b64 = base64.b64encode(buffer.read()).decode("utf-8")
    response = await client.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": prompt,
                "images": [image_b64],
            },
        ],
    )
    return response.message.content


async def process_voice(buffer: BytesIO, filename: str) -> str:
    """Обрабатывает голосовое сообщение (пока заглушка)."""
    # TODO: добавить транскрибацию (например, whisper)
    return f"Обработано голосовое: {filename}"


async def close() -> None:
    """Закрывает внутренний HTTP-клиент Ollama при завершении работы."""
    await client._client.aclose()
