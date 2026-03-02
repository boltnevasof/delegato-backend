import uuid

from sqlalchemy import Boolean, Column, ForeignKey, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import SkillAccessLevel
from app.db.base import Base, EnumValue, TimestampMixin, UUIDMixin

# Junction table for skill presets
skill_preset_skills = Table(
    "skill_preset_skills",
    Base.metadata,
    Column("preset_id", UUID(as_uuid=True), ForeignKey("skill_presets.id"), primary_key=True),
    Column("skill_id", UUID(as_uuid=True), ForeignKey("skill_catalog.id"), primary_key=True),
)


class SkillCatalog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "skill_catalog"

    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    access_level: Mapped[SkillAccessLevel] = mapped_column(
        EnumValue(SkillAccessLevel, name="skill_access_level", create_constraint=True, create_type=False),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")


class SkillPreset(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "skill_presets"

    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    skills: Mapped[list["SkillCatalog"]] = relationship(
        secondary=skill_preset_skills, lazy="selectin",
    )
