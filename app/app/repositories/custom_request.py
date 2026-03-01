import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import CustomRequestStatus
from app.models.custom_request import CustomTariffRequest
from app.utils.pagination import paginate


class CustomTariffRequestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, **kwargs) -> CustomTariffRequest:
        request = CustomTariffRequest(**kwargs)
        self._session.add(request)
        await self._session.flush()
        return request

    async def list_paginated(
        self, page: int, per_page: int, status: CustomRequestStatus | None = None,
    ) -> tuple[list[CustomTariffRequest], int]:
        query = select(CustomTariffRequest).order_by(CustomTariffRequest.created_at.desc())
        if status is not None:
            query = query.where(CustomTariffRequest.status == status)
        return await paginate(self._session, query, page, per_page)

    async def update_status(
        self, request_id: uuid.UUID, status: CustomRequestStatus, **kwargs,
    ) -> None:
        values = {"status": status, **kwargs}
        await self._session.execute(
            update(CustomTariffRequest)
            .where(CustomTariffRequest.id == request_id)
            .values(**values)
        )
        await self._session.flush()
