import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.db.engine import session_context
from app.models.agent_profile import AgentProfile


class AgentProfileRepository:
    @property
    def _session(self):
        return session_context.get()

    async def get_by_user_id(self, user_id: uuid.UUID) -> AgentProfile | None:
        result = await self._session.execute(
            select(AgentProfile).where(AgentProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def upsert(self, user_id: uuid.UUID, **kwargs) -> AgentProfile:
        """
        Создаёт запись если её нет, или обновляет существующую.
        Конфликт разрешается по user_id (unique constraint).
        """
        stmt = (
            insert(AgentProfile)
            .values(user_id=user_id, **kwargs)
            .on_conflict_do_update(
                index_elements=["user_id"],
                set_={k: v for k, v in kwargs.items()},
            )
            .returning(AgentProfile)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.scalar_one()
