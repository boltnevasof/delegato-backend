import uuid

from pydantic import BaseModel, ConfigDict


class SkillCatalogItem(BaseModel):
    model_config = ConfigDict(strict=True)
    id: uuid.UUID
    slug: str
    name: str
    description: str
    access_level: str
    available_for_user: bool


class SkillPresetItem(BaseModel):
    model_config = ConfigDict(strict=True)
    slug: str
    name: str
    skill_ids: list[uuid.UUID]


class SkillCatalogResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    skills: list[SkillCatalogItem]
    presets: list[SkillPresetItem]


class AgentSkillResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    id: uuid.UUID
    slug: str
    is_enabled: bool


class AddSkillRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    skill_id: uuid.UUID


class ToggleSkillRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    is_enabled: bool
