import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select, update

from app.core.constants import NotificationStatus
from app.db.engine import session_context
from app.models.notification import Notification


class NotificationRepository:
    @property
    def _session(self):
        return session_context.get()

    async def create(self, **kwargs) -> Notification:
        notification = Notification(**kwargs)
        self._session.add(notification)
        await self._session.flush()
        return notification

    async def get_by_user_id_paginated(
        self, user_id: uuid.UUID, page: int, per_page: int,
    ) -> tuple[list[Notification], int]:
        query = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        count_query = (
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id)
        )

        result = await self._session.execute(query)
        total_result = await self._session.execute(count_query)
        return list(result.scalars().all()), total_result.scalar_one()

    async def update_status(
        self, notification_id: uuid.UUID, status: NotificationStatus,
    ) -> None:
        values: dict = {"status": status}
        if status == NotificationStatus.SENT:
            values["sent_at"] = datetime.now(timezone.utc)

        await self._session.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .values(**values),
        )
        await self._session.flush()
