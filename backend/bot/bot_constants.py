"""Constants for the bot."""

BACKUP_URL = "http://localhost:11434"
TELEGRAM_AUTH_URL = "/api/v1/auth/telegram"
EXPENSES_URL = "/api/v1/expenses"
LOCAL_OLLAMA_MODEL = "gemma3:4b"
MAX_RETRIES = 10
DB_FIELD_EXPENSE = {
    "expense_name": "Название",
    "amount": "Сумма",
    "type": "Категория",
    "currency": "Валюта",
}
VALID_EXPENSE_TYPES = (
    "general", "food", "transport", "housing", "utilities",
    "entertainment", "health", "education", "shopping", "other",
)

SYSTEM_PROMPT = (
    "Ты — финансовый помощник. Помогаешь вести учёт трат: "
    "распознаёшь расходы из фото чеков и текстовых сообщений, "
    "выделяешь категории и суммы, отвечаешь кратко и по делу."
    "Учитывай что пользователь может присылать текст с опечатками, "
    "поэтому исправляй их и понимай смысл сообщения."
)
PROMPT_EXPENSE = (
    "Распознай текст и выдели из него данные о расходах. "
    "Выведи результат в формате JSON с полями: "
    "expense_name (Название), amount (Сумма), "
    "type (Категория: " + ", ".join(VALID_EXPENSE_TYPES) + "), "
    "currency (Валюта, 3 буквы, по умолчанию RUB). "
    "Только JSON, без пояснений и markdown."
)
