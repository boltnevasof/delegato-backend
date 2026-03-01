import uuid

from app.core.constants import ChannelStatus, ChannelType
from app.exceptions.base import BadRequest, NotFound
from app.models.agent_channel import AgentChannel
from app.repositories.agent_channel import AgentChannelRepository


class ChannelService:
    def __init__(self, agent_channel_repository: AgentChannelRepository) -> None:
        self._repo = agent_channel_repository

    async def connect_channel(
        self,
        agent_id: uuid.UUID,
        channel_type: str,
        config: dict,
        max_channels: int | None = None,
    ) -> AgentChannel:
        if max_channels is not None:
            current_count = await self._repo.count_by_agent(agent_id)
            if current_count >= max_channels:
                raise BadRequest(
                    detail=f"Maximum {max_channels} channels allowed on your tariff",
                )

        return await self._repo.create(
            agent_id=agent_id,
            channel_type=ChannelType(channel_type),
            channel_config=config,
            status=ChannelStatus.CONNECTED,
        )

    async def get_channels(self, agent_id: uuid.UUID) -> list[AgentChannel]:
        return await self._repo.get_by_agent_id(agent_id)

    async def update_channel(
        self, channel_id: uuid.UUID, **kwargs: object,
    ) -> AgentChannel:
        channel = await self._repo.update(channel_id, **kwargs)
        if channel is None:
            raise NotFound(detail="Channel not found")
        return channel
