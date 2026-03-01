import uuid

from pydantic import BaseModel, ConfigDict


class ToolCatalogItem(BaseModel):
    model_config = ConfigDict(strict=True)
    id: uuid.UUID
    slug: str
    name: str
    description: str


class ToolCatalogResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    tools: list[ToolCatalogItem]


class AgentToolResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    id: uuid.UUID
    slug: str
    is_enabled: bool


class AddToolRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    tool_id: uuid.UUID


class ToggleToolRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    is_enabled: bool
