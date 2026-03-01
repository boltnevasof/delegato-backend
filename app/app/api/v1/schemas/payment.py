import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SubscribeRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    tariff_id: uuid.UUID


class SubscribeResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    payment_url: str
    payment_id: uuid.UUID


class PaymentHistoryItem(BaseModel):
    model_config = ConfigDict(strict=True)

    id: uuid.UUID
    amount_rub: int = Field(description="Amount in kopecks")
    status: str
    created_at: datetime


class PaymentHistoryResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    items: list[PaymentHistoryItem]
    total: int
    page: int
    per_page: int
