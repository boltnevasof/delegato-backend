from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.api.v1.schemas.server import (
    ServerLogItem,
    ServerLogListResponse,
    ServerStatusResponse,
)
from app.core.container import Container
from app.models.user import User
from app.services.server import ServerService

router = APIRouter(prefix="/servers", tags=["servers"])


@router.get(
    "/me",
    response_model=ServerStatusResponse,
    summary="Статус сервера",
    description="Возвращает текущий статус выделенного сервера агента: IP-адрес, этап провижининга и дату создания.",
)
@inject
async def get_server_status(
    current_user: User = Depends(get_current_user),
    server_service: ServerService = Depends(Provide[Container.server_service]),
) -> ServerStatusResponse:
    dto = await server_service.get_by_user(current_user.id)
    return ServerStatusResponse(
        id=dto.id,
        status=dto.status,
        ip_address=dto.ip_address,
        created_at=dto.created_at,
    )


@router.get(
    "/me/logs",
    response_model=ServerLogListResponse,
    summary="Логи сервера",
    description="Возвращает постраничный список логов провижининга и конфигурации сервера. Можно фильтровать по уровню (info / warning / error).",
)
@inject
async def get_server_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    level: str | None = Query(None, description="Фильтр по уровню: info, warning, error"),
    current_user: User = Depends(get_current_user),
    server_service: ServerService = Depends(Provide[Container.server_service]),
) -> ServerLogListResponse:
    items, total = await server_service.get_logs(
        current_user.id, page, per_page, level=level,
    )
    return ServerLogListResponse(
        items=[
            ServerLogItem(
                id=log.id,
                level=log.level,
                stage=log.stage,
                message=log.message,
                created_at=log.created_at,
            )
            for log in items
        ],
        total=total,
        page=page,
        per_page=per_page,
    )
