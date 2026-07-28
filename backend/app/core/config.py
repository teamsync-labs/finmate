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
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

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
            return f"sqlite:///{BASE_DIR / 'finsight.db'}"
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
