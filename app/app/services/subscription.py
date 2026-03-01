import uuid
from datetime import datetime, timedelta, timezone

from app.core.constants import SubscriptionStatus
from app.exceptions.base import BadRequest, NotFound
from app.models.subscription import Subscription
from app.repositories.subscription import SubscriptionRepository
from app.repositories.tariff import TariffRepository


class SubscriptionService:
    GRACE_PERIOD_DAYS = 3

    def __init__(
        self,
        subscription_repository: SubscriptionRepository,
        tariff_repository: TariffRepository,
    ) -> None:
        self._repo = subscription_repository
        self._tariff_repo = tariff_repository

    async def create_subscription(
        self,
        user_id: uuid.UUID,
        tariff_plan_id: uuid.UUID,
        current_period_start: datetime,
        current_period_end: datetime,
        payment_method_token: str | None = None,
    ) -> Subscription:
        return await self._repo.create(
            user_id=user_id,
            tariff_plan_id=tariff_plan_id,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            payment_method_token=payment_method_token,
        )

    async def get_current(self, user_id: uuid.UUID) -> Subscription:
        sub = await self._repo.get_by_user_id(user_id)
        if sub is None:
            raise NotFound(detail="No active subscription")
        return sub

    async def update_status(
        self, subscription_id: uuid.UUID, status: SubscriptionStatus, **kwargs: object,
    ) -> None:
        await self._repo.update_status(subscription_id, status, **kwargs)

    async def change_tariff(
        self, user_id: uuid.UUID, new_tariff_id: uuid.UUID,
    ) -> dict:
        sub = await self.get_current(user_id)
        if sub.status not in (SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE):
            raise BadRequest(detail="Cannot change tariff in current subscription state")

        new_tariff = await self._tariff_repo.get_by_id(new_tariff_id)
        if new_tariff is None:
            raise NotFound(detail="Tariff not found")

        now = datetime.now(timezone.utc)
        total_days = (sub.current_period_end - sub.current_period_start).days
        remaining_days = max((sub.current_period_end - now).days, 0)
        old_tariff = sub.tariff_plan

        proration = 0
        if total_days > 0:
            daily_old = old_tariff.price_rub / total_days
            daily_new = new_tariff.price_rub / total_days
            proration = int((daily_new - daily_old) * remaining_days)

        await self._repo.update(
            sub.id,
            tariff_plan_id=new_tariff_id,
        )

        updated = await self._repo.get_by_user_id(user_id)
        return {
            "subscription": updated,
            "proration_amount_rub": max(proration, 0),
        }

    async def cancel(self, user_id: uuid.UUID, reason: str) -> dict:
        sub = await self.get_current(user_id)
        if sub.status == SubscriptionStatus.CANCELLED:
            raise BadRequest(detail="Subscription already cancelled")

        now = datetime.now(timezone.utc)
        grace_end = sub.current_period_end + timedelta(days=self.GRACE_PERIOD_DAYS)

        await self._repo.update(
            sub.id,
            status=SubscriptionStatus.CANCELLED,
            cancel_reason=reason,
            cancelled_at=now,
            grace_period_end=grace_end,
        )

        return {
            "status": SubscriptionStatus.CANCELLED.value,
            "grace_period_end": grace_end.isoformat(),
        }

    async def reactivate(self, user_id: uuid.UUID) -> Subscription:
        sub = await self.get_current(user_id)
        if sub.status != SubscriptionStatus.CANCELLED:
            raise BadRequest(detail="Only cancelled subscriptions can be reactivated")

        now = datetime.now(timezone.utc)
        if sub.grace_period_end and now > sub.grace_period_end:
            raise BadRequest(detail="Grace period has expired")

        updated = await self._repo.update(
            sub.id,
            status=SubscriptionStatus.ACTIVE,
            cancel_reason=None,
            cancelled_at=None,
            grace_period_end=None,
        )
        return updated

    async def expire_grace_period(self, subscription_id: uuid.UUID) -> None:
        await self._repo.update_status(subscription_id, SubscriptionStatus.EXPIRED)
