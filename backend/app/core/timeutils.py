"""Утилиты для работы со временем (всегда UTC)."""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """
    Текущее время в UTC без tzinfo.

    Используется «наивный» UTC, чтобы корректно работать и с SQLite
    (тесты), и с PostgreSQL: сравнение/хранение дат не зависит от того,
    возвращает ли драйвер aware- или naive-объекты datetime.
    """

    return datetime.now(timezone.utc).replace(tzinfo=None)
