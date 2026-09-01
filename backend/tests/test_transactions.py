"""
Тесты разбора транзакций:
- юнит-тесты parser.py (json-обёртки, категории, суммы)
- эндпоинты /api/v1/transactions/{voice,photo,text}
- авторизация через X-Service-Key + X-Telegram-Id
- оркестрация цепочек с замоканным services.yandex
"""

import json
from io import BytesIO

import pytest
from PIL import Image

from app.core.config import settings
from app.models.expenses import Expenses
from app.services import ollama, parser, yandex

TEXT_URL = "/api/v1/transactions/text"
VOICE_URL = "/api/v1/transactions/voice"
PHOTO_URL = "/api/v1/transactions/photo"

SERVICE_KEY = "test-service-key"
TELEGRAM_ID = 100500


def _service_headers() -> dict[str, str]:
    return {
        "X-Service-Key": SERVICE_KEY,
        "X-Telegram-Id": str(TELEGRAM_ID),
    }


def _make_jpeg() -> bytes:
    """Генерирует небольшой валидный JPEG через Pillow."""

    buffer = BytesIO()
    Image.new("RGB", (8, 8), color=(255, 255, 255)).save(buffer, "JPEG")
    return buffer.getvalue()


def _llm_payload(amount: float | None = 150.0) -> str:
    return json.dumps({
        "amount": amount,
        "currency": "RUB",
        "merchant": "Кофейня",
        "category": "Продукты",
        "items": ["капучино", "круассан"],
        "raw_summary": "кофе 150 рублей",
    }, ensure_ascii=False)


@pytest.fixture
def service_key(monkeypatch):
    """Включает сервисную авторизацию для бота."""

    monkeypatch.setattr(settings, "BOT_SERVICE_KEY", SERVICE_KEY)
    return SERVICE_KEY


class TestParser:
    """Юнит-тесты чистого слоя parser.py."""

    def test_extract_json_with_code_fence(self):
        text = '```json\n{"amount": 100}\n```'
        assert parser.extract_json(text) == {"amount": 100}

    def test_extract_json_with_prose(self):
        text = 'Вот данные: {"amount": 50, "merchant": "Кофе"} Надеюсь, помог.'
        data = parser.extract_json(text)
        assert data["amount"] == 50
        assert data["merchant"] == "Кофе"

    def test_extract_json_invalid(self):
        with pytest.raises(ValueError):
            parser.extract_json("вообще не json")

    def test_normalize_category_aliases(self):
        assert parser.normalize_category("Продукты") == "food"
        assert parser.normalize_category("еда") == "food"
        assert parser.normalize_category("Food") == "food"
        assert parser.normalize_category("transport") == "transport"
        assert parser.normalize_category("неизвестное") == "other"

    def test_normalize_category_empty(self):
        assert parser.normalize_category(None) == "general"
        assert parser.normalize_category("") == "general"

    def test_parse_amount(self):
        assert parser.parse_amount(134.9) == 134.9
        assert parser.parse_amount("134,90") == 134.9
        assert parser.parse_amount("Итого: 1 234.50 руб") == 1234.5
        assert parser.parse_amount(None) is None


