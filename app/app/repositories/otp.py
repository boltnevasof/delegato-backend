from datetime import UTC, datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.otp import OTPCode


class OTPCodeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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

    async def delete_expired(self) -> int:
        now = datetime.now(UTC)
        result = await self._session.execute(
            delete(OTPCode).where(OTPCode.expires_at < now)
        )
        await self._session.flush()
        return result.rowcount
