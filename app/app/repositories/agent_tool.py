import uuid

from sqlalchemy import delete, select, update

from app.db.engine import session_context
from app.models.agent_tool import AgentTool


class AgentToolRepository:
    @property
    def _session(self):
        return session_context.get()

    async def create(self, agent_id: uuid.UUID, tool_id: uuid.UUID, config: dict | None = None) -> AgentTool:
        agent_tool = AgentTool(agent_id=agent_id, tool_id=tool_id, config=config)
        self._session.add(agent_tool)
        await self._session.flush()
        return agent_tool

    async def get_by_agent_id(self, agent_id: uuid.UUID) -> list[AgentTool]:
        result = await self._session.execute(
            select(AgentTool).where(AgentTool.agent_id == agent_id)
        )
        return list(result.scalars().all())

    async def get_by_agent_and_tool(
        self, agent_id: uuid.UUID, tool_id: uuid.UUID,
    ) -> AgentTool | None:
        result = await self._session.execute(
            select(AgentTool).where(
                AgentTool.agent_id == agent_id,
                AgentTool.tool_id == tool_id,
            )
        )
        return result.scalar_one_or_none()

    async def update(self, agent_tool_id: uuid.UUID, **kwargs) -> None:
        await self._session.execute(
            update(AgentTool).where(AgentTool.id == agent_tool_id).values(**kwargs)
        )
        await self._session.flush()

    async def delete(self, agent_tool_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(AgentTool).where(AgentTool.id == agent_tool_id)
        )
        await self._session.flush()
