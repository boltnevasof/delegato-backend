import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.utils.pagination import paginate


class AgentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user_id: uuid.UUID) -> Agent:
        agent = Agent(user_id=user_id)
        self._session.add(agent)
        await self._session.flush()
        return agent

    async def get_by_user_id(self, user_id: uuid.UUID) -> Agent | None:
        result = await self._session.execute(
            select(Agent).where(Agent.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, agent_id: uuid.UUID) -> Agent | None:
        result = await self._session.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        return result.scalar_one_or_none()

    async def update(self, agent_id: uuid.UUID, **kwargs) -> Agent | None:
        await self._session.execute(
            update(Agent).where(Agent.id == agent_id).values(**kwargs)
        )
        await self._session.flush()
        return await self.get_by_id(agent_id)

    async def list_paginated(
        self, page: int, per_page: int,
    ) -> tuple[list[Agent], int]:
        query = select(Agent).order_by(Agent.created_at.desc())
        return await paginate(self._session, query, page, per_page)
