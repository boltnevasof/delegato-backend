import uuid

from app.exceptions.base import NotFound
from app.repositories.agent import AgentRepository
from app.repositories.subscription import SubscriptionRepository
from app.repositories.tariff import TariffRepository
from app.repositories.user import UserRepository
from app.services.dto.user import AgentSummaryDTO, SubscriptionSummaryDTO, UserProfileDTO


class UserService:
    def __init__(
        self,
        user_repository: UserRepository,
        agent_repository: AgentRepository,
        subscription_repository: SubscriptionRepository,
        tariff_repository: TariffRepository,
    ) -> None:
        self._user_repo = user_repository
        self._agent_repo = agent_repository
        self._subscription_repo = subscription_repository
        self._tariff_repo = tariff_repository

    async def get_profile(self, user_id: uuid.UUID) -> UserProfileDTO:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFound(detail="User not found")

        auth_methods = [am.provider.value for am in user.auth_methods]

        agent_summary = None
        agent = await self._agent_repo.get_by_user_id(user_id)
        if agent:
            agent_summary = AgentSummaryDTO(
                id=agent.id,
                status=agent.status.value,
                onboarding_step=agent.onboarding_step,
            )

        subscription_summary = None
        sub = await self._subscription_repo.get_by_user_id(user_id)
        if sub:
            tariff = await self._tariff_repo.get_by_id(sub.tariff_plan_id)
            subscription_summary = SubscriptionSummaryDTO(
                id=sub.id,
                tariff_slug=tariff.slug if tariff else "unknown",
                status=sub.status.value,
                current_period_end=sub.current_period_end,
            )

        return UserProfileDTO(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role.value,
            auth_methods=auth_methods,
            created_at=user.created_at,
            agent=agent_summary,
            subscription=subscription_summary,
        )
