import uuid

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query

from app.api.deps import check_ip_whitelist, get_admin_user, manage_session
from app.api.v1.schemas.admin import (
    AdminAgentListItem,
    AdminAgentListResponse,
    AdminCustomRequestItem,
    AdminCustomRequestListResponse,
    AdminLoginRequest,
    AdminLoginResponse,
    AdminOTPCodeItem,
    AdminOTPCodeListResponse,
    AdminServerListItem,
    AdminServerListResponse,
    AdminServerStats,
    AdminSupportRequestItem,
    AdminSupportRequestListResponse,
    AdminUpdateUserRequest,
    AdminUpdateUserResponse,
    AdminUserListItem,
    AdminUserListResponse,
)
from app.api.v1.schemas.server import ServerLogItem, ServerLogListResponse
from app.core.constants import CustomRequestStatus, ServerLogLevel, ServerStatus, SupportRequestStatus
from app.core.container import Container
from app.repositories.agent import AgentRepository
from app.repositories.custom_request import CustomTariffRequestRepository
from app.repositories.otp import OTPCodeRepository
from app.repositories.server import ServerRepository
from app.repositories.support_request import SupportRequestRepository
from app.repositories.server_log import ServerLogRepository
from app.repositories.user import UserRepository
from app.services.admin import AdminService
from app.services.dto.admin import AdminLoginDTO, AdminUpdateUserDTO

login_router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(check_ip_whitelist)],
)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_admin_user), Depends(check_ip_whitelist)],
)


@router.get(
    "/users",
    response_model=AdminUserListResponse,
    summary="Список пользователей",
    description="Постраничный список всех пользователей платформы с поиском по email/имени.",
)
@inject
@manage_session
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, description="Поиск по email или имени"),
    user_repo: UserRepository = Depends(Provide[Container.user_repository]),
) -> AdminUserListResponse:
    items, total = await user_repo.list_paginated(page, per_page, search=search)
    return AdminUserListResponse(
        items=[
            AdminUserListItem(
                id=u.id, email=u.email, name=u.name,
                role=u.role.value, is_active=u.is_active,
                created_at=u.created_at,
            )
            for u in items
        ],
        total=total, page=page, per_page=per_page,
    )


@router.get(
    "/servers",
    response_model=AdminServerListResponse,
    summary="Список серверов",
    description="Постраничный список всех серверов с возможностью фильтрации по статусу (provisioning, active, error и т.д.).",
)
@inject
@manage_session
async def list_servers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, description="Фильтр по статусу сервера"),
    server_repo: ServerRepository = Depends(Provide[Container.server_repository]),
) -> AdminServerListResponse:
    server_status = ServerStatus(status) if status else None
    items, total = await server_repo.list_paginated(page, per_page, status=server_status)
    return AdminServerListResponse(
        items=[
            AdminServerListItem(
                id=s.id, agent_id=s.agent_id, status=s.status.value,
                ip_address=s.ip_address, created_at=s.created_at,
            )
            for s in items
        ],
        total=total, page=page, per_page=per_page,
    )


@router.get(
    "/servers/stats",
    response_model=AdminServerStats,
    summary="Статистика серверов",
    description="Сводная статистика по серверам: общее количество, активные, в процессе провижининга, с ошибками, остановленные.",
)
@inject
@manage_session
async def get_server_stats(
    server_repo: ServerRepository = Depends(Provide[Container.server_repository]),
) -> AdminServerStats:
    stats = await server_repo.get_stats()
    return AdminServerStats(
        total=stats.get("total", 0),
        active=stats.get("active", 0),
        provisioning=stats.get("provisioning", 0),
        error=stats.get("error", 0),
        stopped=stats.get("stopped", 0),
    )


@router.get(
    "/servers/{server_id}/logs",
    response_model=ServerLogListResponse,
    summary="Логи сервера (по ID)",
    description="Постраничные логи конкретного сервера. Фильтрация по уровню: info, warning, error.",
)
@inject
@manage_session
async def get_server_logs(
    server_id: uuid.UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    level: str | None = Query(None, description="Фильтр по уровню лога"),
    log_repo: ServerLogRepository = Depends(Provide[Container.server_log_repository]),
) -> ServerLogListResponse:
    log_level = ServerLogLevel(level) if level else None
    items, total = await log_repo.get_by_server_id_paginated(
        server_id, page, per_page, level=log_level,
    )
    return ServerLogListResponse(
        items=[
            ServerLogItem(
                id=log.id, level=log.level.value, stage=log.stage,
                message=log.message, created_at=log.created_at,
            )
            for log in items
        ],
        total=total, page=page, per_page=per_page,
    )


