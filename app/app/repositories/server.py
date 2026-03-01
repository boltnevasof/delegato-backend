import uuid

from sqlalchemy import func, select, update

from app.core.constants import ServerStatus
from app.db.engine import session_context
from app.models.server import Server
from app.utils.pagination import paginate


class ServerRepository:
    @property
    def _session(self):
        return session_context.get()

    async def create(self, agent_id: uuid.UUID) -> Server:
        server = Server(agent_id=agent_id)
        self._session.add(server)
        await self._session.flush()
        return server

    async def get_by_agent_id(self, agent_id: uuid.UUID) -> Server | None:
        result = await self._session.execute(
            select(Server).where(Server.agent_id == agent_id)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self, server_id: uuid.UUID, status: ServerStatus, **kwargs,
    ) -> None:
        values = {"status": status, **kwargs}
        await self._session.execute(
            update(Server).where(Server.id == server_id).values(**values)
        )
        await self._session.flush()

    async def get_by_id(self, server_id: uuid.UUID) -> Server | None:
        result = await self._session.execute(
            select(Server).where(Server.id == server_id),
        )
        return result.scalar_one_or_none()

    async def update(self, server_id: uuid.UUID, **kwargs) -> Server | None:
        await self._session.execute(
            update(Server).where(Server.id == server_id).values(**kwargs)
        )
        await self._session.flush()
        return await self.get_by_id(server_id)

    async def list_paginated(
        self, page: int, per_page: int, status: ServerStatus | None = None,
    ) -> tuple[list[Server], int]:
        query = select(Server).order_by(Server.created_at.desc())
        if status is not None:
            query = query.where(Server.status == status)
        return await paginate(self._session, query, page, per_page)

    async def get_stats(self) -> dict[str, int]:
        result = await self._session.execute(
            select(Server.status, func.count()).group_by(Server.status),
        )
        stats = {row[0].value: row[1] for row in result.all()}
        total = sum(stats.values())
        return {"total": total, **stats}
