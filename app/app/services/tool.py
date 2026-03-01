import uuid

from app.exceptions.base import NotFound
from app.models.agent_tool import AgentTool
from app.repositories.agent_tool import AgentToolRepository
from app.repositories.tool import ToolCatalogRepository


class ToolService:
    def __init__(
        self,
        tool_catalog_repository: ToolCatalogRepository,
        agent_tool_repository: AgentToolRepository,
    ) -> None:
        self._catalog_repo = tool_catalog_repository
        self._agent_tool_repo = agent_tool_repository

    async def get_catalog(self) -> list[dict]:
        tools = await self._catalog_repo.list_active()
        return [
            {
                "id": t.id,
                "slug": t.slug,
                "name": t.name,
                "description": t.description,
            }
            for t in tools
        ]

    async def add_tool(
        self, agent_id: uuid.UUID, tool_id: uuid.UUID, config: dict | None = None,
    ) -> AgentTool:
        tool = await self._catalog_repo.get_by_id(tool_id)
        if tool is None:
            raise NotFound(detail=f"Tool {tool_id} not found")
        existing = await self._agent_tool_repo.get_by_agent_and_tool(agent_id, tool_id)
        if existing is not None:
            return existing
        return await self._agent_tool_repo.create(agent_id, tool_id, config=config)

    async def toggle_tool(
        self, agent_id: uuid.UUID, tool_id: uuid.UUID, is_enabled: bool,
    ) -> AgentTool:
        agent_tool = await self._agent_tool_repo.get_by_agent_and_tool(agent_id, tool_id)
        if agent_tool is None:
            raise NotFound(detail="Tool not assigned to agent")
        await self._agent_tool_repo.update(agent_tool.id, is_enabled=is_enabled)
        agent_tool.is_enabled = is_enabled
        return agent_tool

    async def remove_tool(self, agent_id: uuid.UUID, tool_id: uuid.UUID) -> None:
        agent_tool = await self._agent_tool_repo.get_by_agent_and_tool(agent_id, tool_id)
        if agent_tool is None:
            raise NotFound(detail="Tool not assigned to agent")
        await self._agent_tool_repo.delete(agent_tool.id)
