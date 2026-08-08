from aiogram import F, Router
from aiogram.types import Message
from services.api_client import send_text
import os

router_text = Router()

@router_text.message(F.text & ~F.text.startswith("/"))
async def get_text(message: Message):
    text = message.text
    await message.answer("Получил текстовое, обрабатываю")

    os.makedirs("downloads", exist_ok=True)
    path = f"downloads/{message.message_id}.txt"
    with open(path, "w", encoding="utf-8") as file:
        file.write(text)

    try:
        response = await send_text(path)
        print(f"Ответ backend: {response.status_code}")
    except Exception as e:
        print(f"Ошибка при отправке на backend: {e}")