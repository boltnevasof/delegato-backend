import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

from fastapi import Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_token
from app.db.engine import get_async_session
from app.exceptions.base import Forbidden, Unauthorized
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_async_session():
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise Unauthorized(detail="Missing authorization header")

    payload = decode_token(credentials.credentials, "access")
    user_id = payload.get("sub")
    if user_id is None:
        raise Unauthorized(detail="Invalid token payload")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise Unauthorized(detail="User not found")
    if not user.is_active:
        raise Forbidden(detail="User account is deactivated")

    return user


async def get_admin_user(
    user: User = Depends(get_current_user),
) -> User:
    if user.role.value != "admin":
        raise Forbidden(detail="Admin access required")
    return user


async def check_ip_whitelist(request: Request) -> None:
    client_ip = request.client.host if request.client else None
    allowed_ips = settings.admin_whitelist_ips_list
    if client_ip not in allowed_ips:
        raise Forbidden(detail="IP not whitelisted")


@dataclass
class PaginationParams:
    page: int = Query(default=1, ge=1, description="Page number")
    per_page: int = Query(default=20, ge=1, le=100, description="Items per page")
