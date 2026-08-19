from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from services.api_client import authorize_user
from services.token_storage import save_token

router_start = Router()


@router_start.message(Command("start"))
async def cmd_start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Авторизоваться", callback_data="authorize")]
    ])
    await message.answer(
        "Привет! Я помогу вести учёт трат.\n\n"
        "Нажми кнопку ниже, чтобы начать:",
        reply_markup=keyboard
    )


@router_start.callback_query(F.data == "authorize")
async def process_authorize(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    username = callback.from_user.username

    try:
        response = await authorize_user(telegram_id, username)
        access_token = response.json()["access_token"]
        save_token(telegram_id, access_token)
        await callback.message.answer("Авторизация прошла успешно!")
    except Exception as e:
        print(f"Ошибка авторизации: {e}")
        await callback.message.answer("Не удалось авторизоваться, попробуйте позже")

    await callback.answer()