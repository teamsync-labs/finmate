from aiogram import F, Router
from aiogram.types import Message

from services.api_client import send_text

router_text = Router()


@router_text.message(F.text & ~F.text.startswith("/"))
async def get_text(message: Message):
    text = message.text
    await message.answer("Получил текстовое, обрабатываю")

    try:
        response = await send_text(text)
        print(f"Ответ backend: {response.status_code}")
    except Exception as e:
        print(f"Ошибка при отправке на backend: {e}")