from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router_start = Router()

@router_start.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
    "Привет! Я помогу вести учёт трат.\n\n"
    "Просто отправь мне:\n"
    "🎤 голосовое сообщение с описанием траты\n"
    "📷 фото чека\n"
    "✍️ или напиши текстом")