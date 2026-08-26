pending_start_dates: dict[int, str] = {}

def save_start_date(telegram_id: int, date_str: str) -> None:
    pending_start_dates[telegram_id] = date_str


def pop_start_date(telegram_id: int) -> str | None:
    return pending_start_dates.pop(telegram_id, None)