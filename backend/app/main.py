from contextlib import asynccontextmanager
import logging
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.core.constants import (
    APP_CONTACT_EMAIL,
    APP_CONTACT_NAME,
    APP_VERSION,
)
from app.core.database import engine, Base
from app.api.v1 import auth, accounts, report, transactions
from app.admin import register_admin


_DOCS_USER = "dev"
_DOCS_PASSWORD = "dev"
_docs_basic = HTTPBasic(auto_error=True)


def _require_docs_basic(
    credentials: Annotated[HTTPBasicCredentials, Depends(_docs_basic)],
) -> None:
    if (
        credentials.username != _DOCS_USER
        or credentials.password != _DOCS_PASSWORD
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized",
            headers={"WWW-Authenticate": 'Basic realm="API docs"'},
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "API финансового помощника"
        " с автоматической категоризацией и учётом транзакций"
    ),
    version=APP_VERSION,
    contact={
        "name": APP_CONTACT_NAME,
        "email": APP_CONTACT_EMAIL,
    },
    swagger_ui_parameters={"persistAuthorization": True},
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Admin session middleware (required by SQLAdmin for auth)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(accounts.router, prefix=settings.API_V1_PREFIX)
app.include_router(report.router, prefix=settings.API_V1_PREFIX)
app.include_router(transactions.router, prefix=settings.API_V1_PREFIX)


# Register admin panel
register_admin(app)


@app.get("/docs", include_in_schema=False)
async def swagger_ui(_: Annotated[None, Depends(_require_docs_basic)]):
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{settings.APP_NAME} - Swagger UI",
    )


@app.get("/redoc", include_in_schema=False)
async def redoc_ui(_: Annotated[None, Depends(_require_docs_basic)]):
    return get_redoc_html(
        openapi_url="/openapi.json",
        title=f"{settings.APP_NAME} - ReDoc",
    )


@app.get("/openapi.json", include_in_schema=False)
async def openapi_schema(_: Annotated[None, Depends(_require_docs_basic)]):
    return JSONResponse(app.openapi())


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger = logging.getLogger(__name__)
    logger.exception("Unhandled exception: %s", exc)

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )


@app.get("/")
def root():
    return {"message": f"Welcome to {settings.APP_NAME}"}


@app.get("/health")
def health():
    """Проверка здоровья сервиса и состояния БД."""

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        database = "connected"
        status = "ok"
    except Exception:
        database = "disconnected"
        status = "degraded"

    return {"status": status, "database": database}
