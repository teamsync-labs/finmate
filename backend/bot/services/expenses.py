"""
services/expenses.py — распознавание расхода.
LLM → парсинг → retry → сохранение.
"""
from collections.abc import Awaitable, Callable

from aiogram.types import Message

from bot_constants import DB_FIELD_EXPENSE, MAX_RETRIES, PROMPT_EXPENSE
from services.backend_api import create_expense
from services.parser import formatting_values


async def recognize_expense(
    ask: Callable[[str], Awaitable[str]],
) -> dict | None:
    """
    Цикл: запрос к LLM → парсинг.

    При ошибке повторный запрос на исправление.
    """

    raw = await ask(PROMPT_EXPENSE)
    data = formatting_values(raw)

    for _ in range(MAX_RETRIES):
        if data is not False:
            break
        raw = await ask(
            "Ты вернул некорректный JSON. Вот твой предыдущий ответ:\n"
            f"{raw}\n\n"
            "Исправь ошибки и выдай ТОЛЬКО исправленный JSON "
            f"с полями: {', '.join(DB_FIELD_EXPENSE.values())}."
        )
        data = formatting_values(raw)

    return data if data is not False else None


def format_expense(data: dict) -> str:
    """Форматирует данные расхода для ответа пользователю."""
    return "\n".join(
        f"{DB_FIELD_EXPENSE.get(key, key)}: {value}"
        for key, value in data.items()
    )


async def handle_expense(
    message: Message,
    ask: Callable[[str], Awaitable[str]],
) -> None:
    """Полный цикл: распознать → показать → сохранить."""
    data = await recognize_expense(ask)
    if data is None:
        await message.answer("Не удалось распознать данные, попробуй ещё раз.")
        return
    await message.answer(format_expense(data))
    await create_expense(
        message.from_user.id,
        data
    )
