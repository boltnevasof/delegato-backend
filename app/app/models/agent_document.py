import uuid

from sqlalchemy import Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, FullTimestampMixin, UUIDMixin


class AgentDocument(Base, UUIDMixin, FullTimestampMixin):
    """
    Сгенерированные Claude MD-документы для агента.
    Обновляются каждый раз при сохранении формы.
    is_synchronized — флаг синхронизации с OpenClaw.
    """

    __tablename__ = "agent_documents"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # ── Сгенерированные MD-документы ──────────────────────────────────────────
    user_md: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_md: Mapped[str | None] = mapped_column(Text, nullable=True)
    soul_md: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Служебное ─────────────────────────────────────────────────────────────
    is_synchronized: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false",
    )
