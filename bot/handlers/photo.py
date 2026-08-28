from aiogram import F, Router
from aiogram.types import Message

from services.api_client import send_photo

router_photo = Router()


@router_photo.message(F.photo)
async def get_photo(message: Message):
    photo = message.photo[-1]
    await message.answer("Получил фото, обрабатываю")

    file_bytes = await message.bot.download(photo)

    try:
        response = await send_photo(file_bytes)
        print(f"Ответ backend: {response.status_code}")
    except Exception as e:
        print(f"Ошибка при отправке на backend: {e}")