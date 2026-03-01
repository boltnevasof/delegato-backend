import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tool import ToolCatalog


class ToolCatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self) -> list[ToolCatalog]:
        result = await self._session.execute(
            select(ToolCatalog).where(ToolCatalog.is_active == True)  # noqa: E712
        )
        return list(result.scalars().all())

    async def get_by_id(self, tool_id: uuid.UUID) -> ToolCatalog | None:
        result = await self._session.execute(
            select(ToolCatalog).where(ToolCatalog.id == tool_id)
        )
        return result.scalar_one_or_none()
