import uuid
from dataclasses import dataclass
from functools import wraps

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.container import Container
from app.core.security import decode_token
from app.db.engine import session_context
from app.exceptions.base import Forbidden, Unauthorized
from app.models.user import User
from app.repositories.user import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


@inject
def manage_session(func):
    """Декоратор: создаёт сессию → ContextVar → execute → commit → close → reset."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        session = Container.session()
        token = session_context.set(session)
        try:
            result = await func(*args, **kwargs)
            await session.commit()
            return result
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()
            session_context.reset(token)
    return wrapper


@inject
@manage_session
async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    user_repository: UserRepository = Depends(Provide[Container.user_repository]),
) -> User:
    if credentials is None:
        raise Unauthorized(detail="Missing authorization header")

    payload = decode_token(credentials.credentials, "access")
    user_id = payload.get("sub")
    if user_id is None:
        raise Unauthorized(detail="Invalid token payload")

    user = await user_repository.get_by_id(uuid.UUID(user_id))
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
    pass  # temporarily disabled


@dataclass
class PaginationParams:
    page: int = Query(default=1, ge=1, description="Page number")
    per_page: int = Query(default=20, ge=1, le=100, description="Items per page")
