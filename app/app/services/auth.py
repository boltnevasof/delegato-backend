import secrets
import uuid
from datetime import UTC, datetime, timedelta

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.integrations.starlette_client import OAuth

from app.core.config import settings
from app.core.constants import AuthProvider
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.exceptions.base import BadRequest, ExternalServiceError, Unauthorized
from app.models.user import User
from app.repositories.auth_method import UserAuthMethodRepository
from app.repositories.otp import OTPCodeRepository
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.services.dto.auth import (
    GoogleCallbackDTO,
    OTPRequestDTO,
    OTPVerifyDTO,
    TelegramAuthDTO,
    TokenPairDTO,
)
from app.services.email.base import EmailService
from app.utils.telegram import verify_telegram_auth


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        auth_method_repository: UserAuthMethodRepository,
        otp_repository: OTPCodeRepository,
        refresh_token_repository: RefreshTokenRepository,
        email_service: EmailService,
    ) -> None:
        self._user_repo = user_repository
        self._auth_method_repo = auth_method_repository
        self._otp_repo = otp_repository
        self._refresh_token_repo = refresh_token_repository
        self._email_service = email_service

    async def send_otp(self, dto: OTPRequestDTO) -> int:
        code = "".join(secrets.choice("0123456789") for _ in range(6))
        expires_at = datetime.now(UTC) + timedelta(minutes=5)
        await self._otp_repo.create(email=dto.email, code=code, expires_at=expires_at)
        await self._email_service.send_otp(dto.email, code)
        return 300  # expires_in seconds

    async def verify_otp(self, dto: OTPVerifyDTO) -> TokenPairDTO:
        otp = await self._otp_repo.get_valid_by_email_and_code(dto.email, dto.code)
        if otp is None:
            raise Unauthorized(detail="Invalid or expired OTP code")

        await self._otp_repo.mark_used(otp)

        user = await self._get_or_create_user(
            email=dto.email,
            name=None,
            provider=AuthProvider.EMAIL,
            provider_user_id=dto.email,
        )
        return await self._issue_tokens(user)

    async def google_initiate(self) -> str:
        oauth = OAuth()
        oauth.register(
            name="google",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
        state = secrets.token_urlsafe(32)
        google = oauth.create_client("google")
        authorization_url = await google.create_authorization_url(
            settings.GOOGLE_REDIRECT_URI, state=state,
        )
        return authorization_url["url"]

    async def google_callback(self, dto: GoogleCallbackDTO) -> TokenPairDTO:
        client = AsyncOAuth2Client(
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
        )
        try:
            token = await client.fetch_token(
                "https://oauth2.googleapis.com/token",
                code=dto.code,
                redirect_uri=settings.GOOGLE_REDIRECT_URI,
            )
        except Exception as e:
            raise ExternalServiceError(detail=f"Google token exchange failed: {e}")

        async with httpx.AsyncClient() as http:
            resp = await http.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {token['access_token']}"},
            )
            if resp.status_code != 200:
                raise ExternalServiceError(detail="Failed to fetch Google user info")
            userinfo = resp.json()

        email = userinfo.get("email")
        if not email:
            raise BadRequest(detail="Google account has no email")

        user = await self._get_or_create_user(
            email=email,
            name=userinfo.get("name"),
            provider=AuthProvider.GOOGLE,
            provider_user_id=userinfo["sub"],
        )
        return await self._issue_tokens(user)

    async def telegram_verify(self, dto: TelegramAuthDTO) -> TokenPairDTO:
        data = {
            "id": dto.id,
            "first_name": dto.first_name,
            "auth_date": dto.auth_date,
            "hash": dto.hash,
        }
        if dto.username:
            data["username"] = dto.username

        if not verify_telegram_auth(data, settings.TELEGRAM_BOT_TOKEN):
            raise Unauthorized(detail="Invalid Telegram authentication data")

        email = f"tg_{dto.id}@telegram.delegato.ru"
        user = await self._get_or_create_user(
            email=email,
            name=dto.first_name,
            provider=AuthProvider.TELEGRAM,
            provider_user_id=str(dto.id),
        )
        return await self._issue_tokens(user)

    async def refresh_tokens(self, refresh_token_str: str) -> TokenPairDTO:
        payload = decode_token(refresh_token_str, "refresh")
        jti = payload.get("jti")
        user_id = payload.get("sub")

        if not jti or not user_id:
            raise Unauthorized(detail="Invalid refresh token")

        stored_token = await self._refresh_token_repo.get_by_jti(jti)
        if stored_token is None or stored_token.is_revoked:
            raise Unauthorized(detail="Refresh token revoked or not found")

        await self._refresh_token_repo.revoke(jti)

        user = await self._user_repo.get_by_id(uuid.UUID(user_id))
        if user is None or not user.is_active:
            raise Unauthorized(detail="User not found or deactivated")

        return await self._issue_tokens(user)

    async def _get_or_create_user(
        self,
        email: str,
        name: str | None,
        provider: AuthProvider,
        provider_user_id: str,
    ) -> User:
        user = await self._user_repo.get_by_email(email)
        if user is None:
            user = await self._user_repo.create(email=email, name=name)

        existing_method = await self._auth_method_repo.get_by_provider_and_id(
            provider, provider_user_id,
        )
        if existing_method is None:
            await self._auth_method_repo.create(
                user_id=user.id,
                provider=provider,
                provider_user_id=provider_user_id,
                email=email if provider == AuthProvider.EMAIL else None,
            )

        return user

    async def _issue_tokens(self, user: User) -> TokenPairDTO:
        jti = str(uuid.uuid4())
        access_token = create_access_token(user.id, user.role.value)
        refresh_token = create_refresh_token(user.id, jti)

        expires_at = datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        await self._refresh_token_repo.create(
            user_id=user.id, jti=jti, expires_at=expires_at,
        )

        await self._refresh_token_repo.delete_expired_by_user(user.id)

        return TokenPairDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
