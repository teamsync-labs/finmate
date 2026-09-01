import httpx

from config import (
    AUTH_ENDPOINT,
    HTTP_TIMEOUT,
    PHOTO_ENDPOINT,
    REPORT_ENDPOINT,
    SERVICE_KEY,
    TEXT_ENDPOINT,
    VOICE_ENDPOINT,
)


def _headers(telegram_id: int) -> dict[str, str]:
    """Заголовки сервисной авторизации для backend.

    Backend (app.core.security.get_current_user) принимает
    X-Service-Key + X-Telegram-Id от бота вместо JWT.
    """

    return {
        "X-Service-Key": SERVICE_KEY,
        "X-Telegram-Id": str(telegram_id),
    }


async def register_user(telegram_id: int, username: str | None = None):
    """Регистрирует пользователя на backend после принятия соглашений.

    POST /api/v1/auth/telegram создаёт пользователя, если он ещё не
    существует, и возвращает пару токенов (access + refresh).
    """

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        response = await client.post(
            AUTH_ENDPOINT,
            json={"telegram_id": telegram_id, "username": username},
        )
    return response


async def send_voice(file, telegram_id: int):
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        response = await client.post(
            VOICE_ENDPOINT,
            files={"voice": file},
            headers=_headers(telegram_id),
        )
    return response


async def send_photo(file, telegram_id: int):
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        response = await client.post(
            PHOTO_ENDPOINT,
            files={"photo": file},
            headers=_headers(telegram_id),
        )
    return response


async def send_text(text: str, telegram_id: int):
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        response = await client.post(
            TEXT_ENDPOINT,
            json={"text": text},
            headers=_headers(telegram_id),
        )
    return response


def format_transaction(data: dict) -> str:
    """Форматирует ParsedTransaction из backend в читаемое сообщение."""

    amount = data.get("amount")
    merchant = data.get("merchant")
    items = data.get("items") or []
    summary = data.get("raw_summary")
    category = data.get("category")

    # Распознать ничего не удалось (суммы нет, остальное пустое).
    # Не показываем бессмысленное «Категория: general» — лучше честно
    # сообщить об ошибке распознавания.
    if amount is None and not merchant and not items and not summary:
        return "Не удалось распознать расход. Попробуйте ещё раз."

    lines = []
    if amount is not None:
        lines.append(f"Сумма: {amount} {data.get('currency', 'RUB')}")
    if merchant:
        lines.append(f"Место: {merchant}")
    if category:
        lines.append(f"Категория: {category}")
    if items:
        lines.append("Позиции: " + ", ".join(items))
    if summary:
        lines.append(f"{summary}")

    if data.get("expense_id") is not None:
        lines.append("Сохранено в вашем учёте.")
    return "\n".join(lines)


async def get_report(date_from: str, date_to: str, token: str):
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        response = await client.post(
            REPORT_ENDPOINT,
            json={"date_from": date_from, "date_to": date_to},
            headers={"Authorization": f"Bearer {token}"}
        )
    return response
