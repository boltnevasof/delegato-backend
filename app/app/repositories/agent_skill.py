import uuid

from sqlalchemy import delete, select, update

from app.db.engine import session_context
from app.models.agent_skill import AgentSkill


class AgentSkillRepository:
    @property
    def _session(self):
        return session_context.get()

    async def create(self, agent_id: uuid.UUID, skill_id: uuid.UUID) -> AgentSkill:
        agent_skill = AgentSkill(agent_id=agent_id, skill_id=skill_id)
        self._session.add(agent_skill)
        await self._session.flush()
        return agent_skill

    async def get_by_agent_id(self, agent_id: uuid.UUID) -> list[AgentSkill]:
        result = await self._session.execute(
            select(AgentSkill).where(AgentSkill.agent_id == agent_id)
        )
        return list(result.scalars().all())

    async def get_by_agent_and_skill(
        self, agent_id: uuid.UUID, skill_id: uuid.UUID,
    ) -> AgentSkill | None:
        result = await self._session.execute(
            select(AgentSkill).where(
                AgentSkill.agent_id == agent_id,
                AgentSkill.skill_id == skill_id,
            )
        )
        return result.scalar_one_or_none()

    async def update(self, agent_skill_id: uuid.UUID, **kwargs) -> None:
        await self._session.execute(
            update(AgentSkill).where(AgentSkill.id == agent_skill_id).values(**kwargs)
        )
        await self._session.flush()

    async def delete(self, agent_skill_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(AgentSkill).where(AgentSkill.id == agent_skill_id)
        )
        await self._session.flush()
