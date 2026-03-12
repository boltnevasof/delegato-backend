import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.db.engine import session_context
from app.models.agent_document import AgentDocument


class AgentDocumentRepository:
    @property
    def _session(self):
        return session_context.get()

    async def get_by_user_id(self, user_id: uuid.UUID) -> AgentDocument | None:
        result = await self._session.execute(
            select(AgentDocument).where(AgentDocument.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        user_id: uuid.UUID,
        *,
        user_md: str,
        agent_md: str,
        soul_md: str,
    ) -> AgentDocument:
        """Создаёт или перезаписывает MD-документы, сбрасывает is_synchronized."""
        stmt = (
            insert(AgentDocument)
            .values(
                user_id=user_id,
                user_md=user_md,
                agent_md=agent_md,
                soul_md=soul_md,
                is_synchronized=False,
            )
            .on_conflict_do_update(
                index_elements=["user_id"],
                set_={
                    "user_md": user_md,
                    "agent_md": agent_md,
                    "soul_md": soul_md,
                    "is_synchronized": False,
                },
            )
            .returning(AgentDocument)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.scalar_one()
