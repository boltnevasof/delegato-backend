import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SkillSummary(BaseModel):
    model_config = ConfigDict(strict=True)
    id: uuid.UUID
    slug: str
    is_enabled: bool


class ToolSummary(BaseModel):
    model_config = ConfigDict(strict=True)
    id: uuid.UUID
    slug: str
    is_enabled: bool


class ChannelSummary(BaseModel):
    model_config = ConfigDict(strict=True)
    id: uuid.UUID
    type: str
    status: str


class ServerSummary(BaseModel):
    model_config = ConfigDict(strict=True)
    id: uuid.UUID
    status: str
    ip_address: str | None


class AgentDetailResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    id: uuid.UUID
    status: str
    soul_md: str | None
    agent_md: str | None
    onboarding_step: int
    skills: list[SkillSummary]
    tools: list[ToolSummary]
    channels: list[ChannelSummary]
    server: ServerSummary | None


class OnboardingDescribeRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    business_description: str


class AsyncTaskAcceptedResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    task_id: str
    status: str = "accepted"
    message: str = "AI generation started"


class AsyncTaskStatusResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    task_id: str
    status: str
    result: dict[str, Any] | None = None
    error: str | None = None


class OnboardingConnectChannelRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    channel_type: str = "telegram"
    config: dict[str, Any]


class OnboardingConnectChannelResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    id: uuid.UUID
    channel_type: str
    status: str


class OnboardingSelectSkillsRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    skill_ids: list[uuid.UUID] = Field(default_factory=list)
    preset_slug: str | None = None


class OnboardingSelectSkillsResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    activated_skills: list[SkillSummary]


class OnboardingCompleteResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str
    task_id: str | None = None


class SoulMdUpdateRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    content: str


class AgentMdUpdateRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    content: str


class EnhanceRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    field: str = Field(pattern="^(soul_md|agent_md)$")
    content: str
