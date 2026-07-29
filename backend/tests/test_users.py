"""
Минимальные тесты пользователей:
- GET /api/v1/users/me — получение профиля текущего пользователя
"""


class TestUsersMe:
    """Тесты эндпоинта получения профиля."""

    def _register_and_get_token(self, client, telegram_id: int) -> str:
        """Хелпер: регистрирует пользователя и возвращает токен."""
        payload = {"telegram_id": telegram_id}
        response = client.post("/api/v1/auth/telegram", json=payload)
        assert response.status_code == 200
        return response.json()["access_token"]

    def test_get_me_authenticated(self, client):
        """
        GET /api/v1/users/me с валидным токеном
        должен вернуть профиль пользователя.
        """
        token = self._register_and_get_token(client, 111222333)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 200
        data = response.json()

        assert data["telegram_id"] == 111222333
        assert "id" in data
        assert "created_at" in data

    def test_get_me_no_token(self, client):
        """
        GET /api/v1/users/me без токена
        должен вернуть 401 Unauthorized.
        """
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self, client):
        """
        GET /api/v1/users/me с невалидным токеном
        должен вернуть 401 Unauthorized.
        """
        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 401

    def test_get_me_returns_correct_user_data(self, client):
        """
        Проверяем, что /users/me возвращает данные
        того пользователя, чей токен используется.
        """
        # Создаём двух пользователей
        token1 = self._register_and_get_token(client, 100200300)
        token2 = self._register_and_get_token(client, 400500600)

        # Проверяем первого
        resp1 = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token1}"},
        )
        assert resp1.json()["telegram_id"] == 100200300

        # Проверяем второго
        resp2 = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert resp2.json()["telegram_id"] == 400500600
