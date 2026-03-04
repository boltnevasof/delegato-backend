import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AdminUserListItem(BaseModel):
    model_config = ConfigDict(strict=True)
    id: uuid.UUID
    email: str
    name: str | None
    role: str
    is_active: bool
    created_at: datetime


class AdminUserListResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    items: list[AdminUserListItem]
    total: int
    page: int
    per_page: int


class AdminServerListItem(BaseModel):
    model_config = ConfigDict(strict=True)
    id: uuid.UUID
    agent_id: uuid.UUID
    status: str
    ip_address: str | None
    created_at: datetime


class AdminServerListResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    items: list[AdminServerListItem]
    total: int
    page: int
    per_page: int


class AdminServerStats(BaseModel):
    model_config = ConfigDict(strict=True)
    total: int
    active: int
    provisioning: int
    error: int
    stopped: int


class AdminAgentListItem(BaseModel):
    model_config = ConfigDict(strict=True)
    id: uuid.UUID
    user_id: uuid.UUID
    status: str
    onboarding_step: int
    created_at: datetime


class AdminAgentListResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    items: list[AdminAgentListItem]
    total: int
    page: int
    per_page: int


class AdminCustomRequestItem(BaseModel):
    model_config = ConfigDict(strict=True)
    id: uuid.UUID
    user_id: uuid.UUID
    contact_info: str
    requirements: str
    status: str
    created_at: datetime


class AdminCustomRequestListResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    items: list[AdminCustomRequestItem]
    total: int
    page: int
    per_page: int


class AdminLoginRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    access_token: str
    token_type: str
    expires_in: int


class AdminUpdateUserRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    name: str | None = None
    email: str | None = None
    role: str | None = None
    is_active: bool | None = None


class AdminUpdateUserResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    id: uuid.UUID
    email: str
    name: str | None
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AdminOTPCodeItem(BaseModel):
    model_config = ConfigDict(strict=True)
    id: uuid.UUID
    email: str
    code: str
    is_used: bool
    expires_at: datetime
    created_at: datetime


class AdminOTPCodeListResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    items: list[AdminOTPCodeItem]
    total: int
    page: int
    per_page: int
