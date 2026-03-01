import uuid

from pydantic import BaseModel, ConfigDict, Field


class TariffResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    id: uuid.UUID
    slug: str
    name: str
    price_rub: int = Field(description="Price in kopecks")
    max_channels: int | None
    llm_model: str | None
    skills_access: str
    is_self_service: bool


class TariffListResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    tariffs: list[TariffResponse]


class CustomTariffRequestCreate(BaseModel):
    model_config = ConfigDict(strict=True)

    contact_info: str = Field(max_length=500)
    requirements: str


class CustomTariffRequestResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    id: uuid.UUID
    status: str
    message: str = "Request received"
