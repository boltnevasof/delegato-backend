import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import ProvisioningTaskStatus, ProvisioningTaskType
from app.db.base import Base, TimestampMixin, UUIDMixin


class ProvisioningTask(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "provisioning_tasks"

    server_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    task_type: Mapped[ProvisioningTaskType] = mapped_column(
        Enum(ProvisioningTaskType, name="provisioning_task_type", create_constraint=True),
        nullable=False,
    )
    status: Mapped[ProvisioningTaskStatus] = mapped_column(
        Enum(ProvisioningTaskStatus, name="provisioning_task_status", create_constraint=True),
        nullable=False,
        server_default=ProvisioningTaskStatus.PENDING.value,
    )
    taskiq_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, server_default="3")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
