import os

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if TOKEN is None:
    raise ValueError("TELEGRAM_BOT_TOKEN не найден в .env")

TELEGRAM_PROXY = os.getenv("TELEGRAM_PROXY", "")

BASE_URL = os.getenv("BASE_URL", "http://localhost:8088")

SERVICE_KEY = os.getenv("BOT_SERVICE_KEY", "")

# Таймаут запросов бота к backend (сек). Должен быть больше, чем
# YANDEX_AI_TIMEOUT_SECONDS на backend (60с), иначе бот будет отваливаться
# по таймауту, пока backend ждёт ответ YandexGPT.
HTTP_TIMEOUT = float(os.getenv("BOT_HTTP_TIMEOUT", "90"))

VOICE_ENDPOINT = f"{BASE_URL}/api/v1/transactions/voice"
PHOTO_ENDPOINT = f"{BASE_URL}/api/v1/transactions/photo"
TEXT_ENDPOINT = f"{BASE_URL}/api/v1/transactions/text"

AUTH_ENDPOINT = f"{BASE_URL}/api/v1/auth/telegram"

REPORT_ENDPOINT = f"{BASE_URL}/api/v1/reports"

CONSENT_PUBLIC_BASE = os.getenv("CONSENT_PUBLIC_BASE", "").rstrip("/")
if not CONSENT_PUBLIC_BASE.startswith(("http://", "https://")):
    raise ValueError(
        "CONSENT_PUBLIC_BASE не задан или некорректен в .env: нужен полный URL, "
        "например https://consent.geek-tik.tech/t/finmate"
    )
POLICY_URL = f"{CONSENT_PUBLIC_BASE}/policy"
PDN_CONSENT_URL = f"{CONSENT_PUBLIC_BASE}/pdn-consent"
