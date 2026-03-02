import contextvars
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ContextVar — единственный способ получить сессию в репозиториях
session_context: contextvars.ContextVar[AsyncSession] = contextvars.ContextVar(
    "session_context",
)


def create_session() -> AsyncSession:
    """Фабрика сессий. Вызывается из Container.session() и manage_session."""
    return async_session_factory()
