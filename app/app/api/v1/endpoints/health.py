import redis.asyncio as aioredis
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.db.engine import async_session_factory

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Health check",
    description="Проверяет доступность PostgreSQL и Redis. Возвращает 503 если хотя бы один компонент недоступен.",
)
async def health_check() -> JSONResponse:
    result = {
        "status": "ok",
        "db": "ok",
        "redis": "ok",
        "version": settings.APP_VERSION,
    }
    status_code = 200

    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        result["db"] = "error"
        result["status"] = "degraded"
        status_code = 503

    try:
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.aclose()
    except Exception:
        result["redis"] = "error"
        result["status"] = "degraded"
        status_code = 503

    return JSONResponse(content=result, status_code=status_code)