@router.get(
    "/agents",
    response_model=AdminAgentListResponse,
    summary="Список агентов",
    description="Постраничный список всех AI-агентов платформы с информацией о статусе и шаге онбординга.",
)
@inject
@manage_session
async def list_agents(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    agent_repo: AgentRepository = Depends(Provide[Container.agent_repository]),
) -> AdminAgentListResponse:
    items, total = await agent_repo.list_paginated(page, per_page)
    return AdminAgentListResponse(
        items=[
            AdminAgentListItem(
                id=a.id, user_id=a.user_id, status=a.status.value,
                onboarding_step=a.onboarding_step, created_at=a.created_at,
            )
            for a in items
        ],
        total=total, page=page, per_page=per_page,
    )


@router.get(
    "/custom-requests",
    response_model=AdminCustomRequestListResponse,
    summary="Заявки на кастомный тариф",
    description="Постраничный список заявок на индивидуальный тариф с фильтрацией по статусу (new, contacted, closed).",
)
@inject
@manage_session
async def list_custom_requests(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, description="Фильтр по статусу заявки"),
    custom_repo: CustomTariffRequestRepository = Depends(
        Provide[Container.custom_request_repository],
    ),
) -> AdminCustomRequestListResponse:
    req_status = CustomRequestStatus(status) if status else None
    items, total = await custom_repo.list_paginated(page, per_page, status=req_status)
    return AdminCustomRequestListResponse(
        items=[
            AdminCustomRequestItem(
                id=r.id, user_id=r.user_id, contact_info=r.contact_info,
                requirements=r.requirements, status=r.status.value,
                created_at=r.created_at,
            )
            for r in items
        ],
        total=total, page=page, per_page=per_page,
    )


# --- Login (no JWT required, only IP whitelist) ---

@login_router.post(
    "/login",
    response_model=AdminLoginResponse,
    summary="Логин администратора",
    description="Аутентификация по username/password из .env. Возвращает JWT access token.",
)
@inject
@manage_session
async def admin_login(
    body: AdminLoginRequest,
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
) -> AdminLoginResponse:
    dto = AdminLoginDTO(username=body.username, password=body.password)
    result = await admin_service.login(dto)
    return AdminLoginResponse(
        access_token=result.access_token,
        token_type=result.token_type,
        expires_in=result.expires_in,
    )


# --- User update (JWT + admin role required) ---

@router.patch(
    "/users/{user_id}",
    response_model=AdminUpdateUserResponse,
    summary="Редактирование пользователя",
    description="Обновление полей пользователя: имя, email, роль, активность.",
)
@inject
@manage_session
async def update_user(
    user_id: uuid.UUID,
    body: AdminUpdateUserRequest,
    admin_service: AdminService = Depends(Provide[Container.admin_service]),
    user_repo: UserRepository = Depends(Provide[Container.user_repository]),
) -> AdminUpdateUserResponse:
    dto = AdminUpdateUserDTO(
        name=body.name,
        email=body.email,
        role=body.role,
        is_active=body.is_active,
    )
    await admin_service.update_user(user_id, dto)
    user = await user_repo.get_by_id(user_id)
    return AdminUpdateUserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


# --- OTP codes list (JWT + admin role required) ---

@router.get(
    "/otp-codes",
    response_model=AdminOTPCodeListResponse,
    summary="Список OTP-кодов",
    description="Постраничный список OTP-кодов с фильтрацией по email.",
)
@inject
@manage_session
async def list_otp_codes(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    email: str | None = Query(None, description="Фильтр по email"),
    otp_repo: OTPCodeRepository = Depends(Provide[Container.otp_repository]),
) -> AdminOTPCodeListResponse:
    items, total = await otp_repo.list_paginated(page, per_page, email=email)
    return AdminOTPCodeListResponse(
        items=[
            AdminOTPCodeItem(
                id=o.id,
                email=o.email,
                code=o.code,
                is_used=o.is_used,
                expires_at=o.expires_at,
                created_at=o.created_at,
            )
            for o in items
        ],
        total=total, page=page, per_page=per_page,
    )


@router.get(
    "/support-requests",
    response_model=AdminSupportRequestListResponse,
    summary="Заявки в поддержку",
    description="Постраничный список заявок в поддержку с фильтрацией по статусу (new, in_progress, closed).",
)
@inject
@manage_session
async def list_support_requests(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, description="Фильтр по статусу заявки"),
    support_repo: SupportRequestRepository = Depends(
        Provide[Container.support_request_repository],
    ),
) -> AdminSupportRequestListResponse:
    req_status = SupportRequestStatus(status) if status else None
    items, total = await support_repo.list_paginated(page, per_page, status=req_status)
    return AdminSupportRequestListResponse(
        items=[
            AdminSupportRequestItem(
                id=r.id,
                user_id=r.user_id,
                topic=r.topic,
                description=r.description,
                contact_method=r.contact_method,
                contact=r.contact,
                status=r.status.value,
                created_at=r.created_at,
            )
            for r in items
        ],
        total=total, page=page, per_page=per_page,
    )
