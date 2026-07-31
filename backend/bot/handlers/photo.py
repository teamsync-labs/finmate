from aiogram import F, Router
from aiogram.types import Message
from services.api_client import send_photo
import os

router_photo = Router()

@router_photo.message(F.photo)
async def get_photo(message: Message):
    photo = message.photo[-1]
    await message.answer("Получил фото, обрабатываю")

    os.makedirs("downloads", exist_ok=True)
    path = f"downloads/{photo.file_id}.jpg"
    await message.bot.download(photo, destination=path)

    try:
        response = await send_photo(path)
        print(f"Ответ backend: {response.status_code}")
    except Exception as e:
        print(f"Ошибка при отправке на backend: {e}")