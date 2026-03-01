from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.skill import SkillCatalog


class AgentSkill(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_skills"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skill_catalog.id"), nullable=False,
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    skill: Mapped[SkillCatalog] = relationship(lazy="selectin")

    __table_args__ = (
        UniqueConstraint("agent_id", "skill_id", name="uq_agent_skill"),
    )
