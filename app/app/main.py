import sys
import uuid as uuid_mod
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from contextvars import ContextVar

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.api.v1.api_routers import v1_router
from app.core.config import settings
from app.core.container import Container
from app.db.engine import engine
from app.exceptions.base import AppException

# --- Request context ---
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")

# --- DI Container ---
container = Container()

# --- Loguru structured logging ---
logger.remove()
logger.add(
    sys.stderr,
    format="{time:YYYY-MM-DDTHH:mm:ss.SSSZ} | {level} | {extra[request_id]} | {message}",
    level="INFO",
    serialize=settings.DEBUG is False,
    enqueue=True,
)


def _before_send(event: dict, hint: dict) -> dict | None:
    """Strip PII from Sentry events."""
    if "request" in event and "headers" in event["request"]:
        headers = event["request"]["headers"]
        for key in ("authorization", "cookie"):
            headers.pop(key, None)
    return event


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            traces_sample_rate=0.1,
            environment="production" if not settings.DEBUG else "development",
            before_send=_before_send,
            integrations=[
                FastApiIntegration(),
                StarletteIntegration(),
                AsyncioIntegration(),
                SqlalchemyIntegration(),
            ],
        )
    yield
    await engine.dispose()


app = FastAPI(
    title="Delegato Backend",
    description="SaaS-платформа для управления AI-агентами, развёрнутыми на выделенных серверах клиентов.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_tags=[
        {"name": "health", "description": "Проверка работоспособности сервиса и зависимостей."},
        {"name": "auth", "description": "Аутентификация: email OTP, Google OAuth, Telegram Login."},
        {"name": "users", "description": "Профиль текущего пользователя."},
        {"name": "tariffs", "description": "Каталог тарифных планов и заявки на кастомный тариф."},
        {"name": "subscriptions", "description": "Управление подпиской: смена тарифа, отмена, реактивация."},
        {"name": "payments", "description": "Оплата подписки, вебхуки платёжной системы, история платежей."},
        {"name": "agents", "description": "AI-агент пользователя: онбординг, настройка SOUL.md / AGENT.md, AI-улучшение."},
        {"name": "skills", "description": "Каталог навыков и управление навыками агента."},
        {"name": "tools", "description": "Каталог инструментов и управление инструментами агента."},
        {"name": "channels", "description": "Каналы связи агента (Telegram и др.)."},
        {"name": "servers", "description": "Статус сервера агента и логи провижининга."},
        {"name": "admin", "description": "Административная панель (требуется роль admin и IP whitelist)."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    rid = request.headers.get("X-Request-ID", uuid_mod.uuid4().hex[:12])
    request_id_ctx.set(rid)
    with logger.contextualize(
        request_id=rid,
        path=request.url.path,
        method=request.method,
    ):
        response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


app.include_router(v1_router)
