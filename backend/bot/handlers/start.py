from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from services.backend_api import auth_telegram

router_start = Router()


@router_start.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Обрабатывает команду /start."""

    await message.answer(
        "Привет! Я помогу вести учёт трат.\n\n"
        "Просто отправь мне:\n"
        "голосовое сообщение с описанием траты\n"
        "фото чека\n"
        "или напиши текстом"
    )
    try:
        await auth_telegram(message.from_user.id)
    except Exception:
        await message.answer(
            "Произошла ошибка при регистрации/входе пользователя. "
            "Попробуйте ещё раз позже."
        )
