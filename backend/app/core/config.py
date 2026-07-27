from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "FinSight API"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "sqlite:///./finsight.db"

    SECRET_KEY: str = "super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    CORS_ORIGINS: list[str] = [
        "http://localhost:8000",
        "http://localhost:5173",
    ]

    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()


if (
    not settings.SECRET_KEY
    or settings.SECRET_KEY == "super-secret-key-change-in-production"
):
    import warnings
    warnings.warn(
        "SECRET_KEY is not changed! Set a strong SECRET_KEY"
        " via .env or environment variables.",
        UserWarning,
        stacklevel=1,
    )
