import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ServerStatusResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    id: uuid.UUID
    status: str
    ip_address: str | None
    created_at: datetime


class ServerLogItem(BaseModel):
    model_config = ConfigDict(strict=True)
    id: uuid.UUID
    level: str
    stage: str
    message: str
    created_at: datetime


class ServerProvisionResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    server_id: uuid.UUID
    status: str


class ServerLogListResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    items: list[ServerLogItem]
    total: int
    page: int
    per_page: int
