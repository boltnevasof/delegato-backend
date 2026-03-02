import uuid

from sqlalchemy import select, update

from app.core.constants import SubscriptionStatus
from app.db.engine import session_context
from app.models.subscription import Subscription


class SubscriptionRepository:
    @property
    def _session(self):
        return session_context.get()

    async def create(self, **kwargs) -> Subscription:
        subscription = Subscription(**kwargs)
        self._session.add(subscription)
        await self._session.flush()
        return subscription

    async def get_by_user_id(self, user_id: uuid.UUID) -> Subscription | None:
        result = await self._session.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self, subscription_id: uuid.UUID, status: SubscriptionStatus, **kwargs,
    ) -> None:
        values = {"status": status, **kwargs}
        await self._session.execute(
            update(Subscription).where(Subscription.id == subscription_id).values(**values)
        )
        await self._session.flush()

    async def update(self, subscription_id: uuid.UUID, **kwargs) -> Subscription | None:
        await self._session.execute(
            update(Subscription).where(Subscription.id == subscription_id).values(**kwargs)
        )
        await self._session.flush()
        result = await self._session.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        return result.scalar_one_or_none()
