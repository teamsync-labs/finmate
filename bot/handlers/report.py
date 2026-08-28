from datetime import date

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback

from services.date_storage import pop_start_date, save_start_date

router_report = Router()


@router_report.message(Command("report"))
async def cmd_report(message: Message):
    await message.answer(
        "Выберите начальную дату:",
        reply_markup=await SimpleCalendar(locale='ru_RU').start_calendar()
    )


@router_report.callback_query(SimpleCalendarCallback.filter())
async def process_calendar_selection(callback_query: CallbackQuery, callback_data: dict):
    calendar = SimpleCalendar(locale='ru_RU')
    selected, selected_date = await calendar.process_selection(callback_query, callback_data)

    if selected:
        telegram_id = callback_query.from_user.id
        start_date = pop_start_date(telegram_id)

        if start_date is None:
            save_start_date(telegram_id, selected_date.strftime("%Y-%m-%d"))
            await callback_query.message.answer(
                "Теперь выберите конечную дату:",
                reply_markup=await SimpleCalendar(locale='ru_RU').start_calendar()
            )
        else:
            end_date = selected_date.strftime("%Y-%m-%d")
            await callback_query.message.answer(
                f"Период выбран: с {start_date} по {end_date}"
            )