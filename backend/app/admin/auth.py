"""Authentication backend for SQLAdmin panel."""

from typing import Optional

from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from app.core.config import settings


class AdminAuth(AuthenticationBackend):
    """Простая аутентификация по логину/паролю для админ-панели."""

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if (
            username == settings.ADMIN_USERNAME
            and password == settings.ADMIN_PASSWORD
        ):
            request.session.update({"token": "admin_session_token"})
            return True

        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> Response | bool:
        token = request.session.get("token")
        if not token or token != "admin_session_token":
            return RedirectResponse(
                request.url_for("admin:login"),
                status_code=302
            )
        return True
