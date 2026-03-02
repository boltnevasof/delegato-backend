import uuid

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import AgentStatus
from app.db.base import Base, EnumValue, FullTimestampMixin, UUIDMixin


class Agent(Base, UUIDMixin, FullTimestampMixin):
    __tablename__ = "agents"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False,
    )
    status: Mapped[AgentStatus] = mapped_column(
        EnumValue(AgentStatus, name="agent_status", create_constraint=True),
        nullable=False,
        server_default=AgentStatus.PENDING_SETUP.value,
    )
    soul_md: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_md: Mapped[str | None] = mapped_column(Text, nullable=True)
    onboarding_step: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
