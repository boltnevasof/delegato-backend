import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import AuthProvider
from app.models.user import UserAuthMethod


class UserAuthMethodRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_provider_and_id(
        self, provider: AuthProvider, provider_user_id: str,
    ) -> UserAuthMethod | None:
        result = await self._session.execute(
            select(UserAuthMethod).where(
                UserAuthMethod.provider == provider,
                UserAuthMethod.provider_user_id == provider_user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: uuid.UUID) -> list[UserAuthMethod]:
        result = await self._session.execute(
            select(UserAuthMethod).where(UserAuthMethod.user_id == user_id)
        )
        return list(result.scalars().all())

    async def create(
        self,
        user_id: uuid.UUID,
        provider: AuthProvider,
        provider_user_id: str,
        email: str | None = None,
        metadata: dict | None = None,
    ) -> UserAuthMethod:
        auth_method = UserAuthMethod(
            user_id=user_id,
            provider=provider,
            provider_user_id=provider_user_id,
            email=email,
            metadata_=metadata,
        )
        self._session.add(auth_method)
        await self._session.flush()
        return auth_method
