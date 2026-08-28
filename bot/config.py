import os

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if TOKEN is None:
    raise ValueError("TELEGRAM_BOT_TOKEN не найден в .env")

BASE_URL = os.getenv("BASE_URL", "http://localhost:8088")

VOICE_ENDPOINT = f"{BASE_URL}/api/v1/transactions/voice"
PHOTO_ENDPOINT = f"{BASE_URL}/api/v1/transactions/photo"
TEXT_ENDPOINT = f"{BASE_URL}/api/v1/transactions/text"

AUTH_ENDPOINT = f"{BASE_URL}/api/v1/auth/telegram"

REPORT_ENDPOINT = f"{BASE_URL}/api/v1/reports"

CONSENT_PUBLIC_BASE = os.getenv("CONSENT_PUBLIC_BASE", "")
POLICY_URL = f"{CONSENT_PUBLIC_BASE}/policy"
PDN_CONSENT_URL = f"{CONSENT_PUBLIC_BASE}/pdn-consent"