"""SQLAdmin model views for FinSight admin panel."""

from wtforms import SelectField

from sqladmin import Admin, ModelView

from app.admin.auth import AdminAuth
from app.core.config import settings
from app.core.database import engine
from app.models.user import User
from app.models.expenses import Expenses


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
            "choices": [
                ("general", "Общее"),
                ("food", "Продукты"),
                ("transport", "Транспорт"),
                ("housing", "Жильё"),
                ("utilities", "Коммунальные"),
                ("entertainment", "Развлечения"),
                ("health", "Здоровье"),
                ("education", "Образование"),
                ("shopping", "Покупки"),
                ("other", "Другое"),
            ]
        },
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
        title="FinSight Admin",
        base_url="/admin",
        logo_url=None,
    )

    admin.add_view(UserAdmin)
    admin.add_view(ExpenseAdmin)

    return admin
