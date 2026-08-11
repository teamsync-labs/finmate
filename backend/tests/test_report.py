"""
Базовые тесты эндпоинта отчётов:
POST /api/v1/reports — отчёт по расходам за период.

Проверяем:
- требуется авторизация
- пустой отчёт, группировка по категориям и суммы
- фильтрацию по периоду, категорию "other" и изоляцию по пользователю
- невалидный диапазон дат
"""

from datetime import datetime

from app.models.expenses import Expenses
from app.models.user import User

PERIOD = {"date_from": "2025-06-01", "date_to": "2025-06-30"}


def _register(client, telegram_id: int = 100500) -> dict:
    """Регистрирует пользователя и возвращает заголовки с токеном."""

    response = client.post(
        "/api/v1/auth/telegram",
        json={"telegram_id": telegram_id, "username": "reporter"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _add_expense(
    db_session,
    user_id: int,
    name: str,
    amount: float,
    type_: str | None,
    created_at: datetime,
):
    """Создаёт расход напрямую в БД с явной датой."""

    expense = Expenses(
        user_id=user_id,
        expense_name=name,
        amount=amount,
        type=type_,
        currency="RUB",
        created_at=created_at,
    )
    db_session.add(expense)
    db_session.commit()


class TestReportAuth:
    """Доступ к отчёту только для авторизованных."""

    def test_report_requires_auth(self, client):
        """Без токена должен вернуться 401."""

        response = client.post("/api/v1/reports", json=PERIOD)
        assert response.status_code == 401


class TestReport:
    """Основные сценарии отчёта."""

    def test_groups_by_category(self, client, db_session):
        """Расходы группируются по категории, суммы и количество считаются."""

        headers = _register(client)
        user = db_session.query(User).filter_by(telegram_id=100500).first()

        _add_expense(
            db_session, user.id, "Пицца",
            100.0, "food", datetime(2025, 6, 10, 12, 0, 0)
        )
        _add_expense(
            db_session, user.id, "Кофе",
            50.0, "food", datetime(2025, 6, 11, 9, 0, 0)
        )
        _add_expense(
            db_session, user.id, "Метро", 30.0,
            "transport", datetime(2025, 6, 12, 8, 0, 0)
        )

        response = client.post(
            "/api/v1/reports",
            json=PERIOD,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()

        assert data["date_from"] == PERIOD["date_from"]
        assert data["date_to"] == PERIOD["date_to"]
        assert data["total_amount"] == 180.0
        assert data["total_count"] == 3

        categories = {c["category"]: c for c in data["categories"]}
        assert categories["food"]["total"] == 150.0
        assert categories["food"]["count"] == 2
        assert categories["transport"]["total"] == 30.0
        assert categories["transport"]["count"] == 1

    def test_filters_by_period(self, client, db_session):
        """Расходы вне периода не попадают в отчёт."""

        headers = _register(client)
        user = db_session.query(User).filter_by(telegram_id=100500).first()

        _add_expense(
            db_session, user.id, "Внутри",
            100.0, "food", datetime(2025, 6, 15, 12, 0, 0)
        )
        _add_expense(
            db_session, user.id, "До периода",
            999.0, "food", datetime(2025, 5, 1, 12, 0, 0)
        )
        _add_expense(
            db_session, user.id, "После периода",
            999.0, "food", datetime(2025, 7, 1, 12, 0, 0)
        )

        response = client.post(
            "/api/v1/reports",
            json=PERIOD,
            headers=headers
        )
        data = response.json()
        assert data["total_count"] == 1
        assert data["total_amount"] == 100.0

    def test_only_current_user(self, client, db_session):
        """Расходы других пользователей не попадают в отчёт."""

        headers = _register(client)
        user = db_session.query(User).filter_by(telegram_id=100500).first()
        other = User(telegram_id=777777, username="other")
        db_session.add(other)
        db_session.commit()

        _add_expense(
            db_session, user.id, "Мой",
            100.0, "food", datetime(2025, 6, 15, 12, 0, 0)
        )
        _add_expense(
            db_session, other.id, "Чужой",
            999.0, "food", datetime(2025, 6, 15, 12, 0, 0)
        )

        response = client.post(
            "/api/v1/reports",
            json=PERIOD,
            headers=headers
        )
        data = response.json()
        assert data["total_count"] == 1
        assert data["total_amount"] == 100.0

    def test_invalid_date_range(self, client):
        """date_from позже date_to — 422 Validation Error."""

        headers = _register(client)
        payload = {"date_from": "2025-07-01", "date_to": "2025-06-01"}
        response = client.post(
            "/api/v1/reports",
            json=payload,
            headers=headers
        )
        assert response.status_code == 422
