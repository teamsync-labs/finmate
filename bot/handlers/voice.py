from aiogram import F, Router
from aiogram.types import Message

from services.api_client import send_voice

router_voice = Router()


@router_voice.message(F.voice)
async def get_voice(message: Message):
    voice = message.voice
    await message.answer("Получил голосовое, обрабатываю")

    file_bytes = await message.bot.download(voice)

    try:
        response = await send_voice(file_bytes)
        print(f"Ответ backend: {response.status_code}")
    except Exception as e:
        print(f"Ошибка при отправке на backend: {e}")