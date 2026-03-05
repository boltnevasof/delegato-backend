import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SupportRequestCreate(BaseModel):
    model_config = ConfigDict(strict=True)

    topic: str
    description: str
    contact_method: str
    contact: str


class SupportRequestCreateResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    id: uuid.UUID
    status: str
    message: str = "Request received"
    created_at: datetime
