import logging
from io import BytesIO

from aiogram import F, Router
from aiogram.types import Message

from services.llm import process_voice

logger = logging.getLogger(__name__)
router_voice = Router()


@router_voice.message(F.voice)
async def get_voice(message: Message) -> None:
    voice = message.voice
    await message.answer("Получил голосовое, обрабатываю")
    buffer = BytesIO()
    try:
        await message.bot.download(voice, destination=buffer)
        buffer.seek(0)
        result = await process_voice(
            buffer,
            filename=f"{voice.file_id}.ogg",
        )
        await message.answer(result)
    except Exception as e:
        logger.exception("Ошибка обработки голосового: %s", e)
        await message.answer(
            "Не удалось обработать голосовое, попробуй ещё раз."
        )
