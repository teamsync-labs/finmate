"""SQLAdmin model views for FinSight admin panel."""

from datetime import datetime, time, timezone
from pathlib import Path

from fastapi.templating import Jinja2Templates
from sqladmin import Admin, BaseView, ModelView, expose
from starlette.requests import Request
from starlette.responses import HTMLResponse, Response
from wtforms import SelectField

from app.admin.auth import AdminAuth
from app.core.config import settings
from app.core.constants import (
    ADMIN_BASE_URL,
    ADMIN_TITLE,
    EXPENSE_TYPE_CHOICES,
    UNCATEGORIZED_CATEGORY,
)
from app.core.database import SessionLocal, engine
from app.models.user import User
from app.models.expenses import Expenses


# Шаблоны админ-панели лежат в app/admin/templates/
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


class UserAdmin(ModelView, model=User):
    """Admin view for User model."""

    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-user"

    column_list = [
        User.id,
        User.telegram_id,
        User.username,
        User.created_at,
    ]
    column_searchable_list = [
        User.username,
        User.telegram_id,
    ]
    column_sortable_list = [
        User.id,
        User.telegram_id,
        User.username,
        User.created_at,
    ]
    column_default_sort = [(User.id, True)]
    column_labels = {
        User.id: "ID",
        User.telegram_id: "Telegram ID",
        User.username: "Username",
        User.settings: "Настройки",
        User.created_at: "Создан",
    }

    form_excluded_columns = [
        User.expenses,
        User.username,
    ]

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True


class ReportAdmin(BaseView):
    """Эндпоинт отчёта по расходам за период в админ-панели.

    Доступен по адресу /admin/report?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
    и защищён той же админ-аутентификацией, что и остальные страницы.
    """

    name = "Отчёт по расходам"
    name_plural = "Отчёты"
    icon = "fa-solid fa-chart-pie"

    @expose("/report", methods=["GET"])
    async def report(self, request: Request) -> Response:
        """Отчёт по расходам за указанный период.

        Если параметры date_from / date_to не переданы или некорректны,
        вместо ошибки 400 рендерится HTML-форма выбора периода, которая
        сабмитит на тот же /admin/report. При корректных параметрах
        рендерится HTML-страница с итогами и таблицей по категориям.
        """

        date_from = request.query_params.get("date_from", "").strip()
        date_to = request.query_params.get("date_to", "").strip()

        if not date_from or not date_to:
            return self._render_page(request, date_from, date_to)

        try:
            start = datetime.combine(
                datetime.fromisoformat(date_from).date(),
                time.min,
                tzinfo=timezone.utc,
            )
            end = datetime.combine(
                datetime.fromisoformat(date_to).date(),
                time.max,
                tzinfo=timezone.utc,
            )
        except ValueError:
            return self._render_page(
                request,
                date_from,
                date_to,
                error=(
                    "Неверный формат даты. "
                    "Ожидается ISO-формат, например 2025-01-01."
                ),
            )

        if start > end:
            return self._render_page(
                request,
                date_from,
                date_to,
                error="«С даты» должна быть раньше или равна «По дату».",
            )

        with SessionLocal() as db:
            expenses = (
                db.query(Expenses)
                .filter(
                    Expenses.created_at >= start,
                    Expenses.created_at <= end,
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
            {
                "category": category,
                "total": round(sum(e.amount for e in items), 2),
                "count": len(items),
                "expenses": [
                    {
                        "id": e.id,
                        "user_id": e.user_id,
                        "expense_name": e.expense_name,
                        "amount": e.amount,
                        "currency": e.currency,
                        "created_at": (
                            e.created_at.isoformat()
                            if e.created_at else None
                        ),
                    }
                    for e in items
                ],
            }
            for category, items in sorted(grouped.items())
        ]

        return self._render_page(
            request,
            date_from,
            date_to,
            report={
                "date_from": date_from,
                "date_to": date_to,
                "total_amount": round(
                    sum(e.amount for e in expenses), 2
                ),
                "total_count": len(expenses),
                "categories": categories,
            },
        )

    def _render_page(
        self,
        request: Request,
        date_from: str = "",
        date_to: str = "",
        error: str | None = None,
        report: dict | None = None,
    ) -> HTMLResponse:
        """Рендерит HTML-страницу отчёта: форму выбора периода и результаты.

        Форма отправляется методом GET на тот же /admin/report и несёт
        параметры date_from / date_to в query string. Если передан report,
        на странице дополнительно выводятся итоги и таблицы по категориям.
        Вся разметка (формы, ошибок и результатов) живёт в шаблоне
        report.html: сюда передаются только структурированные данные,
        экранирование и циклы делает Jinja2.
        """

        form_action = request.url.path
        admin_url = form_action.rsplit("/", 1)[0]

        return templates.TemplateResponse(
            request,
            "report.html",
            {
                "form_action": form_action,
                "admin_url": admin_url,
                "date_from": date_from,
                "date_to": date_to,
                "error": error,
                "report": report,
            },
        )


class ExpenseAdmin(ModelView, model=Expenses):
    """Admin view for Expenses model."""

    name = "Расход"
    name_plural = "Расходы"
    icon = "fa-solid fa-receipt"

    column_list = [
        Expenses.id,
        Expenses.expense_name,
        Expenses.amount,
        Expenses.type,
        Expenses.currency,
        Expenses.user,
        Expenses.created_at,
    ]
    column_searchable_list = [Expenses.expense_name]
    column_sortable_list = [
        Expenses.id,
        Expenses.expense_name,
        Expenses.amount,
        Expenses.created_at,
    ]
    column_default_sort = [(Expenses.id, True)]
    column_labels = {
        Expenses.id: "ID",
        Expenses.expense_name: "Название",
        Expenses.amount: "Сумма",
        Expenses.type: "Тип",
        Expenses.currency: "Валюта",
        Expenses.user: "Пользователь",
        Expenses.created_at: "Создан",
        Expenses.updated_at: "Обновлён",
    }

    form_overrides = {
        "type": SelectField,
    }
    form_args = {
        "type": {
            "choices": list(EXPENSE_TYPE_CHOICES),
        }
    }

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True


def register_admin(app):
    """Register SQLAdmin with all model views."""

    auth_backend = AdminAuth(secret_key=settings.SECRET_KEY)

    admin = Admin(
        app=app,
        engine=engine,
        authentication_backend=auth_backend,
        title=ADMIN_TITLE,
        base_url=ADMIN_BASE_URL,
        logo_url=None,
    )

    admin.add_view(UserAdmin)
    admin.add_view(ExpenseAdmin)
    admin.add_view(ReportAdmin)

    return admin
