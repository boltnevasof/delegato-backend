import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AgentSummary(BaseModel):
    model_config = ConfigDict(strict=True)

    id: uuid.UUID
    status: str
    onboarding_step: int


class SubscriptionSummary(BaseModel):
    model_config = ConfigDict(strict=True)

    id: uuid.UUID
    tariff_slug: str
    status: str
    current_period_end: datetime


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    id: uuid.UUID
    email: str
    name: str | None
    role: str
    auth_methods: list[str]
    created_at: datetime
    agent: AgentSummary | None = None
    subscription: SubscriptionSummary | None = None
