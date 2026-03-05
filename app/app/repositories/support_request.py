from sqlalchemy import select

from app.core.constants import SupportRequestStatus
from app.db.engine import session_context
from app.models.support_request import SupportRequest
from app.utils.pagination import paginate


class SupportRequestRepository:
    @property
    def _session(self):
        return session_context.get()

    async def create(self, **kwargs) -> SupportRequest:
        request = SupportRequest(**kwargs)
        self._session.add(request)
        await self._session.flush()
        return request

    async def list_paginated(
        self,
        page: int,
        per_page: int,
        status: SupportRequestStatus | None = None,
    ) -> tuple[list[SupportRequest], int]:
        query = select(SupportRequest).order_by(SupportRequest.created_at.desc())
        if status is not None:
            query = query.where(SupportRequest.status == status)
        return await paginate(self._session, query, page, per_page)
