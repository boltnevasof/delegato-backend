import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, select, update

from app.db.engine import session_context
from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    @property
    def _session(self):
        return session_context.get()

    async def create(
        self, user_id: uuid.UUID, jti: str, expires_at: datetime,
    ) -> RefreshToken:
        token = RefreshToken(user_id=user_id, jti=jti, expires_at=expires_at)
        self._session.add(token)
        await self._session.flush()
        return token

    async def get_by_jti(self, jti: str) -> RefreshToken | None:
        result = await self._session.execute(
            select(RefreshToken).where(RefreshToken.jti == jti)
        )
        return result.scalar_one_or_none()

    async def revoke(self, jti: str) -> None:
        await self._session.execute(
            update(RefreshToken).where(RefreshToken.jti == jti).values(is_revoked=True)
        )
        await self._session.flush()

    async def delete_expired(self) -> int:
        now = datetime.now(UTC)
        result = await self._session.execute(
            delete(RefreshToken).where(RefreshToken.expires_at < now),
        )
        await self._session.flush()
        return result.rowcount

    async def delete_expired_by_user(self, user_id: uuid.UUID) -> int:
        now = datetime.now(UTC)
        result = await self._session.execute(
            delete(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.expires_at < now,
            )
        )
        await self._session.flush()
        return result.rowcount
