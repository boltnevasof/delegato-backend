from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from taskiq_redis.exceptions import ResultIsMissingError

from app.api.deps import get_current_user, manage_session
from app.api.v1.schemas.agent import (
    AgentAboutRequest,
    AgentAboutResponse,
    AgentDetailResponse,
    AsyncTaskAcceptedResponse,
    AsyncTaskStatusResponse,
    ChannelSummary,
    OnboardingAnswerEntry,
    OnboardingAnswerRequest,
    OnboardingCompleteResponse,
    OnboardingConnectChannelRequest,
    OnboardingConnectChannelResponse,
    OnboardingDescribeRequest,
    OnboardingSelectSkillsRequest,
    OnboardingSelectSkillsResponse,
    OnboardingStateResponse,
    OnboardingStepRequest,
    ServerSummary,
    SkillSummary,
    ToolSummary,
)
from app.broker import broker
from app.core.container import Container
from app.models.user import User
from app.repositories.agent_profile import AgentProfileRepository
from app.repositories.agent_document import AgentDocumentRepository
from app.services.agent import AgentService
from app.services.channel import ChannelService
from app.tasks.ai import generate_about_task

# ── Вопросы onboarding (захардкожены) ────────────────────────────────────────
# question_id совпадает с полями AgentProfile

ONBOARDING_QUESTIONS = [
    {"question_id": "name", "step": 1},
    {"question_id": "location", "step": 2},
    {"question_id": "occupation", "step": 3},
    {"question_id": "about_self", "step": 4},
    {"question_id": "agent_restrictions", "step": 5},
]

VALID_QUESTION_IDS = {q["question_id"] for q in ONBOARDING_QUESTIONS}

# Шаг 6 означает «onboarding завершён»
ONBOARDING_COMPLETED_STEP = 6

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get(
    "/me",
    response_model=AgentDetailResponse,
    summary="Получить агента",
    description="Возвращает полную информацию об AI-агенте текущего пользователя.",
)
@inject
@manage_session
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


# ── Настройки агента (about) ───────────────────────────────────────────────────

@router.get(
    "/me/about",
    response_model=AgentAboutResponse,
    summary="Получить настройки агента",
    description="Возвращает поля формы и сгенерированные MD-документы для текущего пользователя.",
)
@inject
@manage_session
async def get_agent_about(
    current_user: User = Depends(get_current_user),
    profile_repo: AgentProfileRepository = Depends(Provide[Container.agent_profile_repository]),
    doc_repo: AgentDocumentRepository = Depends(Provide[Container.agent_document_repository]),
) -> AgentAboutResponse:
    profile = await profile_repo.get_by_user_id(current_user.id)
    doc = await doc_repo.get_by_user_id(current_user.id)
    return AgentAboutResponse(
        name=profile.name if profile else None,
        location=profile.location if profile else None,
        about_self=profile.about_self if profile else None,
        occupation=profile.occupation if profile else None,
        agent_restrictions=profile.agent_restrictions if profile else None,
        user_md=doc.user_md if doc else None,
        agent_md=doc.agent_md if doc else None,
        soul_md=doc.soul_md if doc else None,
        is_synchronized=doc.is_synchronized if doc else False,
    )


@router.put(
    "/me/about",
    status_code=202,
    response_model=AsyncTaskAcceptedResponse,
    summary="Сохранить настройки агента",
    description=(
        "Сохраняет поля формы в agent_profiles и запускает фоновую AI-задачу "
        "для генерации user_md, agent_md, soul_md. Возвращает task_id."
    ),
)
@inject
@manage_session
async def save_agent_about(
    body: AgentAboutRequest,
    current_user: User = Depends(get_current_user),
    profile_repo: AgentProfileRepository = Depends(Provide[Container.agent_profile_repository]),
) -> AsyncTaskAcceptedResponse:
    # Сохраняем данные формы немедленно
    await profile_repo.upsert(
        current_user.id,
        name=body.name,
        location=body.location,
        about_self=body.about_self,
        occupation=body.occupation,
        agent_restrictions=body.agent_restrictions,
    )

    # Запускаем генерацию MD в фоне
    task = await generate_about_task.kiq(
        user_id=str(current_user.id),
        name=body.name,
        location=body.location,
        about_self=body.about_self,
        occupation=body.occupation,
        agent_restrictions=body.agent_restrictions,
    )
    return AsyncTaskAcceptedResponse(
        task_id=task.task_id,
        message="Настройки сохранены, генерация MD запущена",
    )


# ── Онбординг ─────────────────────────────────────────────────────────────────

