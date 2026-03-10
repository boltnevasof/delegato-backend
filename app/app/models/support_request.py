import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import SupportRequestStatus
from app.db.base import Base, EnumValue, FullTimestampMixin, UUIDMixin


class SupportRequest(Base, UUIDMixin, FullTimestampMixin):
    __tablename__ = "support_requests"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    topic: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    contact_method: Mapped[str] = mapped_column(String(50), nullable=False)
    contact: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[SupportRequestStatus] = mapped_column(
        EnumValue(SupportRequestStatus, name="support_request_status", create_constraint=True),
        nullable=False,
        server_default=SupportRequestStatus.NEW.value,
    )
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
