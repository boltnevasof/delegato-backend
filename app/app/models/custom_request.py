import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import CustomRequestStatus
from app.db.base import Base, FullTimestampMixin, UUIDMixin


class CustomTariffRequest(Base, UUIDMixin, FullTimestampMixin):
    __tablename__ = "custom_tariff_requests"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    contact_info: Mapped[str] = mapped_column(String(500), nullable=False)
    requirements: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[CustomRequestStatus] = mapped_column(
        Enum(CustomRequestStatus, name="custom_request_status", create_constraint=True),
        nullable=False,
        server_default=CustomRequestStatus.NEW.value,
    )
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
