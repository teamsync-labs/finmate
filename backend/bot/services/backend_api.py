"""HTTP-клиент к бэкенду FinSight API."""

import httpx

from bot_constants import EXPENSES_URL, TELEGRAM_AUTH_URL
from config import BACKEND_URL

client = httpx.AsyncClient(base_url=BACKEND_URL, timeout=10.0)


async def auth_telegram(
    telegram_id: int,
    username: str | None = None,
) -> dict:
    """Регистрация/вход пользователя: создаёт юзера, если его ещё нет."""
    response = await client.post(
        TELEGRAM_AUTH_URL,
        json={
            "telegram_id": telegram_id,
            "username": username,
        },
    )
    response.raise_for_status()
    return response.json()


async def create_expense(telegram_id: int, data: dict) -> dict:
    """Создаёт запись о расходе для пользователя."""
    auth_data = await auth_telegram(telegram_id)
    token = auth_data["access_token"]
    response = await client.post(
        EXPENSES_URL,
        json=data,
        headers={"Authorization": f"Bearer {token}"},
    )
    response.raise_for_status()
    return response.json()


async def close() -> None:
    """Закрывает HTTP-клиент при завершении работы бота."""
    await client.aclose()
