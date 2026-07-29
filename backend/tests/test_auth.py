"""
Минимальные тесты аутентификации:
- POST /api/v1/auth/telegram — регистрация/логин через Telegram
"""


class TestAuthTelegram:
    """Тесты эндпоинта аутентификации через Telegram."""

    def test_auth_telegram_new_user(self, client):
        """
        POST /api/v1/auth/telegram с новым telegram_id
        должен создать пользователя и вернуть токен.
        """
        payload = {
            "telegram_id": 123456789,
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User",
        }
        response = client.post("/api/v1/auth/telegram", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

    def test_auth_telegram_existing_user(self, client):
        """
        Повторный запрос с тем же telegram_id
        должен вернуть новый токен (логин).
        """
        payload = {
            "telegram_id": 999888777,
            "username": "existing_user",
        }
        # Первый раз — создание
        resp1 = client.post("/api/v1/auth/telegram", json=payload)
        assert resp1.status_code == 200
        # token1 = resp1.json()["access_token"] в перспективе не забыть.

        # Второй раз — логин
        resp2 = client.post("/api/v1/auth/telegram", json=payload)
        assert resp2.status_code == 200
        token2 = resp2.json()["access_token"]

        # Токены могут быть разными (разное время выпуска)
        assert isinstance(token2, str)

    def test_auth_telegram_only_required_fields(self, client):
        """
        Должен работать с минимальным набором полей
        (только telegram_id).
        """
        payload = {"telegram_id": 555666777}
        response = client.post("/api/v1/auth/telegram", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_auth_telegram_invalid_payload(self, client):
        """
        Без telegram_id должен вернуть 422 Validation Error.
        """
        payload = {"username": "no_id_user"}
        response = client.post("/api/v1/auth/telegram", json=payload)
        assert response.status_code == 422
