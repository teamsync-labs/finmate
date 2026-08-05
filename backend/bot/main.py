import asyncio
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher

from config import TOKEN, PROXY, TELEGRAM_PROXY
from handlers import (
    router_start, router_voice,
    router_photo, router_text
)
from services import backend_api, llm


@asynccontextmanager
async def lifespan(dispatcher: Dispatcher):
    """Закрывает HTTP-клиенты при завершении работы бота."""

    yield
    await backend_api.close()
    await llm.close()


async def main() -> None:
    """Главная корутинная функция для запуска бота."""

    proxy = TELEGRAM_PROXY if (PROXY and TELEGRAM_PROXY) else None
    bot = Bot(token=TOKEN, proxy=proxy)
    dp = Dispatcher(lifespan=lifespan)

    dp.include_router(router_start)
    dp.include_router(router_voice)
    dp.include_router(router_photo)
    dp.include_router(router_text)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
