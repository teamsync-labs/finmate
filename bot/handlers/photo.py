from aiogram import F, Router
from aiogram.types import Message

from services.api_client import format_transaction, send_photo

router_photo = Router()


@router_photo.message(F.photo)
async def get_photo(message: Message):
    photo = message.photo[-1]
    await message.answer("Получил фото, обрабатываю")

    file_bytes = await message.bot.download(photo)

    try:
        response = await send_photo(file_bytes, message.from_user.id)
        print(f"Ответ backend: {response.status_code}")
        if response.status_code == 200:
            await message.answer(format_transaction(response.json()))
        elif response.status_code == 502:
            await message.answer(
                "Сервис распознавания временно недоступен. Попробуйте позже."
            )
        else:
            await message.answer(
                "Не удалось распознать чек. Попробуйте ещё раз."
            )
    except Exception as e:
        print(f"Ошибка при отправке на backend: {type(e).__name__}: {e}")
        await message.answer("Что-то пошло не так. Попробуйте позже.")
