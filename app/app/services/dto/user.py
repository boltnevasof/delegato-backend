import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AgentSummaryDTO:
    id: uuid.UUID
    status: str
    onboarding_step: int


@dataclass(frozen=True)
class SubscriptionSummaryDTO:
    id: uuid.UUID
    tariff_slug: str
    status: str
    current_period_end: datetime


@dataclass(frozen=True)
class UserProfileDTO:
    id: uuid.UUID
    email: str
    name: str | None
    role: str
    auth_methods: list[str]
    created_at: datetime
    agent: AgentSummaryDTO | None = None
    subscription: SubscriptionSummaryDTO | None = None
