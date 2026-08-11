from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import auth, accounts, report
from app.admin import register_admin


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
    version="1.0.0",
    contact={"name": "Команда FinSight", "email": "dev@finsight.example.com"},
    swagger_ui_parameters={"persistAuthorization": True},
    lifespan=lifespan,
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


# Register admin panel
register_admin(app)


original_openapi = app.openapi


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
