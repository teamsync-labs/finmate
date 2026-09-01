from fastapi import (
    APIRouter, Depends
)
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.constants import UNCATEGORIZED_CATEGORY
from app.core.security import get_current_user
from app.models.user import User
from app.models.expenses import Expenses
from app.schemas.report import (
    CategoryReport,
    ReportExpenseItem,
    ReportRequest,
    ReportResponse,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("", response_model=ReportResponse)
def period_report(
    payload: ReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Отчёт по расходам за период.

    Принимает две даты (date_from, date_to) и возвращает перечень
    расходов текущего пользователя за этот период, сгруппированный
    и отсортированный по категориям.
    """

    expenses = (
        db.query(Expenses)
        .filter(
            Expenses.user_id == current_user.id,
            Expenses.created_at >= payload.start_datetime,
            Expenses.created_at <= payload.end_datetime,
        )
        .order_by(Expenses.type.asc(), Expenses.created_at.desc())
        .all()
    )

    # Группируем расходы по категории (поле type).
    # Расходы без категории относим к "other".
    grouped: dict[str, list[Expenses]] = {}
    for expense in expenses:
        grouped.setdefault(
            expense.type or UNCATEGORIZED_CATEGORY, []
        ).append(expense)

    categories = [
        CategoryReport(
            category=category,
            total=round(sum(item.amount for item in items), 2),
            count=len(items),
            expenses=[
                ReportExpenseItem.model_validate(item) for item in items
            ],
        )
        for category, items in sorted(grouped.items())
    ]

    return ReportResponse(
        date_from=payload.date_from,
        date_to=payload.date_to,
        total_amount=round(sum(e.amount for e in expenses), 2),
        total_count=len(expenses),
        categories=categories,
    )
