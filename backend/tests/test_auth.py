"""
Тесты аутентификации:
- POST /api/v1/auth/telegram — регистрация/логин через Telegram
- POST /api/v1/auth/refresh — ротация refresh-токена
- POST /api/v1/auth/logout — отзыв refresh-токена
"""

from datetime import timedelta

from app.core.security import hash_token
from app.core.timeutils import utcnow
from app.models.refresh_token import RefreshToken

AUTH_URL = "/api/v1/auth/telegram"
REFRESH_URL = "/api/v1/auth/refresh"
LOGOUT_URL = "/api/v1/auth/logout"


def _assert_auth_fields(data: dict, telegram_id: int) -> None:
    """Проверяет, что ответ содержит токены и базовые поля пользователя."""

    assert "access_token" in data
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0
    assert "refresh_token" in data
    assert isinstance(data["refresh_token"], str)
    assert len(data["refresh_token"]) > 0
    assert data["token_type"] == "bearer"
    assert data["telegram_id"] == telegram_id
    assert "username" in data


class TestAuthTelegram:
    """Эндпоинт аутентификации через Telegram."""

    def test_new_user(self, client, register_user):
        """Новый telegram_id — создание пользователя и выдача токенов."""

        data = register_user(123456789, username="test_user")

        _assert_auth_fields(data, 123456789)
        assert data["username"] == "test_user"

    def test_default_username(self, register_user):
        """Без username backend подставляет str(telegram_id)."""

        data = register_user(555666777)
        _assert_auth_fields(data, 555666777)
        assert data["username"] == "555666777"

    def test_login_updates_username(self, register_user):
        """Логин с username обновляет сохранённое значение."""

        data1 = register_user(777888999)
        assert data1["username"] == "777888999"

        data2 = register_user(777888999, username="new_nickname")
        assert data2["username"] == "new_nickname"

    def test_invalid_payload(self, client):
        """Без telegram_id — 422 Validation Error."""
        response = client.post(AUTH_URL, json={"username": "no_id_user"})
        assert response.status_code == 422


class TestRefreshToken:
    """Ротация сессии по refresh-токену."""

    def test_refresh_returns_new_token_pair(self, register_user, client):
        """Refresh возвращает новую пару токенов и отзывает старую."""

        auth = register_user(424242, username="refresh_user")

        response = client.post(
            REFRESH_URL,
            json={"refresh_token": auth["refresh_token"]},
        )
        assert response.status_code == 200
        data = response.json()

        _assert_auth_fields(data, 424242)
        assert data["refresh_token"] != auth["refresh_token"]

    def test_rotated_token_can_be_used_again(self, register_user, client):
        """Новая пара токенов снова работает для обновления."""

        auth = register_user(424242, username="refresh_user")

        first = client.post(
            REFRESH_URL,
            json={"refresh_token": auth["refresh_token"]},
        ).json()
        second = client.post(
            REFRESH_URL,
            json={"refresh_token": first["refresh_token"]},
        )
        assert second.status_code == 200
        assert second.json()["access_token"] != first["access_token"]

    def test_refreshed_access_token_works(self, register_user, client):
        """Access-токен из refresh-ответа авторизует защищённые роуты."""

        auth = register_user(424242, username="refresh_user")
        refreshed = client.post(
            REFRESH_URL,
            json={"refresh_token": auth["refresh_token"]},
        ).json()

        headers = {"Authorization": f"Bearer {refreshed['access_token']}"}
        response = client.get("/api/v1/expenses", headers=headers)
        assert response.status_code == 200

    def test_refresh_with_invalid_token(self, client):
        """Несуществующий refresh-токен — 401."""

        response = client.post(
            REFRESH_URL,
            json={"refresh_token": "definitely-not-a-real-token"},
        )
        assert response.status_code == 401

    def test_refresh_old_token_rejected_after_rotation(
        self, register_user, client
    ):
        """Старый токен после ротации использовать нельзя — 401."""

        auth = register_user(424242, username="refresh_user")

        response = client.post(
            REFRESH_URL,
            json={"refresh_token": auth["refresh_token"]},
        )
        assert response.status_code == 200

        reuse = client.post(
            REFRESH_URL,
            json={"refresh_token": auth["refresh_token"]},
        )
        assert reuse.status_code == 401

    def test_reuse_revokes_token_family(self, register_user, client):
        """Реплей отозванного токена отзывает всё семейство."""

        auth = register_user(424242, username="refresh_user")

        first = client.post(
            REFRESH_URL,
            json={"refresh_token": auth["refresh_token"]},
        )
        assert first.status_code == 200
        new_token = first.json()["refresh_token"]

        replay = client.post(
            REFRESH_URL,
            json={"refresh_token": auth["refresh_token"]},
        )
        assert replay.status_code == 401

        blocked = client.post(
            REFRESH_URL,
            json={"refresh_token": new_token},
        )
        assert blocked.status_code == 401

    def test_refresh_expired_token(self, register_user, client, db_session):
        """Просроченный refresh-токен — 401."""

        auth = register_user(424242, username="refresh_user")

        record = db_session.query(RefreshToken).filter(
            RefreshToken.token_hash == hash_token(auth["refresh_token"])
        ).one()
        record.expires_at = utcnow() - timedelta(minutes=1)
        db_session.commit()

        response = client.post(
            REFRESH_URL,
            json={"refresh_token": auth["refresh_token"]},
        )
        assert response.status_code == 401

    def test_refresh_missing_body(self, client):
        """Пустое тело запроса — 422 Validation Error."""

        response = client.post(REFRESH_URL, json={})
        assert response.status_code == 422


class TestLogout:
    """Выход из аккаунта по refresh-токену."""

    def test_logout_revokes_refresh_token(self, register_user, client):
        """После logout обновление сессии по старому токену — 401."""

        refresh_token = register_user(
            515151, username="leaver"
        )["refresh_token"]

        logout = client.post(
            LOGOUT_URL,
            json={"refresh_token": refresh_token},
        )
        assert logout.status_code == 204

        refresh = client.post(
            REFRESH_URL,
            json={"refresh_token": refresh_token},
        )
        assert refresh.status_code == 401

    def test_logout_with_invalid_token(self, client):
        """Logout с несуществующим токеном не падает с ошибкой."""

        response = client.post(
            LOGOUT_URL,
            json={"refresh_token": "no-such-token"},
        )
        assert response.status_code == 204
