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


class AdminSupportRequestItem(BaseModel):
    model_config = ConfigDict(strict=True)
    id: uuid.UUID
    user_id: uuid.UUID
    topic: str
    description: str
    contact_method: str
    contact: str
    status: str
    created_at: datetime


class AdminSupportRequestListResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    items: list[AdminSupportRequestItem]
    total: int
    page: int
    per_page: int


# --- Tariff CRUD ---


class AdminTariffListItem(BaseModel):
    model_config = ConfigDict(strict=True)
    id: uuid.UUID
    slug: str
    name: str
    price_rub: int
    max_channels: int | None
    llm_model: str | None
    skills_access: str
    is_self_service: bool
    is_active: bool
    created_at: datetime


class AdminTariffListResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    items: list[AdminTariffListItem]
    total: int
    page: int
    per_page: int


class AdminCreateTariffRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    slug: str
    name: str
    price_rub: int
    max_channels: int | None = None
    llm_model: str | None = None
    skills_access: str = "basic"
    is_self_service: bool = True
    is_active: bool = True


class AdminUpdateTariffRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    slug: str | None = None
    name: str | None = None
    price_rub: int | None = None
    max_channels: int | None = None
    llm_model: str | None = None
    skills_access: str | None = None
    is_self_service: bool | None = None
    is_active: bool | None = None


class AdminTariffResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    id: uuid.UUID
    slug: str
    name: str
    price_rub: int
    max_channels: int | None
    llm_model: str | None
    skills_access: str
    is_self_service: bool
    is_active: bool
    created_at: datetime


# --- User tariff assignment ---


class AdminAssignTariffRequest(BaseModel):
    tariff_plan_id: uuid.UUID


class AdminUserSubscriptionResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    subscription_id: uuid.UUID | None
    tariff_plan_id: uuid.UUID | None
    tariff_name: str | None
    status: str | None
