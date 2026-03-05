import secrets
import uuid

from loguru import logger

from app.core.config import settings
from app.core.constants import UserRole
from app.core.security import create_access_token
from app.exceptions.base import ConflictError, NotFound, Unauthorized
from app.repositories.otp import OTPCodeRepository
from app.repositories.user import UserRepository
from app.services.dto.admin import AdminLoginDTO, AdminTokenDTO, AdminUpdateUserDTO


class AdminService:
    def __init__(
        self,
        user_repository: UserRepository,
        otp_repository: OTPCodeRepository,
    ) -> None:
        self._user_repo = user_repository
        self._otp_repo = otp_repository

    async def login(self, dto: AdminLoginDTO) -> AdminTokenDTO:
        if not settings.ADMIN_PASSWORD:
            raise Unauthorized(detail="Admin login is not configured")

        if not secrets.compare_digest(dto.username, settings.ADMIN_USERNAME):
            raise Unauthorized(detail="Invalid admin credentials")
        if not secrets.compare_digest(dto.password, settings.ADMIN_PASSWORD):
            raise Unauthorized(detail="Invalid admin credentials")

        user = await self._user_repo.get_by_email(settings.ADMIN_EMAIL)
        if user is None:
            raise Unauthorized(detail="Admin user not found in database")

        access_token = create_access_token(user.id, user.role.value)
        return AdminTokenDTO(
            access_token=access_token,
            expires_in=settings.ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def update_user(self, user_id: uuid.UUID, dto: AdminUpdateUserDTO) -> None:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFound(detail="User not found")

        fields: dict = {}
        if dto.name is not None:
            fields["name"] = dto.name
        if dto.email is not None:
            existing = await self._user_repo.get_by_email(dto.email)
            if existing and existing.id != user_id:
                raise ConflictError(detail="Email already in use")
            fields["email"] = dto.email
        if dto.role is not None:
            UserRole(dto.role)  # validate enum
            fields["role"] = dto.role
        if dto.is_active is not None:
            fields["is_active"] = dto.is_active

        if fields:
            await self._user_repo.update(user_id, **fields)

    async def ensure_admin_user_exists(self) -> None:
        if not settings.ADMIN_PASSWORD:
            logger.warning("ADMIN_PASSWORD not set, skipping admin user creation")
            return

        user = await self._user_repo.get_by_email(settings.ADMIN_EMAIL)
        if user is None:
            user = await self._user_repo.create(
                email=settings.ADMIN_EMAIL,
                name=settings.ADMIN_USERNAME,
            )
            await self._user_repo.update(user.id, role=UserRole.ADMIN.value)
            logger.info("Admin user created: {email}", email=settings.ADMIN_EMAIL)
        elif user.role != UserRole.ADMIN:
            await self._user_repo.update(user.id, role=UserRole.ADMIN.value)
            logger.info("Admin role set for user: {email}", email=settings.ADMIN_EMAIL)
