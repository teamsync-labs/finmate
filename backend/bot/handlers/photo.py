from io import BytesIO
import logging

from aiogram import F, Router
from aiogram.types import Message

from services.expenses import handle_expense
from services.llm import process_photo

logger = logging.getLogger(__name__)
router_photo = Router()


@router_photo.message(F.photo)
async def get_photo(message: Message) -> None:
    photo = message.photo[-1]
    await message.answer("Получил фото, обрабатываю")
    buffer = BytesIO()
    try:
        await message.bot.download(photo, destination=buffer)
        buffer.seek(0)
        filename = f"{photo.file_id}.jpg"
        await handle_expense(
            message,
            lambda prompt: process_photo(
                buffer,
                filename=filename,
                prompt=prompt
            ),
        )
    except Exception:
        logger.exception(
            "Ошибка обработки фото: %s",
            photo.file_id
        )
        await message.answer(
            "Не удалось обработать фото, попробуй ещё раз."
        )
