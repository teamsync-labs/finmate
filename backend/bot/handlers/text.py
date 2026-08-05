import logging

from aiogram import F, Router
from aiogram.types import Message

from services.expenses import handle_expense
from services.llm import process_text

logger = logging.getLogger(__name__)
router_text = Router()


@router_text.message(F.text & ~F.text.startswith("/"))
async def get_text(message: Message) -> None:
    await message.answer("Получил текстовое, обрабатываю")
    try:
        await handle_expense(
            message,
            lambda prompt: process_text(
                f"{prompt}\n\nСообщение пользователя:\n{message.text}"
            ),
        )
    except Exception as e:
        logger.exception("Ошибка обработки текста: %s", e)
        await message.answer(
            "Не удалось обработать сообщение, попробуй ещё раз."
        )
