import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession

from config import TELEGRAM_PROXY, TOKEN
from handlers import router_start, router_voice, router_photo, router_text, router_report


async def main():
    session = AiohttpSession(proxy=TELEGRAM_PROXY) if TELEGRAM_PROXY else None
    bot = Bot(token=TOKEN, session=session)
    dp = Dispatcher()

    dp.include_router(router_start)
    dp.include_router(router_voice)
    dp.include_router(router_photo)
    dp.include_router(router_text)
    dp.include_router(router_report)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())