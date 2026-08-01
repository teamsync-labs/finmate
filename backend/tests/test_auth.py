"""
Минимальные тесты аутентификации:
- POST /api/v1/auth/telegram — регистрация/логин через Telegram
- Ответ содержит токен + полные данные пользователя
"""


class TestAuthTelegram:
    """Тесты эндпоинта аутентификации через Telegram."""

    def _register(self, client, payload: dict) -> dict:
        """Регистрирует/логинит пользователя и возвращает ответ."""
        response = client.post("/api/v1/auth/telegram", json=payload)
        assert response.status_code == 200
        return response.json()

    def _assert_user_fields(self, data: dict, telegram_id: int):
        """Проверяет, что ответ содержит токен и базовые поля пользователя."""
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["telegram_id"] == telegram_id
        assert "username" in data

    def test_auth_telegram_new_user(self, client):
        """
        POST /api/v1/auth/telegram с новым telegram_id
        должен создать пользователя и вернуть токен + профиль.
        """
        payload = {
            "telegram_id": 123456789,
            "username": "test_user",
        }
        data = self._register(client, payload)

        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
        assert data["token_type"] == "bearer"

        # Переданный username сохраняется
        self._assert_user_fields(data, 123456789)
        assert data["username"] == "test_user"

    def test_auth_telegram_default_username(self, client):
        """
        Если username не передан — backend подставляет str(telegram_id).
        """
        data = self._register(client, {"telegram_id": 555666777})
        self._assert_user_fields(data, 555666777)
        assert data["username"] == "555666777"

    def test_auth_telegram_login_updates_username(self, client):
        """
        Логин с переданным username обновляет сохранённое значение.
        """
        # Создание без username -> username = str(telegram_id)
        data1 = self._register(client, {"telegram_id": 777888999})
        assert data1["username"] == "777888999"

        data2 = self._register(
            client,
            {
                "telegram_id": 777888999,
                "username": "new_nickname"
            },
        )
        assert data2["username"] == "new_nickname"

    def test_auth_telegram_invalid_payload(self, client):
        """
        Без telegram_id должен вернуть 422 Validation Error.
        """
        payload = {"username": "no_id_user"}
        response = client.post("/api/v1/auth/telegram", json=payload)
        assert response.status_code == 422
