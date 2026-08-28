from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import PDN_CONSENT_URL, POLICY_URL

router_start = Router()


@router_start.message(Command("start"))
async def cmd_start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Политика конфиденциальности", url=POLICY_URL)],
        [InlineKeyboardButton(text="Принимаю", callback_data="accept_policy")],
        [InlineKeyboardButton(text="Не принимаю", callback_data="decline_policy")]
    ])
    await message.answer(
        "FinMate — помощник по учёту расходов.\n\n"
        "Пришлите голосовое, фото чека или текст с суммой — сохраним данные о покупке.\n\n"
        "Политика конфиденциальности — по кнопке ниже. Нажимая «Принимаю», вы подтверждаете, что ознакомились с политикой.",
        reply_markup=keyboard
    )


@router_start.callback_query(F.data == "accept_policy")
async def process_accept_policy(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Cогласие на обработку ПДн", url=PDN_CONSENT_URL)],
        [InlineKeyboardButton(text="Даю согласие", callback_data="accept_pdn")],
        [InlineKeyboardButton(text="Не даю согласие", callback_data="decline_pdn")]
    ])
    await callback.message.answer(
        "И последний шаг перед началом.\n\n"
        "Согласие на обработку персональных данных — текст по кнопке ниже.\n\n"
        "Нажимая «Даю согласие», вы даёте согласие на обработку персональных данных. Отозвать — /delete.\n\n",
        reply_markup=keyboard
    )
    await callback.answer()

@router_start.callback_query(F.data == "accept_pdn")
async def process_accept_pdn(callback: CallbackQuery):
    await callback.message.answer(
        "Пришлите голосовое о трате, фото чека или текст с суммой.\n\n"
        "Справка — /help, список за сегодня — /today."
    )
    await callback.answer()

@router_start.callback_query(F.data == "decline_policy")
async def process_decline_policy(callback: CallbackQuery):
    await callback.message.answer("Для использования бота нужно дать согласие на обработку персональных данных. Чтобы продолжить, нажмите /start.")
    await callback.answer()

@router_start.callback_query(F.data == "decline_pdn")
async def process_decline_pdn(callback: CallbackQuery):
    await callback.message.answer("Для использования бота нужно дать согласие на обработку персональных данных. Чтобы продолжить, нажмите /start.")
    await callback.answer()