from datetime import UTC, datetime

from sqlalchemy import delete, select, update

from app.db.engine import session_context
from app.models.otp import OTPCode
from app.utils.pagination import paginate


class OTPCodeRepository:
    @property
    def _session(self):
        return session_context.get()

    async def create(self, email: str, code: str, expires_at: datetime) -> OTPCode:
        otp = OTPCode(email=email, code=code, expires_at=expires_at)
        self._session.add(otp)
        await self._session.flush()
        return otp

    async def get_valid_by_email_and_code(self, email: str, code: str) -> OTPCode | None:
        now = datetime.now(UTC)
        result = await self._session.execute(
            select(OTPCode).where(
                OTPCode.email == email,
                OTPCode.code == code,
                OTPCode.is_used == False,  # noqa: E712
                OTPCode.expires_at > now,
            )
        )
        return result.scalar_one_or_none()

    async def mark_used(self, otp: OTPCode) -> None:
        await self._session.execute(
            update(OTPCode).where(OTPCode.id == otp.id).values(is_used=True)
        )
        await self._session.flush()

    async def list_paginated(
        self, page: int, per_page: int, email: str | None = None,
    ) -> tuple[list[OTPCode], int]:
        query = select(OTPCode).order_by(OTPCode.created_at.desc())
        if email:
            query = query.where(OTPCode.email.ilike(f"%{email}%"))
        return await paginate(self._session, query, page, per_page)

    async def delete_expired(self) -> int:
        now = datetime.now(UTC)
        result = await self._session.execute(
            delete(OTPCode).where(OTPCode.expires_at < now)
        )
        await self._session.flush()
        return result.rowcount