class TestTextEndpoint:
    """POST /api/v1/transactions/text."""

    def test_requires_auth(self, client):
        """Без заголовков авторизации — 401."""

        response = client.post(TEXT_URL, json={"text": "кофе 150 руб"})
        assert response.status_code == 401

    def test_text_parses(
        self, client,
        register_user,
        service_key,
        monkeypatch
    ):
        """Полный путь: текст → LLM → ParsedTransaction."""

        register_user(TELEGRAM_ID, username="tester")

        async def fake_llm(prompt: str) -> str:
            return _llm_payload()

        monkeypatch.setattr(yandex, "llm_chat", fake_llm)

        response = client.post(
            TEXT_URL,
            json={"text": "кофе 150 руб"},
            headers=_service_headers(),
        )
        assert response.status_code == 200
        data = response.json()

        assert data["amount"] == 150.0
        assert data["currency"] == "RUB"
        assert data["merchant"] == "Кофейня"
        assert data["category"] == "food"
        assert data["items"] == ["капучино", "круассан"]

    def test_text_saves_expense(
        self, client, register_user, service_key, monkeypatch, db_session
    ):
        """Текстовый расход автоматически сохраняется в БД."""

        register_user(TELEGRAM_ID, username="tester")

        async def fake_llm(prompt: str) -> str:
            return _llm_payload()

        monkeypatch.setattr(yandex, "llm_chat", fake_llm)

        response = client.post(
            TEXT_URL,
            json={"text": "кофе 150 руб"},
            headers=_service_headers(),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["expense_id"] is not None

        expense = db_session.query(Expenses).filter(
            Expenses.id == data["expense_id"]
        ).one()
        assert expense.expense_name == "Кофейня"
        assert expense.amount == 150.0
        assert expense.type == "food"
        assert expense.currency == "RUB"
        assert expense.user_id is not None

    def test_text_llm_non_json(
        self, client,
        register_user,
        service_key,
        monkeypatch
    ):
        """LLM вернул не-JSON — 422."""

        register_user(TELEGRAM_ID)

        async def fake_llm(prompt: str) -> str:
            return "просто текст без json"

        monkeypatch.setattr(yandex, "llm_chat", fake_llm)

        response = client.post(
            TEXT_URL,
            json={"text": "кофе"},
            headers=_service_headers(),
        )
        assert response.status_code == 422


class TestVoiceEndpoint:
    """POST /api/v1/transactions/voice."""

    def test_voice_pipeline(
        self, client,
        register_user,
        service_key,
        monkeypatch
    ):
        """Голос: STT → LLM → ParsedTransaction c transcript."""

        register_user(TELEGRAM_ID)
        calls = {}

        async def fake_stt(audio_bytes: bytes) -> str:
            calls["audio"] = audio_bytes
            return "кофе 150 рублей"

        async def fake_llm(prompt: str) -> str:
            calls["prompt"] = prompt
            return _llm_payload()

        monkeypatch.setattr(yandex, "stt_recognize", fake_stt)
        monkeypatch.setattr(yandex, "llm_chat", fake_llm)

        response = client.post(
            VOICE_URL,
            files={"voice": ("voice.ogg", b"fake-ogg-bytes", "audio/ogg")},
            headers=_service_headers(),
        )
        assert response.status_code == 200
        data = response.json()

        assert data["amount"] == 150.0
        assert data["category"] == "food"
        assert data["transcript"] == "кофе 150 рублей"
        assert calls["audio"] == b"fake-ogg-bytes"
        assert "кофе 150 рублей" in calls["prompt"]

    def test_voice_empty_transcript(
        self, client,
        register_user,
        service_key,
        monkeypatch
    ):
        """STT вернул пустой текст — 422, LLM не зовём."""

        register_user(TELEGRAM_ID)

        async def fake_stt(audio_bytes: bytes) -> str:
            return ""

        monkeypatch.setattr(yandex, "stt_recognize", fake_stt)
        monkeypatch.setattr(
            yandex, "llm_chat",
            lambda prompt: (_ for _ in ()).throw(
                AssertionError("не должны звать LLM")
            )
        )

        response = client.post(
            VOICE_URL,
            files={"voice": ("voice.ogg", b"fake", "audio/ogg")},
            headers=_service_headers(),
        )
        assert response.status_code == 422
        assert "распознать" in response.json()["detail"]

    def test_voice_empty_transcript_not_saved(
        self, client, register_user,
        service_key, monkeypatch,
        db_session
    ):
        """Пустой транскрипт — 422, в БД ничего не создаётся."""

        register_user(TELEGRAM_ID)

        async def fake_stt(audio_bytes: bytes) -> str:
            return ""

        monkeypatch.setattr(yandex, "stt_recognize", fake_stt)

        response = client.post(
            VOICE_URL,
            files={"voice": ("voice.ogg", b"fake", "audio/ogg")},
            headers=_service_headers(),
        )
        assert response.status_code == 422

        count = db_session.query(Expenses).count()
        assert count == 0

    def test_voice_saves_expense(
        self, client, register_user,
        service_key, monkeypatch,
        db_session
    ):
        """Распознанный голос сохраняется в таблицу expenses."""

        register_user(TELEGRAM_ID)

        async def fake_stt(audio_bytes: bytes) -> str:
            return "кофе 150 рублей"

        async def fake_llm(prompt: str) -> str:
            return _llm_payload()

        monkeypatch.setattr(yandex, "stt_recognize", fake_stt)
        monkeypatch.setattr(yandex, "llm_chat", fake_llm)

        response = client.post(
            VOICE_URL,
            files={"voice": ("voice.ogg", b"fake-ogg-bytes", "audio/ogg")},
            headers=_service_headers(),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["expense_id"] is not None

        expense = db_session.query(Expenses).filter(
            Expenses.id == data["expense_id"]
        ).one()
        assert expense.amount == 150.0
        assert expense.type == "food"
        assert expense.currency == "RUB"
        assert expense.expense_name == "Кофейня"


class TestPhotoEndpoint:
    """POST /api/v1/transactions/photo."""

    def test_photo_pipeline(
        self, client, register_user,
        service_key, monkeypatch
    ):
        """Фото: JPEG → OCR → LLM → ParsedTransaction c raw_ocr_text."""

        register_user(TELEGRAM_ID)
        calls = {}

        async def fake_ocr(jpeg_bytes: bytes) -> str:
            calls["jpeg"] = jpeg_bytes
            return "ПЯТЁРОЧКА\nМолоко 89.90\nИТОГО 134.90"

        async def fake_llm(prompt: str) -> str:
            calls["prompt"] = prompt
            return json.dumps({
                "amount": 134.9,
                "currency": "RUB",
                "merchant": "Пятёрочка",
                "category": "продукты",
                "items": ["Молоко"],
                "raw_summary": "Молоко 89.90, итого 134.90",
            }, ensure_ascii=False)

        monkeypatch.setattr(yandex, "ocr_recognize", fake_ocr)
        monkeypatch.setattr(yandex, "llm_chat", fake_llm)

        jpeg = _make_jpeg()
        response = client.post(
            PHOTO_URL,
            files={"photo": ("receipt.jpg", jpeg, "image/jpeg")},
            headers=_service_headers(),
        )
        assert response.status_code == 200
        data = response.json()

        assert data["amount"] == 134.9
        assert data["category"] == "food"
        assert data["merchant"] == "Пятёрочка"
        assert data["raw_ocr_text"].startswith("ПЯТЁРОЧКА")
        assert "ИТОГО" in calls["prompt"]

    def test_photo_too_large(
        self, client, register_user,
        service_key, monkeypatch
    ):
        """Слишком большой файл — 413."""

        register_user(TELEGRAM_ID)
        monkeypatch.setattr(settings, "MAX_UPLOAD_BYTES", 10)

        response = client.post(
            PHOTO_URL,
            files={"photo": ("big.jpg", b"x" * 100, "image/jpeg")},
            headers=_service_headers(),
        )
        assert response.status_code == 413

    def test_photo_empty_ocr(
        self, client, register_user,
        service_key, monkeypatch
    ):
        """OCR вернул пустой текст — 422, а не «Категория: general»."""

        register_user(TELEGRAM_ID)

        async def fake_ocr(jpeg_bytes: bytes) -> str:
            return "   "

        monkeypatch.setattr(yandex, "ocr_recognize", fake_ocr)
        monkeypatch.setattr(
            yandex, "llm_chat",
            lambda prompt: (_ for _ in ()).throw(
                AssertionError("не должны звать LLM при пустом OCR")
            )
        )

        response = client.post(
            PHOTO_URL,
            files={"photo": ("receipt.jpg", _make_jpeg(), "image/jpeg")},
            headers=_service_headers(),
        )
        assert response.status_code == 422
        assert "распознал" in response.json()["detail"]


class TestDebugOllamaRouting:
    """DEBUG=True: LLM/OCR идут в локальную Ollama, а не в Yandex Cloud."""

    def test_text_uses_ollama_in_debug(
        self, client, register_user, service_key, monkeypatch
    ):
        """Текст в dev-режиме: LLM — локальная Ollama."""

        register_user(TELEGRAM_ID)
        monkeypatch.setattr(settings, "DEBUG", True)

        async def fake_ollama_llm(prompt: str) -> str:
            return _llm_payload()

        monkeypatch.setattr(ollama, "llm_chat", fake_ollama_llm)
        monkeypatch.setattr(
            yandex, "llm_chat",
            lambda prompt: (_ for _ in ()).throw(
                AssertionError("не должны ходить в YandexGPT при DEBUG=True")
            ),
        )

        response = client.post(
            TEXT_URL,
            json={"text": "кофе 150 руб"},
            headers=_service_headers(),
        )
        assert response.status_code == 200
        assert response.json()["amount"] == 150.0

    def test_photo_uses_ollama_in_debug(
        self, client, register_user, service_key, monkeypatch
    ):
        """Фото в dev-режиме: OCR и LLM — локальная Ollama."""

        register_user(TELEGRAM_ID)
        monkeypatch.setattr(settings, "DEBUG", True)

        async def fake_ollama_ocr(jpeg_bytes: bytes) -> str:
            return "ПЯТЁРОЧКА\nМолоко 89.90\nИТОГО 134.90"

        async def fake_ollama_llm(prompt: str) -> str:
            return json.dumps({
                "amount": 134.9,
                "currency": "RUB",
                "merchant": "Пятёрочка",
                "category": "продукты",
                "items": ["Молоко"],
                "raw_summary": "Молоко 89.90, итого 134.90",
            }, ensure_ascii=False)

        monkeypatch.setattr(ollama, "ocr_recognize", fake_ollama_ocr)
        monkeypatch.setattr(ollama, "llm_chat", fake_ollama_llm)
        monkeypatch.setattr(
            yandex, "ocr_recognize",
            lambda jpeg: (_ for _ in ()).throw(
                AssertionError(
                    "не должны ходить в Yandex Vision при DEBUG=True"
                )
            ),
        )
        monkeypatch.setattr(
            yandex, "llm_chat",
            lambda prompt: (_ for _ in ()).throw(
                AssertionError("не должны ходить в YandexGPT при DEBUG=True")
            ),
        )

        response = client.post(
            PHOTO_URL,
            files={"photo": ("receipt.jpg", _make_jpeg(), "image/jpeg")},
            headers=_service_headers(),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 134.9
        assert data["category"] == "food"
        assert data["raw_ocr_text"].startswith("ПЯТЁРОЧКА")

    def test_voice_uses_yandex_stt_and_ollama_llm_in_debug(
        self, client, register_user, service_key, monkeypatch
    ):
        """Голос в dev-режиме: STT — Yandex SpeechKit, LLM — Ollama."""

        register_user(TELEGRAM_ID)
        monkeypatch.setattr(settings, "DEBUG", True)

        async def fake_stt(audio_bytes: bytes) -> str:
            return "кофе 150 рублей"

        async def fake_ollama_llm(prompt: str) -> str:
            return _llm_payload()

        monkeypatch.setattr(yandex, "stt_recognize", fake_stt)
        monkeypatch.setattr(ollama, "llm_chat", fake_ollama_llm)
        monkeypatch.setattr(
            yandex, "llm_chat",
            lambda prompt: (_ for _ in ()).throw(
                AssertionError("не должны ходить в YandexGPT при DEBUG=True")
            ),
        )

        response = client.post(
            VOICE_URL,
            files={"voice": ("voice.ogg", b"fake-ogg-bytes", "audio/ogg")},
            headers=_service_headers(),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 150.0
        assert data["transcript"] == "кофе 150 рублей"
