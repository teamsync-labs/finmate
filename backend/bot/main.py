from aiogram import Bot, Dispatcher
import asyncio
from config import TOKEN
from handlers import router_start, router_voice, router_photo, router_text

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    dp.include_router(router_start)
    dp.include_router(router_voice)
    dp.include_router(router_photo)
    dp.include_router(router_text)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())