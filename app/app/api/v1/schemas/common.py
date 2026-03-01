from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ErrorResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    detail: str
    code: str | None = None


class MessageResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    message: str


class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(strict=True)

    items: list[T]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    per_page: int = Field(ge=1)
