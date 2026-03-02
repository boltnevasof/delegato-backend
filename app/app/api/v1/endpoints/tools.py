import uuid

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, manage_session
from app.api.v1.schemas.tool import (
    AddToolRequest,
    AgentToolResponse,
    ToggleToolRequest,
    ToolCatalogItem,
    ToolCatalogResponse,
)
from app.core.container import Container
from app.models.user import User
from app.services.agent import AgentService
from app.services.tool import ToolService

router = APIRouter(tags=["tools"])


@router.get(
    "/tools/catalog",
    response_model=ToolCatalogResponse,
    summary="Каталог инструментов",
    description="Возвращает список всех доступных инструментов (MCP-серверов, API-интеграций) для подключения к агенту.",
)
@inject
@manage_session
async def get_tool_catalog(
    current_user: User = Depends(get_current_user),
    tool_service: ToolService = Depends(Provide[Container.tool_service]),
) -> ToolCatalogResponse:
    catalog = await tool_service.get_catalog()
    return ToolCatalogResponse(
        tools=[ToolCatalogItem(**t) for t in catalog],
    )


@router.post(
    "/agents/me/tools",
    response_model=AgentToolResponse,
    status_code=201,
    summary="Добавить инструмент агенту",
    description="Подключает указанный инструмент из каталога к AI-агенту текущего пользователя.",
)
@inject
@manage_session
async def add_tool(
    body: AddToolRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
    tool_service: ToolService = Depends(Provide[Container.tool_service]),
) -> AgentToolResponse:
    agent = await agent_service.get_by_user(current_user.id)
    agent_tool = await tool_service.add_tool(agent.id, body.tool_id)
    return AgentToolResponse(
        id=agent_tool.tool.id, slug=agent_tool.tool.slug, is_enabled=agent_tool.is_enabled,
    )


@router.patch(
    "/agents/me/tools/{tool_id}",
    response_model=AgentToolResponse,
    summary="Вкл/выкл инструмент",
    description="Включает или выключает ранее добавленный инструмент агента без удаления.",
)
@inject
@manage_session
async def toggle_tool(
    tool_id: uuid.UUID,
    body: ToggleToolRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
    tool_service: ToolService = Depends(Provide[Container.tool_service]),
) -> AgentToolResponse:
    agent = await agent_service.get_by_user(current_user.id)
    agent_tool = await tool_service.toggle_tool(agent.id, tool_id, body.is_enabled)
    return AgentToolResponse(
        id=agent_tool.tool.id, slug=agent_tool.tool.slug, is_enabled=agent_tool.is_enabled,
    )


@router.delete(
    "/agents/me/tools/{tool_id}",
    status_code=204,
    summary="Удалить инструмент",
    description="Полностью отключает инструмент от агента. Для повторного использования потребуется добавить заново.",
)
@inject
@manage_session
async def remove_tool(
    tool_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
    tool_service: ToolService = Depends(Provide[Container.tool_service]),
) -> None:
    agent = await agent_service.get_by_user(current_user.id)
    await tool_service.remove_tool(agent.id, tool_id)
