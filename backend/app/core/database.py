"""Database configuration and session management."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


def _get_connect_args() -> dict:
    """Возвращает аргументы подключения в зависимости от типа БД."""

    if settings.effective_db_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


engine = create_engine(
    settings.effective_db_url,
    connect_args=_get_connect_args(),
    pool_pre_ping=True,
    # Для PostgreSQL/MySQL можно настроить pool_size
    # pool_size=5, max_overflow=10  # если не SQLite
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependency для получения сессии БД."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
