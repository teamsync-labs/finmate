"""
Общие фикстуры и фабрики для тестов.

БД переопределяется на SQLite in-memory (единое подключение через
StaticPool), а зависимость get_db подменяется на тестовую сессию —
чтобы тесты не затрагивали реальную базу приложения.
"""

from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app

_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

_TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=_engine,
)

AUTH_URL = "/api/v1/auth/telegram"


def bearer_headers(auth: dict[str, Any]) -> dict[str, str]:
    """Заголовки Authorization по ответу аутентификации."""

    return {"Authorization": f"Bearer {auth['access_token']}"}


def _override_get_db() -> Generator[Session, None, None]:
    """Возвращает тестовую сессию БД вместо реальной."""

    db = _TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def _force_production_ai_mode(monkeypatch) -> None:
    """AI-вызовы в тестах по умолчанию идут в «продовой» режим.

    То есть services.transactions маршрутизируют LLM/OCR в моки
    services.yandex (DEBUG=False), независимо от значений .env
    разработчика. Debug-тесты Ollama сами выставляют DEBUG=True.
    """

    monkeypatch.setattr(settings, "DEBUG", False)
    yield


@pytest.fixture(autouse=True)
def _setup_db() -> Generator[None, None, None]:
    """Создаёт схему БД до теста и полностью очищает её после."""

    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Прямая сессия БД для подготовки данных в тестах."""

    db = _TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Тестовый клиент FastAPI с подменённой зависимостью get_db."""

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)


@pytest.fixture
def register_user(client: TestClient):
    """
    Фабрика регистрации/логина пользователя через Telegram.

    Возвращает ответ AuthResponse (токены + данные пользователя).
    """

    def _register(
        telegram_id: int,
        username: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"telegram_id": telegram_id}
        if username is not None:
            payload["username"] = username
        response = client.post(AUTH_URL, json=payload)
        assert response.status_code == 200, response.text
        return response.json()
    return _register


@pytest.fixture
def auth_headers(register_user):
    """Фабрика заголовков Authorization для авторизованного пользователя."""

    def _headers(
        telegram_id: int = 100500,
        username: str | None = None,
    ) -> dict[str, str]:
        return bearer_headers(register_user(telegram_id, username))

    return _headers
