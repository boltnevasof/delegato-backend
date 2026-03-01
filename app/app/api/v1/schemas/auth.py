from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OTPSendRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    email: EmailStr


class OTPSendResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    message: str = "OTP sent"
    expires_in: int = 300


class OTPVerifyRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    email: EmailStr
    code: str = Field(min_length=6, max_length=6)


class TokenResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TelegramAuthRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    id: int
    first_name: str
    username: str | None = None
    auth_date: int
    hash: str


class RefreshTokenRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    refresh_token: str
