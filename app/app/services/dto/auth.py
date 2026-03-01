from dataclasses import dataclass


@dataclass(frozen=True)
class TokenPairDTO:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800


@dataclass(frozen=True)
class OTPRequestDTO:
    email: str


@dataclass(frozen=True)
class OTPVerifyDTO:
    email: str
    code: str


@dataclass(frozen=True)
class GoogleCallbackDTO:
    code: str
    state: str


@dataclass(frozen=True)
class TelegramAuthDTO:
    id: int
    first_name: str
    username: str | None = None
    auth_date: int = 0
    hash: str = ""
