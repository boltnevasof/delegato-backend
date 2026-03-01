import uuid

from sqlalchemy import func, select

from app.core.constants import ServerLogLevel
from app.db.engine import session_context
from app.models.server_log import ServerLog


class ServerLogRepository:
    @property
    def _session(self):
        return session_context.get()

    async def create(
        self,
        server_id: uuid.UUID,
        level: ServerLogLevel,
        stage: str,
        message: str,
        details: dict | None = None,
    ) -> ServerLog:
        log = ServerLog(
            server_id=server_id, level=level, stage=stage,
            message=message, details=details,
        )
        self._session.add(log)
        await self._session.flush()
        return log

    async def get_by_server_id_paginated(
        self,
        server_id: uuid.UUID,
        page: int,
        per_page: int,
        level: ServerLogLevel | None = None,
    ) -> tuple[list[ServerLog], int]:
        query = select(ServerLog).where(ServerLog.server_id == server_id)
        count_query = select(func.count()).select_from(ServerLog).where(
            ServerLog.server_id == server_id,
        )

        if level is not None:
            query = query.where(ServerLog.level == level)
            count_query = count_query.where(ServerLog.level == level)

        query = query.order_by(ServerLog.created_at.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)

        result = await self._session.execute(query)
        total_result = await self._session.execute(count_query)

        return list(result.scalars().all()), total_result.scalar_one()
