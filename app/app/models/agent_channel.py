import uuid

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import ChannelStatus, ChannelType
from app.db.base import Base, FullTimestampMixin, UUIDMixin


class AgentChannel(Base, UUIDMixin, FullTimestampMixin):
    __tablename__ = "agent_channels"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    channel_type: Mapped[ChannelType] = mapped_column(
        Enum(ChannelType, name="channel_type", create_constraint=True),
        nullable=False,
    )
    channel_config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[ChannelStatus] = mapped_column(
        Enum(ChannelStatus, name="channel_status", create_constraint=True),
        nullable=False,
        server_default=ChannelStatus.CONNECTED.value,
    )
