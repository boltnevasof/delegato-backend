import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class OnboardingDescribeDTO:
    business_description: str


@dataclass(frozen=True)
class OnboardingChannelDTO:
    channel_type: str
    config: dict


@dataclass(frozen=True)
class OnboardingSkillsDTO:
    skill_ids: list[uuid.UUID] = field(default_factory=list)
    preset_slug: str | None = None


@dataclass(frozen=True)
class AgentDetailDTO:
    id: uuid.UUID
    status: str
    soul_md: str | None
    agent_md: str | None
    onboarding_step: int
    skills: list[dict]
    tools: list[dict]
    channels: list[dict]
    server: dict | None


@dataclass(frozen=True)
class AITaskStatusDTO:
    task_id: str
    status: str  # pending / running / completed / failed
    result: dict | None = None
    error: str | None = None
