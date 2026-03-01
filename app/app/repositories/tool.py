import uuid

from sqlalchemy import select

from app.db.engine import session_context
from app.models.tool import ToolCatalog


class ToolCatalogRepository:
    @property
    def _session(self):
        return session_context.get()

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
