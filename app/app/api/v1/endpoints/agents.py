from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.v1.schemas.agent import (
    AgentDetailResponse,
    AgentMdUpdateRequest,
    AsyncTaskAcceptedResponse,
    AsyncTaskStatusResponse,
    ChannelSummary,
    EnhanceRequest,
    OnboardingCompleteResponse,
    OnboardingConnectChannelRequest,
    OnboardingConnectChannelResponse,
    OnboardingDescribeRequest,
    OnboardingSelectSkillsRequest,
    OnboardingSelectSkillsResponse,
    ServerSummary,
    SkillSummary,
    SoulMdUpdateRequest,
    ToolSummary,
)
from app.broker import broker
from app.core.container import Container
from app.models.user import User
from app.services.agent import AgentService
from app.services.channel import ChannelService

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get(
    "/me",
    response_model=AgentDetailResponse,
    summary="Получить агента",
    description="Возвращает полную информацию об AI-агенте текущего пользователя: статус, SOUL.md, навыки, инструменты, каналы и сервер.",
)
@inject
async def get_agent(
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
) -> AgentDetailResponse:
    agent = await agent_service.get_by_user(current_user.id)
    detail = await agent_service.get_detail(agent.id)
    return AgentDetailResponse(
        id=detail.id,
        status=detail.status,
        soul_md=detail.soul_md,
        agent_md=detail.agent_md,
        onboarding_step=detail.onboarding_step,
        skills=[SkillSummary(**s) for s in detail.skills],
        tools=[ToolSummary(**t) for t in detail.tools],
        channels=[ChannelSummary(**c) for c in detail.channels],
        server=ServerSummary(**detail.server) if detail.server else None,
    )


@router.post(
    "/onboarding/describe",
    status_code=202,
    summary="Онбординг: описать бизнес",
    description="Принимает текстовое описание бизнеса и запускает фоновую AI-задачу для генерации SOUL.md и AGENT.md. Возвращает task_id для отслеживания.",
)
@inject
async def onboarding_describe(
    body: OnboardingDescribeRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
) -> AsyncTaskAcceptedResponse:
    agent = await agent_service.get_by_user(current_user.id)
    task_id = await agent_service.describe(agent.id, body.business_description)
    return AsyncTaskAcceptedResponse(task_id=task_id)


@router.post(
    "/onboarding/skip-describe",
    summary="Онбординг: пропустить описание",
    description="Пропускает шаг генерации SOUL.md из описания бизнеса. Пользователь сможет заполнить SOUL.md вручную позже.",
)
@inject
async def onboarding_skip_describe(
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
) -> dict:
    agent = await agent_service.get_by_user(current_user.id)
    return await agent_service.skip_describe(agent.id)


@router.get(
    "/tasks/{task_id}/status",
    response_model=AsyncTaskStatusResponse,
    summary="Статус фоновой задачи",
    description="Проверяет статус асинхронной задачи (AI-генерация, enhance). Возвращает pending / completed / failed.",
)
async def get_task_status(task_id: str) -> AsyncTaskStatusResponse:
    result = await broker.result_backend.get_result(task_id)
    if result is None:
        return AsyncTaskStatusResponse(task_id=task_id, status="pending")

    if result.is_err:
        return AsyncTaskStatusResponse(
            task_id=task_id,
            status="failed",
            error=str(result.error) if result.error else "Unknown error",
        )

    return AsyncTaskStatusResponse(
        task_id=task_id,
        status="completed",
        result=result.return_value,
    )


@router.post(
    "/onboarding/connect-channel",
    response_model=OnboardingConnectChannelResponse,
    status_code=201,
    summary="Онбординг: подключить канал",
    description="Подключает канал связи (Telegram) к агенту на этапе онбординга. Автоматически переводит онбординг на следующий шаг.",
)
@inject
async def onboarding_connect_channel(
    body: OnboardingConnectChannelRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
    channel_service: ChannelService = Depends(Provide[Container.channel_service]),
) -> OnboardingConnectChannelResponse:
    agent = await agent_service.get_by_user(current_user.id)
    channel = await channel_service.connect_channel(agent.id, body.channel_type, body.config)
    await agent_service.update_onboarding_step(agent.id, 2)
    return OnboardingConnectChannelResponse(
        id=channel.id,
        channel_type=channel.channel_type.value,
        status=channel.status.value,
    )


@router.post(
    "/onboarding/select-skills",
    response_model=OnboardingSelectSkillsResponse,
    summary="Онбординг: выбрать навыки",
    description="Активирует выбранные навыки (по ID или пресету) для агента на этапе онбординга.",
)
@inject
async def onboarding_select_skills(
    body: OnboardingSelectSkillsRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
) -> OnboardingSelectSkillsResponse:
    agent = await agent_service.get_by_user(current_user.id)
    activated = await agent_service.select_skills(agent.id, body.skill_ids, body.preset_slug)
    await agent_service.update_onboarding_step(agent.id, 3)
    return OnboardingSelectSkillsResponse(
        activated_skills=[
            SkillSummary(id=s.skill.id, slug=s.skill.slug, is_enabled=s.is_enabled)
            for s in activated
        ],
    )


@router.post(
    "/onboarding/complete",
    response_model=OnboardingCompleteResponse,
    summary="Онбординг: завершить",
    description="Завершает онбординг агента и запускает провижининг сервера. Агент переходит в статус configuring.",
)
@inject
async def onboarding_complete(
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
) -> OnboardingCompleteResponse:
    agent = await agent_service.get_by_user(current_user.id)
    agent = await agent_service.complete_onboarding(agent.id)
    return OnboardingCompleteResponse(status=agent.status.value)


@router.put(
    "/me/soul-md",
    summary="Обновить SOUL.md",
    description="Заменяет содержимое SOUL.md агента. SOUL.md определяет личность, тон и поведение AI-агента.",
)
@inject
async def update_soul_md(
    body: SoulMdUpdateRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
) -> dict:
    agent = await agent_service.get_by_user(current_user.id)
    await agent_service.update_soul_md(agent.id, body.content)
    return {"content": body.content}


@router.put(
    "/me/agent-md",
    summary="Обновить AGENT.md",
    description="Заменяет содержимое AGENT.md агента. AGENT.md определяет инструкции, бизнес-правила и контекст работы агента.",
)
@inject
async def update_agent_md(
    body: AgentMdUpdateRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
) -> dict:
    agent = await agent_service.get_by_user(current_user.id)
    await agent_service.update_agent_md(agent.id, body.content)
    return {"content": body.content}


@router.post(
    "/me/enhance",
    status_code=202,
    summary="AI-улучшение контента",
    description="Запускает фоновую AI-задачу для улучшения SOUL.md или AGENT.md. Возвращает task_id для отслеживания результата.",
)
@inject
async def enhance_content(
    body: EnhanceRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
) -> AsyncTaskAcceptedResponse:
    agent = await agent_service.get_by_user(current_user.id)
    task_id = await agent_service.request_enhance(agent.id, body.field, body.content)
    return AsyncTaskAcceptedResponse(task_id=task_id, message="AI enhancement started")
