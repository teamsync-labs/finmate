import os
from dotenv import load_dotenv

from bot_constants import (
    BACKUP_URL, LOCAL_OLLAMA_MODEL
)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", 'default_token')
PROXY = os.getenv("PROXY", "false").lower() in (
    "1", "true",
    "yes", "on"
)
TELEGRAM_PROXY = os.getenv("TELEGRAM_PROXY", None)

OLLAMA_API_URL = os.getenv("OLLAMA_API_URL") or BACKUP_URL
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL") or LOCAL_OLLAMA_MODEL
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
