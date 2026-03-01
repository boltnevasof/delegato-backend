import uuid

from sqlalchemy import select

from app.db.engine import session_context
from app.models.tariff import TariffPlan


class TariffRepository:
    @property
    def _session(self):
        return session_context.get()

    async def list_active(self) -> list[TariffPlan]:
        result = await self._session.execute(
            select(TariffPlan).where(TariffPlan.is_active == True)  # noqa: E712
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
