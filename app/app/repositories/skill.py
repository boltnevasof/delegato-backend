import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import SkillAccessLevel
from app.models.skill import SkillCatalog, SkillPreset


class SkillCatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self) -> list[SkillCatalog]:
        result = await self._session.execute(
            select(SkillCatalog).where(SkillCatalog.is_active == True)  # noqa: E712
        )
        return list(result.scalars().all())

    async def get_by_id(self, skill_id: uuid.UUID) -> SkillCatalog | None:
        result = await self._session.execute(
            select(SkillCatalog).where(SkillCatalog.id == skill_id)
        )
        return result.scalar_one_or_none()

    async def get_by_ids(self, skill_ids: list[uuid.UUID]) -> list[SkillCatalog]:
        result = await self._session.execute(
            select(SkillCatalog).where(SkillCatalog.id.in_(skill_ids))
        )
        return list(result.scalars().all())

    async def get_by_access_level(self, level: SkillAccessLevel) -> list[SkillCatalog]:
        result = await self._session.execute(
            select(SkillCatalog).where(
                SkillCatalog.is_active == True,  # noqa: E712
                SkillCatalog.access_level == level,
            )
        )
        return list(result.scalars().all())

    async def list_presets(self) -> list[SkillPreset]:
        result = await self._session.execute(select(SkillPreset))
        return list(result.scalars().all())

    async def get_preset_by_slug(self, slug: str) -> SkillPreset | None:
        result = await self._session.execute(
            select(SkillPreset).where(SkillPreset.slug == slug)
        )
        return result.scalar_one_or_none()
