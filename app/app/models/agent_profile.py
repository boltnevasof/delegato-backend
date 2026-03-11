import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, FullTimestampMixin, UUIDMixin


class AgentProfile(Base, UUIDMixin, FullTimestampMixin):
    """
    Профиль агента: сырые поля формы, заполненные пользователем.
    Связь: один пользователь — одна запись (unique на user_id).
    """

    __tablename__ = "agent_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # ── Поля формы ────────────────────────────────────────────────────────────
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    about_self: Mapped[str | None] = mapped_column(Text, nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    agent_restrictions: Mapped[str | None] = mapped_column(Text, nullable=True)
