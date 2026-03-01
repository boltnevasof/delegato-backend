import uuid

from sqlalchemy import Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import ServerLogLevel
from app.db.base import Base, TimestampMixin, UUIDMixin


class ServerLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "server_logs"

    server_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("servers.id", ondelete="CASCADE"), nullable=False,
    )
    level: Mapped[ServerLogLevel] = mapped_column(
        Enum(ServerLogLevel, name="server_log_level", create_constraint=True),
        nullable=False,
    )
    stage: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_server_logs_server_created", "server_id", "created_at"),
    )
