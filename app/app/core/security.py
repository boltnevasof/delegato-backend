import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.core.config import settings
from app.exceptions.base import Unauthorized


def create_access_token(user_id: uuid.UUID, role: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: uuid.UUID, jti: str | None = None) -> str:
    now = datetime.now(UTC)
    if jti is None:
        jti = str(uuid.uuid4())
    payload = {
        "sub": str(user_id),
        "jti": jti,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.JWT_REFRESH_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str, token_type: str) -> dict[str, Any]:
    secret = (
        settings.JWT_SECRET_KEY
        if token_type == "access"
        else settings.JWT_REFRESH_SECRET_KEY
    )
    try:
        payload = jwt.decode(token, secret, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise Unauthorized(detail="Token has expired")
    except jwt.InvalidTokenError:
        raise Unauthorized(detail="Invalid token")

    if payload.get("type") != token_type:
        raise Unauthorized(detail="Invalid token type")

    return payload
