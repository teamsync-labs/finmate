import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    APP_NAME: str = "FinSight API"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: Optional[str] = None

    POSTGRES_USER: str = "finsight"
    POSTGRES_PASSWORD: str = "finsight"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "finsight"

    SECRET_KEY: str = "super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    # Продление сессии — только через refresh-токен.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # Время жизни refresh-токена (по умолчанию 30 дней)
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30

    BOT_SERVICE_KEY: str = os.getenv(
        'BOT_SERVICE_KEY',
        ''
    )

    YANDEX_FOLDER_ID: str = os.getenv('YANDEX_FOLDER_ID', '')
    YANDEX_API_KEY: str = os.getenv('YANDEX_API_KEY', '')
    YANDEX_GPT_MODEL: str = os.getenv('YANDEX_GPT_MODEL', 'yandexgpt/latest')
    YANDEX_OCR_URL: str = os.getenv(
        'YANDEX_OCR_URL',
        'https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText',
    )
    YANDEX_LLM_URL: str = os.getenv(
        'YANDEX_LLM_URL',
        'https://llm.api.cloud.yandex.net/v1/chat/completions',
    )
    YANDEX_STT_URL: str = os.getenv(
        'YANDEX_STT_URL',
        'https://stt.api.cloud.yandex.net/speech/v1/stt:recognize',
    )
    YANDEX_AI_TIMEOUT_SECONDS: float = float(
        os.getenv('YANDEX_AI_TIMEOUT_SECONDS', '60.0')
    )
    MAX_UPLOAD_BYTES: int = int(
        os.getenv('MAX_UPLOAD_BYTES', str(10 * 1024 * 1024))
    )

    # Локальная Ollama — используется в dev-режиме (DEBUG=True)
    # вместо Yandex Cloud: llm_chat → OLLAMA_MODEL, OCR → OLLAMA_OCR_MODEL.
    # В Docker вместо localhost используйте http://host.docker.internal:11434.
    OLLAMA_BASE_URL: str = os.getenv(
        'OLLAMA_BASE_URL',
        'http://localhost:11434',
    )
    OLLAMA_MODEL: str = os.getenv('OLLAMA_MODEL', 'gemma3:4b')
    OLLAMA_OCR_MODEL: str = os.getenv('OLLAMA_OCR_MODEL', 'llava')
    OLLAMA_TgIMEOUT_SECONDS: float = float(
        os.getenv('OLLAMA_TIMEOUT_SECONDS', '120.0')
    )

    ADMIN_USERNAME: str = os.getenv(
        'ADMIN_USERNAME',
        'admin'
    )
    ADMIN_PASSWORD: str = os.getenv(
        'ADMIN_PASSWORD',
        'admin123'
    )

    CORS_ORIGINS: list[str] = [
        "http://localhost:8000",
        "http://localhost:5173",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def effective_db_url(self) -> str:
        """Возвращает URL БД в зависимости от режима.

        Приоритет:
        1. DATABASE_URL (если явно задан) — полный контроль
        2. DEBUG=True  → SQLite (локальная разработка)
        3. DEBUG=False → PostgreSQL (продакшен / Docker)
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL
        if self.DEBUG:
            return "sqlite:///" + str(BASE_DIR / "finsight.db")
        return "postgresql://{user}:{password}@{host}:{port}/{db}".format(
            user=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            db=self.POSTGRES_DB,
        )


settings = Settings()
