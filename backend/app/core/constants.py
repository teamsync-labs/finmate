"""Константы приложения FinSight."""

# Валюты и язык по умолчанию
DEFAULT_CURRENCY = "RUB"
DEFAULT_LANGUAGE = "ru"

# Типы расходов
DEFAULT_EXPENSE_TYPE = "general"
VALID_EXPENSE_TYPES = frozenset({
    "general", "food", "transport",
    "housing", "utilities", "entertainment",
    "health", "education", "shopping", "other",
})
EXPENSE_TYPE_CHOICES = (
    ("general", "Общее"),
    ("food", "Продукты"),
    ("transport", "Транспорт"),
    ("housing", "Жильё"),
    ("utilities", "Коммунальные"),
    ("entertainment", "Развлечения"),
    ("health", "Здоровье"),
    ("education", "Образование"),
    ("shopping", "Покупки"),
    ("other", "Другое"),
)

# Типы счетов
VALID_ACCOUNT_TYPES = frozenset({
    "cash", "bank",
    "credit", "investment",
    "savings",
})

# Категория для расходов без типа
UNCATEGORIZED_CATEGORY = "other"

# Ограничения длины полей
MAX_EXPENSE_NAME_LENGTH = 100
MAX_EXPENSE_TYPE_LENGTH = 20
MAX_CURRENCY_CODE_LENGTH = 3
MAX_USERNAME_LENGTH = 255
MAX_TOKEN_HASH_LENGTH = 64

# Размеры токенов
REFRESH_TOKEN_BYTES = 48
ACCESS_TOKEN_JTI_BYTES = 16

# HTTP-аутентификация
AUTH_SCHEME_BEARER = "Bearer"
WWW_AUTHENTICATE_HEADER = "WWW-Authenticate"

# Админ-панель
ADMIN_SESSION_TOKEN = "admin_session_token"
ADMIN_BASE_URL = "/admin"
ADMIN_TITLE = "FinSight Admin"

# Приложение
APP_VERSION = "1.0.0"
APP_CONTACT_NAME = "Команда FinSight"
APP_CONTACT_EMAIL = "dev@finsight.example.com"
