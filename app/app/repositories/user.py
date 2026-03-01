import uuid

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.utils.pagination import paginate


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, email: str, name: str | None = None) -> User:
        user = User(email=email, name=name)
        self._session.add(user)
        await self._session.flush()
        return user

    async def update(self, user_id: uuid.UUID, **kwargs) -> User | None:
        await self._session.execute(
            update(User).where(User.id == user_id).values(**kwargs)
        )
        await self._session.flush()
        return await self.get_by_id(user_id)

    async def list_paginated(
        self, page: int, per_page: int, search: str | None = None,
    ) -> tuple[list[User], int]:
        query = select(User).order_by(User.created_at.desc())
        if search:
            pattern = f"%{search}%"
            query = query.where(
                or_(User.email.ilike(pattern), User.name.ilike(pattern)),
            )
        return await paginate(self._session, query, page, per_page)
