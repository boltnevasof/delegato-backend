from sqlalchemy import Boolean, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import SkillAccessLevel
from app.db.base import Base, TimestampMixin, UUIDMixin


class TariffPlan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tariff_plans"

    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price_rub: Mapped[int] = mapped_column(Integer, nullable=False)
    max_channels: Mapped[int | None] = mapped_column(Integer, nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    skills_access: Mapped[SkillAccessLevel] = mapped_column(
        Enum(SkillAccessLevel, name="skill_access_level", create_constraint=True),
        nullable=False,
    )
    is_self_service: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
