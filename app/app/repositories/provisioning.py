import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update

from app.core.constants import ProvisioningTaskStatus
from app.db.engine import session_context
from app.models.provisioning import ProvisioningTask


class ProvisioningTaskRepository:
    @property
    def _session(self):
        return session_context.get()

    async def create(self, **kwargs) -> ProvisioningTask:
        task = ProvisioningTask(**kwargs)
        self._session.add(task)
        await self._session.flush()
        return task

    async def get_by_server_id(self, server_id: uuid.UUID) -> list[ProvisioningTask]:
        result = await self._session.execute(
            select(ProvisioningTask)
            .where(ProvisioningTask.server_id == server_id)
            .order_by(ProvisioningTask.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(
        self, task_id: uuid.UUID, status: ProvisioningTaskStatus, **kwargs,
    ) -> None:
        values: dict = {"status": status, **kwargs}
        if status == ProvisioningTaskStatus.RUNNING:
            values.setdefault("started_at", datetime.now(UTC))
        elif status in (ProvisioningTaskStatus.COMPLETED, ProvisioningTaskStatus.FAILED):
            values.setdefault("completed_at", datetime.now(UTC))
        await self._session.execute(
            update(ProvisioningTask).where(ProvisioningTask.id == task_id).values(**values)
        )
        await self._session.flush()

    async def increment_retry(self, task_id: uuid.UUID) -> None:
        await self._session.execute(
            update(ProvisioningTask)
            .where(ProvisioningTask.id == task_id)
            .values(retry_count=ProvisioningTask.retry_count + 1)
        )
        await self._session.flush()