@router.post(
    "/onboarding/describe",
    status_code=202,
    summary="Онбординг: описать бизнес",
    description="Принимает текстовое описание бизнеса и запускает AI-задачу для генерации SOUL.md и AGENT.md.",
)
@inject
@manage_session
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
)
@inject
@manage_session
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
)
@manage_session
async def get_task_status(task_id: str) -> AsyncTaskStatusResponse:
    try:
        result = await broker.result_backend.get_result(task_id)
    except ResultIsMissingError:
        return AsyncTaskStatusResponse(task_id=task_id, status="pending")
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
)
@inject
@manage_session
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
)
@inject
@manage_session
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
)
@inject
@manage_session
async def onboarding_complete(
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
) -> OnboardingCompleteResponse:
    agent = await agent_service.get_by_user(current_user.id)
    agent = await agent_service.complete_onboarding(agent.id)
    return OnboardingCompleteResponse(status=agent.status.value)


# ── Новый onboarding (пошаговая форма) ───────────────────────────────────────

@router.get(
    "/onboarding/state",
    response_model=OnboardingStateResponse,
    summary="Получить состояние onboarding",
    description="Возвращает текущий шаг, статус завершённости и уже сохранённые ответы.",
)
@inject
@manage_session
async def get_onboarding_state(
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
    profile_repo: AgentProfileRepository = Depends(Provide[Container.agent_profile_repository]),
) -> OnboardingStateResponse:
    agent = await agent_service.get_by_user(current_user.id)
    profile = await profile_repo.get_by_user_id(current_user.id)

    answers: list[OnboardingAnswerEntry] = []
    for q in ONBOARDING_QUESTIONS:
        qid = q["question_id"]
        value = getattr(profile, qid, None) if profile else None
        answers.append(OnboardingAnswerEntry(question_id=qid, answer=value))

    return OnboardingStateResponse(
        current_step=agent.onboarding_step,
        is_completed=agent.onboarding_step >= ONBOARDING_COMPLETED_STEP,
        answers=answers,
    )


@router.post(
    "/onboarding/answer",
    summary="Сохранить ответ на шаге onboarding",
    description="Сохраняет или обновляет ответ пользователя по question_id.",
)
@inject
@manage_session
async def save_onboarding_answer(
    body: OnboardingAnswerRequest,
    current_user: User = Depends(get_current_user),
    profile_repo: AgentProfileRepository = Depends(Provide[Container.agent_profile_repository]),
) -> dict:
    if body.question_id not in VALID_QUESTION_IDS:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Invalid question_id: {body.question_id}")

    await profile_repo.upsert(current_user.id, **{body.question_id: body.answer})
    return {"status": "ok"}


@router.post(
    "/onboarding/step",
    summary="Обновить текущий шаг onboarding",
    description="Сохраняет номер текущего шага, чтобы при возвращении пользователь попал на нужный экран.",
)
@inject
@manage_session
async def update_onboarding_step(
    body: OnboardingStepRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
) -> dict:
    agent = await agent_service.get_by_user(current_user.id)
    await agent_service.update_onboarding_step(agent.id, body.step)
    return {"status": "ok"}


@router.post(
    "/onboarding/finish",
    status_code=202,
    response_model=AsyncTaskAcceptedResponse,
    summary="Завершить onboarding и запустить генерацию",
    description=(
        "Помечает onboarding как завершённый, читает сохранённые raw-ответы "
        "из agent_profiles и запускает фоновую генерацию user_md, agent_md, soul_md."
    ),
)
@inject
@manage_session
async def finish_onboarding(
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
    profile_repo: AgentProfileRepository = Depends(Provide[Container.agent_profile_repository]),
) -> AsyncTaskAcceptedResponse:
    agent = await agent_service.get_by_user(current_user.id)

    # Помечаем onboarding как завершённый
    await agent_service.update_onboarding_step(agent.id, ONBOARDING_COMPLETED_STEP)

    # Читаем финальные raw-ответы
    profile = await profile_repo.get_by_user_id(current_user.id)

    # Запускаем генерацию через существующий таск (Cloud API)
    task = await generate_about_task.kiq(
        user_id=str(current_user.id),
        name=profile.name if profile else None,
        location=profile.location if profile else None,
        about_self=profile.about_self if profile else None,
        occupation=profile.occupation if profile else None,
        agent_restrictions=profile.agent_restrictions if profile else None,
    )
    return AsyncTaskAcceptedResponse(
        task_id=task.task_id,
        message="Onboarding завершён, генерация MD запущена",
    )
