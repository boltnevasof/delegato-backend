import uuid

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, manage_session
from app.api.v1.schemas.channel import (
    ChannelListResponse,
    ChannelResponse,
    UpdateChannelRequest,
)
from app.core.container import Container
from app.models.user import User
from app.services.agent import AgentService
from app.services.channel import ChannelService

router = APIRouter(tags=["channels"])


@router.get(
    "/agents/me/channels",
    response_model=ChannelListResponse,
    summary="Список каналов агента",
    description="Возвращает все подключённые каналы связи (Telegram и др.) AI-агента текущего пользователя.",
)
@inject
@manage_session
async def get_channels(
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
    channel_service: ChannelService = Depends(Provide[Container.channel_service]),
) -> ChannelListResponse:
    agent = await agent_service.get_by_user(current_user.id)
    channels = await channel_service.get_channels(agent.id)
    return ChannelListResponse(
        channels=[
            ChannelResponse(
                id=c.id,
                channel_type=c.channel_type.value,
                status=c.status.value,
            )
            for c in channels
        ],
    )


@router.patch(
    "/agents/me/channels/{channel_id}",
    response_model=ChannelResponse,
    summary="Обновить канал",
    description="Изменяет статус канала связи агента (подключён / отключён).",
)
@inject
@manage_session
async def update_channel(
    channel_id: uuid.UUID,
    body: UpdateChannelRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
    channel_service: ChannelService = Depends(Provide[Container.channel_service]),
) -> ChannelResponse:
    await agent_service.get_by_user(current_user.id)
    channel = await channel_service.update_channel(channel_id, status=body.status)
    return ChannelResponse(
        id=channel.id,
        channel_type=channel.channel_type.value,
        status=channel.status.value,
    )
