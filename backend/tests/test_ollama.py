"""Unit-тесты тонкого клиента Ollama (dev-режим).

Основной регресс, который здесь ловим — _strip_thinking_wrappers:
- регулярка для блоков `...` должна матчить именно три точки, а не
  «любые три символа» (иначе съедает первые 3 символа каждой строки
  OCR-результата);
- блоки рассуждений <thinking>...</thinking> должны вырезаться целиком.

Плюс проверка, что OCR-запрос идёт в Ollama с включённым режимом
размышления (think=True) — без него thinking-модели (Qwen3-VL)
могут не распознать изображение и вернуть пустой текст.
"""

import asyncio
import base64

from app.services import ollama
from app.services.ollama import _strip_thinking_wrappers


def test_keeps_first_three_chars_of_each_line():
    """Регресс: первые 3 символа строки не должны удаляться."""

    text = "OOO ROMASHKA\nKafe UYUT\nKapuchino 250.00"
    assert _strip_thinking_wrappers(text) == text


def test_strips_thinking_blocks():
    text = (
        "<thinking>Мне нужно внимательно посмотреть на чек.</thinking>\n"
        "Молоко 89.90\n"
        "<|thinking|>Ещё подумаю.</|thinking|>"
        "ИТОГО 134.90"
    )
    result = _strip_thinking_wrappers(text)
    assert "thinking" not in result
    assert "Молоко 89.90" in result
    assert "ИТОГО 134.90" in result


def test_strips_literal_dot_delimiters():
    """Строки, состоящие из трёх точек (`...`), удаляются."""

    text = "...\nМолоко 89.90\n...\nИТОГО 134.90"
    result = _strip_thinking_wrappers(text)
    assert "..." not in result
    assert "Молоко 89.90" in result
    assert "ИТОГО 134.90" in result


def test_empty_and_whitespace():
    assert _strip_thinking_wrappers("") == ""
    assert _strip_thinking_wrappers("   \n  ") == ""


def test_ocr_recognize_enables_thinking(monkeypatch):
    """OCR-канал: think=True уходит в Ollama (размышление включено)."""

    captured = {}

    class _FakeChatResponse:
        def __init__(self, content: str):
            self._content = content

        def __getitem__(self, key: str):
            if key == "message":
                return {"content": self._content}
            raise KeyError(key)

    class _FakeClient:
        async def chat(self, **kwargs):
            captured.update(kwargs)
            return _FakeChatResponse("ПЯТЁРОЧКА\nИТОГО 134.90")

    monkeypatch.setattr(ollama, "_async_client", lambda: _FakeClient())

    text = asyncio.run(ollama.ocr_recognize(b"jpeg-bytes"))

    assert text == "ПЯТЁРОЧКА\nИТОГО 134.90"
    assert captured["think"] is True
    assert captured["options"]["num_predict"] == 4096
    assert captured["messages"][0]["images"] == [
        base64.b64encode(b"jpeg-bytes").decode()
    ]
