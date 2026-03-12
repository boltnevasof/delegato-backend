import uuid

from sqlalchemy import delete as sa_delete, func, select, update

from app.db.engine import session_context
from app.models.tariff import TariffPlan


class TariffRepository:
    @property
    def _session(self):
        return session_context.get()

    async def list_active(self) -> list[TariffPlan]:
        result = await self._session.execute(
            select(TariffPlan)
            .where(TariffPlan.is_active == True)  # noqa: E712
        )
        return list(result.scalars().all())

    async def get_by_id(self, tariff_id: uuid.UUID) -> TariffPlan | None:
        result = await self._session.execute(
            select(TariffPlan).where(TariffPlan.id == tariff_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> TariffPlan | None:
        result = await self._session.execute(
            select(TariffPlan).where(TariffPlan.slug == slug)
        )
        return result.scalar_one_or_none()

    async def list_paginated(
        self, page: int, per_page: int,
    ) -> tuple[list[TariffPlan], int]:
        total_result = await self._session.execute(select(func.count(TariffPlan.id)))
        total = total_result.scalar() or 0

        offset = (page - 1) * per_page
        result = await self._session.execute(
            select(TariffPlan).order_by(TariffPlan.created_at.desc()).offset(offset).limit(per_page)
        )
        return list(result.scalars().all()), total

    async def create(self, **kwargs) -> TariffPlan:
        tariff = TariffPlan(**kwargs)
        self._session.add(tariff)
        await self._session.flush()
        return tariff

    async def update(self, tariff_id: uuid.UUID, **kwargs) -> TariffPlan | None:
        await self._session.execute(
            update(TariffPlan).where(TariffPlan.id == tariff_id).values(**kwargs)
        )
        await self._session.flush()
        return await self.get_by_id(tariff_id)

    async def delete(self, tariff_id: uuid.UUID) -> None:
        await self._session.execute(
            sa_delete(TariffPlan).where(TariffPlan.id == tariff_id)
        )
        await self._session.flush()
