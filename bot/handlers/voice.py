from aiogram import F, Router
from aiogram.types import Message

from services.api_client import format_transaction, send_voice

router_voice = Router()


@router_voice.message(F.voice)
async def get_voice(message: Message):
    voice = message.voice
    await message.answer("Получил голосовое, обрабатываю")

    file_bytes = await message.bot.download(voice)

    try:
        response = await send_voice(file_bytes, message.from_user.id)
        print(f"Ответ backend: {response.status_code}")
        if response.status_code == 200:
            await message.answer(format_transaction(response.json()))
        elif response.status_code == 502:
            await message.answer(
                "Сервис распознавания временно недоступен. Попробуйте позже."
            )
        else:
            await message.answer(
                "Не удалось распознать голосовое. Попробуйте ещё раз."
            )
    except Exception as e:
        print(f"Ошибка при отправке на backend: {type(e).__name__}: {e}")
        await message.answer("Что-то пошло не так. Попробуйте позже.")
