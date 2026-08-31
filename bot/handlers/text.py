from aiogram import F, Router
from aiogram.types import Message

from services.api_client import format_transaction, send_text

router_text = Router()


@router_text.message(F.text & ~F.text.startswith("/"))
async def get_text(message: Message):
    text = message.text
    await message.answer("Получил текстовое, обрабатываю")

    try:
        response = await send_text(text, message.from_user.id)
        print(f"Ответ backend: {response.status_code}")
        if response.status_code == 200:
            await message.answer(format_transaction(response.json()))
        elif response.status_code == 502:
            await message.answer(
                "Сервис распознавания временно недоступен. Попробуйте позже."
            )
        else:
            await message.answer(
                "Не удалось распознать расход. Попробуйте ещё раз."
            )
    except Exception as e:
        print(f"Ошибка при отправке на backend: {type(e).__name__}: {e}")
        await message.answer("Что-то пошло не так. Попробуйте позже.")
