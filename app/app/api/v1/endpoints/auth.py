from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import manage_session
from app.api.v1.schemas.auth import (
    OTPSendRequest,
    OTPSendResponse,
    OTPVerifyRequest,
    RefreshTokenRequest,
    TelegramAuthRequest,
    TokenResponse,
)
from app.core.container import Container
from app.services.auth import AuthService
from app.services.dto.auth import (
    GoogleCallbackDTO,
    OTPRequestDTO,
    OTPVerifyDTO,
    TelegramAuthDTO,
)

router = APIRouter(prefix="/auth", tags=["auth"])

limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/email/send-otp",
    response_model=OTPSendResponse,
    summary="Отправить OTP-код на email",
    description="Генерирует одноразовый код и отправляет его на указанный email через Unisender. Лимит: 5 запросов в минуту.",
)
@limiter.limit("5/minute")
@inject
@manage_session
async def send_otp(
    request: Request,
    body: OTPSendRequest,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> OTPSendResponse:
    expires_in = await auth_service.send_otp(OTPRequestDTO(email=body.email))
    return OTPSendResponse(expires_in=expires_in)


@router.post(
    "/email/verify-otp",
    response_model=TokenResponse,
    summary="Подтвердить OTP-код",
    description="Проверяет OTP-код и возвращает JWT access/refresh токены. Если пользователь не существует — создаётся автоматически. Лимит: 10 запросов в минуту.",
)
@limiter.limit("10/minute")
@inject
@manage_session
async def verify_otp(
    request: Request,
    body: OTPVerifyRequest,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> TokenResponse:
    tokens = await auth_service.verify_otp(OTPVerifyDTO(email=body.email, code=body.code))
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
    )


@router.get(
    "/google/initiate",
    summary="Начать Google OAuth",
    description="Перенаправляет (302) на страницу авторизации Google. Используется как первый шаг OAuth2 flow.",
)
@inject
@manage_session
async def google_initiate(
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> Response:
    url = await auth_service.google_initiate()
    return Response(status_code=302, headers={"Location": url})


@router.get(
    "/google/callback",
    response_model=TokenResponse,
    summary="Callback Google OAuth",
    description="Обрабатывает ответ Google после авторизации. Создаёт или находит пользователя и возвращает JWT токены.",
)
@inject
@manage_session
async def google_callback(
    code: str,
    state: str,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> TokenResponse:
    tokens = await auth_service.google_callback(GoogleCallbackDTO(code=code, state=state))
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
    )


@router.post(
    "/telegram/verify",
    response_model=TokenResponse,
    summary="Авторизация через Telegram",
    description="Проверяет данные Telegram Login Widget (hash-подпись). Создаёт или находит пользователя и возвращает JWT токены.",
)
@inject
@manage_session
async def telegram_verify(
    body: TelegramAuthRequest,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> TokenResponse:
    tokens = await auth_service.telegram_verify(
        TelegramAuthDTO(
            id=body.id,
            first_name=body.first_name,
            username=body.username,
            auth_date=body.auth_date,
            hash=body.hash,
        ),
    )
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
    )


@router.post(
    "/token/refresh",
    response_model=TokenResponse,
    summary="Обновить JWT токены",
    description="Принимает refresh-токен и возвращает новую пару access/refresh токенов. Старый refresh-токен инвалидируется.",
)
@inject
@manage_session
async def refresh_token(
    body: RefreshTokenRequest,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> TokenResponse:
    tokens = await auth_service.refresh_tokens(body.refresh_token)
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
    )
