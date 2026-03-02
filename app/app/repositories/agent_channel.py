import uuid

from sqlalchemy import func, select, update

from app.db.engine import session_context
from app.models.agent_channel import AgentChannel


class AgentChannelRepository:
    @property
    def _session(self):
        return session_context.get()

    async def create(self, **kwargs) -> AgentChannel:
        channel = AgentChannel(**kwargs)
        self._session.add(channel)
        await self._session.flush()
        return channel

    async def get_by_agent_id(self, agent_id: uuid.UUID) -> list[AgentChannel]:
        result = await self._session.execute(
            select(AgentChannel).where(AgentChannel.agent_id == agent_id)
        )
        return list(result.scalars().all())

    async def count_by_agent(self, agent_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(AgentChannel).where(AgentChannel.agent_id == agent_id)
        )
        return result.scalar_one()

    async def update(self, channel_id: uuid.UUID, **kwargs) -> AgentChannel | None:
        await self._session.execute(
            update(AgentChannel).where(AgentChannel.id == channel_id).values(**kwargs)
        )
        await self._session.flush()
        result = await self._session.execute(
            select(AgentChannel).where(AgentChannel.id == channel_id)
        )
        return result.scalar_one_or_none()
