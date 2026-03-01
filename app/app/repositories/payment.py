import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import PaymentStatus
from app.models.payment import Payment
from app.utils.pagination import paginate


class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, **kwargs) -> Payment:
        payment = Payment(**kwargs)
        self._session.add(payment)
        await self._session.flush()
        return payment

    async def get_by_idempotency_key(self, key: str) -> Payment | None:
        result = await self._session.execute(
            select(Payment).where(Payment.idempotency_key == key)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id_paginated(
        self, user_id: uuid.UUID, page: int, per_page: int,
    ) -> tuple[list[Payment], int]:
        query = (
            select(Payment)
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
        )
        return await paginate(self._session, query, page, per_page)

    async def update_status(
        self, payment_id: uuid.UUID, status: PaymentStatus, **kwargs,
    ) -> None:
        values = {"status": status, **kwargs}
        await self._session.execute(
            update(Payment).where(Payment.id == payment_id).values(**values)
        )
        await self._session.flush()
