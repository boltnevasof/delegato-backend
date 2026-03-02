from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, manage_session
from app.api.v1.schemas.server import (
    ServerLogItem,
    ServerLogListResponse,
    ServerProvisionResponse,
    ServerStatusResponse,
)
from app.core.container import Container
from app.db.engine import session_context
from app.exceptions.base import ConflictError
from app.models.user import User
from app.services.agent import AgentService
from app.services.server import ServerService
from app.tasks.provisioning import provision_server

router = APIRouter(prefix="/servers", tags=["servers"])


@router.post(
    "/provision",
    response_model=ServerProvisionResponse,
    status_code=202,
    summary="Запустить провижининг сервера",
    description=(
        "Создаёт агента и сервер для текущего пользователя, запускает фоновый "
        "провижининг (Terraform → VPS, Ansible → Docker + OpenClaw). "
        "Вызывается после оплаты. Сервер готовится параллельно с онбордингом."
    ),
)
@inject
@manage_session
async def start_provision(
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
    server_service: ServerService = Depends(Provide[Container.server_service]),
) -> ServerProvisionResponse:
    # Create agent if not exists
    agent = await agent_service.get_or_create_agent(current_user.id)

    # Ensure no duplicate server
    existing = await server_service.find_by_agent(agent.id)
    if existing is not None:
        raise ConflictError(detail="Server already exists for this agent")

    # Create server record and commit so the worker can see it
    server = await server_service.create_server(agent.id)
    await session_context.get().commit()

    # Kick background provisioning after data is committed
    await provision_server.kiq(str(server.id))

    return ServerProvisionResponse(
        server_id=server.id,
        status=server.status.value,
    )


@router.get(
    "/me",
    response_model=ServerStatusResponse,
    summary="Статус сервера",
    description="Возвращает текущий статус выделенного сервера агента: IP-адрес, этап провижининга и дату создания.",
)
@inject
@manage_session
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
@manage_session
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
