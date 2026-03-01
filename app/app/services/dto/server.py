import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ServerStatusDTO:
    id: uuid.UUID
    status: str
    ip_address: str | None
    created_at: datetime


@dataclass(frozen=True)
class ServerLogDTO:
    id: uuid.UUID
    level: str
    stage: str
    message: str
    details: dict | None
    created_at: datetime


@dataclass(frozen=True)
class ProvisioningResultDTO:
    success: bool
    server_id: uuid.UUID
    ip_address: str | None
    error: str | None = None
