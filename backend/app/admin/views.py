"""SQLAdmin model views for FinSight admin panel."""

from wtforms import SelectField

from sqladmin import Admin, ModelView

from app.admin.auth import AdminAuth
from app.core.config import settings
from app.core.database import engine
from app.models.user import User
from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction


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
        User.accounts,
        User.categories,
        User.transactions
    ]

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True


class AccountAdmin(ModelView, model=Account):
    """Admin view for Account model."""

    name = "Счёт"
    name_plural = "Счета"
    icon = "fa-solid fa-wallet"

    column_list = [
        Account.id,
        Account.name,
        Account.type,
        Account.balance,
        Account.currency,
        Account.is_archived,
        Account.user,
        Account.created_at,
    ]
    column_searchable_list = [Account.name]
    column_sortable_list = [
        Account.id,
        Account.name,
        Account.balance,
        Account.created_at,
    ]
    column_default_sort = [(Account.id, True)]
    column_labels = {
        Account.id: "ID",
        Account.name: "Название",
        Account.type: "Тип",
        Account.balance: "Баланс",
        Account.currency: "Валюта",
        Account.is_archived: "Архивный",
        Account.credit_limit: "Кредитный лимит",
        Account.user: "Пользователь",
        Account.created_at: "Создан",
        Account.updated_at: "Обновлён",
    }

    form_excluded_columns = [Account.transactions]
    form_overrides = {
        "type": SelectField,
    }
    form_args = {
        "type": {
            "choices": [
                ("cash", "Наличные"),
                ("bank", "Банк"),
                ("credit", "Кредитная"),
                ("investment", "Инвестиции"),
                ("savings", "Сбережения"),
            ]
        },
    }

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True


class CategoryAdmin(ModelView, model=Category):
    """Admin view for Category model."""

    name = "Категория"
    name_plural = "Категории"
    icon = "fa-solid fa-tags"

    column_list = [
        Category.id,
        Category.name,
        Category.type,
        Category.parent,
        Category.is_system,
        Category.user,
    ]
    column_searchable_list = [Category.name]
    column_sortable_list = [
        Category.id,
        Category.name,
        Category.type,
        Category.is_system,
    ]
    column_default_sort = [(Category.id, True)]
    column_labels = {
        Category.id: "ID",
        Category.name: "Название",
        Category.type: "Тип",
        Category.parent: "Родитель",
        Category.icon: "Иконка",
        Category.color: "Цвет",
        Category.is_system: "Системная",
        Category.user: "Пользователь",
    }

    form_excluded_columns = [Category.children]
    form_overrides = {
        "type": SelectField,
    }
    form_args = {
        "type": {
            "choices": [
                ("income", "Доход"),
                ("expense", "Расход"),
            ]
        },
    }

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True


class TransactionAdmin(ModelView, model=Transaction):
    """Admin view for Transaction model."""

    name = "Транзакция"
    name_plural = "Транзакции"
    icon = "fa-solid fa-exchange-alt"

    column_list = [
        Transaction.id,
        Transaction.type,
        Transaction.amount,
        Transaction.currency,
        Transaction.description,
        Transaction.date,
        Transaction.user,
        Transaction.account,
        Transaction.category,
        Transaction.created_at,
    ]
    column_searchable_list = [
        Transaction.description,
        Transaction.notes
    ]
    column_sortable_list = [
        Transaction.id,
        Transaction.amount,
        Transaction.date,
        Transaction.created_at,
    ]
    column_default_sort = [(Transaction.date, True), (Transaction.id, True)]
    column_labels = {
        Transaction.id: "ID",
        Transaction.type: "Тип",
        Transaction.amount: "Сумма",
        Transaction.currency: "Валюта",
        Transaction.description: "Описание",
        Transaction.notes: "Заметки",
        Transaction.date: "Дата",
        Transaction.is_recurring: "Регулярная",
        Transaction.recurrence_rule: "Правило повтора",
        Transaction.user: "Пользователь",
        Transaction.account: "Счёт",
        Transaction.category: "Категория",
        Transaction.created_at: "Создан",
        Transaction.updated_at: "Обновлён",
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
    admin.add_view(AccountAdmin)
    admin.add_view(CategoryAdmin)
    admin.add_view(TransactionAdmin)

    return admin
