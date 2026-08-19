user_tokens: dict[int, str] = {}

def save_token(telegram_id: int, token: str) -> None:
    user_tokens[telegram_id] = token


def get_token(telegram_id: int) -> str | None:
    return user_tokens.get(telegram_id)