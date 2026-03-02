from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, manage_session
from app.api.v1.schemas.user import AgentSummary, SubscriptionSummary, UserProfileResponse
from app.core.container import Container
from app.models.user import User
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Получить профиль",
    description="Возвращает профиль текущего пользователя: данные аккаунта, методы авторизации, агента и подписку.",
)
@inject
@manage_session
async def get_profile(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(Provide[Container.user_service]),
) -> UserProfileResponse:
    profile = await user_service.get_profile(current_user.id)
    agent = None
    if profile.agent:
        agent = AgentSummary(
            id=profile.agent.id,
            status=profile.agent.status,
            onboarding_step=profile.agent.onboarding_step,
        )
    subscription = None
    if profile.subscription:
        subscription = SubscriptionSummary(
            id=profile.subscription.id,
            tariff_slug=profile.subscription.tariff_slug,
            status=profile.subscription.status,
            current_period_end=profile.subscription.current_period_end,
        )
    return UserProfileResponse(
        id=profile.id,
        email=profile.email,
        name=profile.name,
        role=profile.role,
        auth_methods=profile.auth_methods,
        created_at=profile.created_at,
        agent=agent,
        subscription=subscription,
    )
