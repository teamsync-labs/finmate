"""Эндпоинты разбора транзакций: voice / photo / text.

Все три принимают авторизованный запрос (JWT Bearer для внешних
клиентов либо X-Service-Key + X-Telegram-Id для бота) и возвращают
единый ParsedTransaction. Распознанный расход с суммой сразу
сохраняется в БД (таблица expenses), а в ответе возвращается его id
(поле expense_id).
"""

from __future__ import annotations

import logging

import httpx
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)

from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.constants import MAX_EXPENSE_NAME_LENGTH
from app.core.security import get_current_user
from app.models.expenses import Expenses
from app.models.user import User
from app.schemas.transaction import (
    ParsedTransaction, TextTransactionRequest
)
from app.services.transactions import (
    process_photo,
    process_text,
    process_voice,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/transactions", tags=["Transactions"])


async def _read_limited(file: UploadFile) -> bytes:
    """Читает файл с защитой от гигантских загрузок (413)."""

    data = await file.read(settings.MAX_UPLOAD_BYTES + 1)
    if len(data) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large",
        )
    return data


async def _run_ai(coro):
    """
    Выполняет вызов к AI-цепочке и маппит ошибки в HTTP-статусы.

    Ошибки сети/API Yandex → 502, не-JSON от LLM → 422.
    Реальная причина (401/403/квота и т.п.) пишется в логи backend,
    чтобы 502 можно было диагностировать.
    """

    try:
        return await coro
    except httpx.HTTPError as exc:
        logger.exception("AI service error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service is unavailable, please retry later",
        ) from exc
    except ValueError as exc:
        logger.warning("Invalid AI response: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


def _expense_name(parsed: ParsedTransaction) -> str:
    """Формирует название расхода из результата разбора.

    Приоритет: merchant → raw_summary → общая заглушка.
    """

    name = (parsed.merchant or parsed.raw_summary or "Расход").strip()
    return name[:MAX_EXPENSE_NAME_LENGTH]


def _save_parsed(
    db: Session, user_id: int, parsed: ParsedTransaction
) -> int | None:
    """Сохраняет распознанный расход в БД.

    Если сумма не распознана (amount is None), сохранять нечего —
    возвращается None, и в ответе expense_id останется null.
    """

    if parsed.amount is None:
        return None

    expense = Expenses(
        user_id=user_id,
        expense_name=_expense_name(parsed),
        amount=parsed.amount,
        type=parsed.category,
        currency=parsed.currency,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense.id


@router.post("/voice", response_model=ParsedTransaction)
async def parse_voice(
    voice: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Распознать голосовое сообщение → расход (и сохранить в БД)."""

    data = await _read_limited(voice)
    parsed = await _run_ai(process_voice(data))
    return parsed.model_copy(
        update={"expense_id": _save_parsed(db, current_user.id, parsed)}
    )


@router.post("/photo", response_model=ParsedTransaction)
async def parse_photo(
    photo: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Распознать фото чека → расход (и сохранить в БД)."""

    data = await _read_limited(photo)
    parsed = await _run_ai(process_photo(data))
    return parsed.model_copy(
        update={"expense_id": _save_parsed(db, current_user.id, parsed)}
    )


@router.post("/text", response_model=ParsedTransaction)
async def parse_text(
    payload: TextTransactionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Разобрать текстовое описание → расход (и сохранить в БД)."""

    parsed = await _run_ai(process_text(payload.text))
    return parsed.model_copy(
        update={"expense_id": _save_parsed(db, current_user.id, parsed)}
    )
