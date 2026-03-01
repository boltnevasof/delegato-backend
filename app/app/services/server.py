import uuid

from app.core.constants import ServerLogLevel, ServerStatus
from app.exceptions.base import NotFound
from app.models.server import Server
from app.repositories.agent import AgentRepository
from app.repositories.server import ServerRepository
from app.repositories.server_log import ServerLogRepository
from app.services.dto.server import ServerLogDTO, ServerStatusDTO


class ServerService:
    def __init__(
        self,
        server_repository: ServerRepository,
        agent_repository: AgentRepository,
        server_log_repository: ServerLogRepository,
    ) -> None:
        self._server_repo = server_repository
        self._agent_repo = agent_repository
        self._log_repo = server_log_repository

    async def find_by_agent(self, agent_id: uuid.UUID) -> Server | None:
        return await self._server_repo.get_by_agent_id(agent_id)

    async def create_server(self, agent_id: uuid.UUID) -> Server:
        return await self._server_repo.create(agent_id)

    async def get_by_user(self, user_id: uuid.UUID) -> ServerStatusDTO:
        agent = await self._agent_repo.get_by_user_id(user_id)
        if agent is None:
            raise NotFound(detail="Agent not found")
        server = await self._server_repo.get_by_agent_id(agent.id)
        if server is None:
            raise NotFound(detail="Server not found")
        return ServerStatusDTO(
            id=server.id,
            status=server.status.value,
            ip_address=server.ip_address,
            created_at=server.created_at,
        )

    async def get_logs(
        self,
        user_id: uuid.UUID,
        page: int,
        per_page: int,
        level: str | None = None,
    ) -> tuple[list[ServerLogDTO], int]:
        agent = await self._agent_repo.get_by_user_id(user_id)
        if agent is None:
            raise NotFound(detail="Agent not found")
        server = await self._server_repo.get_by_agent_id(agent.id)
        if server is None:
            raise NotFound(detail="Server not found")

        log_level = ServerLogLevel(level) if level else None
        items, total = await self._log_repo.get_by_server_id_paginated(
            server.id, page, per_page, level=log_level,
        )
        return [
            ServerLogDTO(
                id=log.id,
                level=log.level.value,
                stage=log.stage,
                message=log.message,
                details=log.details,
                created_at=log.created_at,
            )
            for log in items
        ], total

    async def update_status(
        self, server_id: uuid.UUID, status: ServerStatus, **kwargs: object,
    ) -> None:
        await self._server_repo.update_status(server_id, status, **kwargs)
