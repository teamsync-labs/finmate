"""
Минимальные тесты базовых эндпоинтов:
- GET / — приветственное сообщение
- GET /health — проверка здоровья сервиса
"""


class TestRoot:
    """Тесты корневого эндпоинта."""

    def test_root_returns_welcome(self, client):
        """GET / должен вернуть приветствие с именем приложения."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "FinMate" in data["message"]


class TestHealth:
    """Тесты эндпоинта health."""

    def test_health_returns_status(self, client):
        """GET /health должен вернуть статус и состояние БД."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert data["status"] in ("ok", "degraded")
        assert data["database"] in ("connected", "disconnected")
