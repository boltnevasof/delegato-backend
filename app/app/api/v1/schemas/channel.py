import uuid

from pydantic import BaseModel, ConfigDict


class ChannelResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    id: uuid.UUID
    channel_type: str
    status: str


class ChannelListResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    channels: list[ChannelResponse]


class UpdateChannelRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str
