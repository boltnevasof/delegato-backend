import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import AuthProvider, UserRole
from app.db.base import Base, FullTimestampMixin, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, FullTimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", create_constraint=True),
        nullable=False,
        server_default=UserRole.USER.value,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    auth_methods: Mapped[list["UserAuthMethod"]] = relationship(
        back_populates="user", lazy="selectin",
    )


class UserAuthMethod(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "user_auth_methods"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    provider: Mapped[AuthProvider] = mapped_column(
        Enum(AuthProvider, name="auth_provider", create_constraint=True), nullable=False,
    )
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    user: Mapped["User"] = relationship(back_populates="auth_methods")

    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_auth_method_provider_id"),
    )
