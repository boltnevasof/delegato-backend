import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import ServerStatus
from app.db.base import Base, EnumValue, FullTimestampMixin, UUIDMixin


class Server(Base, UUIDMixin, FullTimestampMixin):
    __tablename__ = "servers"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), unique=True, nullable=False,
    )
    status: Mapped[ServerStatus] = mapped_column(
        EnumValue(ServerStatus, name="server_status", create_constraint=True),
        nullable=False,
        server_default=ServerStatus.PROVISIONING.value,
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    tfstate_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    openclaw_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    provider_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
