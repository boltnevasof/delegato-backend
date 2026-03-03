from dataclasses import dataclass


@dataclass(frozen=True)
class AdminLoginDTO:
    username: str
    password: str


@dataclass(frozen=True)
class AdminTokenDTO:
    access_token: str
    expires_in: int
    token_type: str = "bearer"


@dataclass(frozen=True)
class AdminUpdateUserDTO:
    name: str | None = None
    email: str | None = None
    role: str | None = None
    is_active: bool | None = None
