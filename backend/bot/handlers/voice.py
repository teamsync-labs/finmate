from aiogram import F, Router
from aiogram.types import Message
from services.api_client import send_voice
import os

router_voice = Router()

@router_voice.message(F.voice)
async def get_voice(message: Message):
    voice = message.voice
    await message.answer("Получил голосовое, обрабатываю")

    os.makedirs("downloads", exist_ok=True)
    path = f"downloads/{voice.file_id}.ogg"
    await message.bot.download(voice, destination=path)

    try:
        response = await send_voice(path)
        print(f"Ответ backend: {response.status_code}")
    except Exception as e:
        print(f"Ошибка при отправке на backend: {e}")