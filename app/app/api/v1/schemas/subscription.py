import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TariffSummary(BaseModel):
    model_config = ConfigDict(strict=True)
    slug: str
    name: str
    price_rub: int


class SubscriptionDetailResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    id: uuid.UUID
    tariff: TariffSummary
    status: str
    current_period_start: datetime
    current_period_end: datetime
    payment_method: str | None
    cancel_reason: str | None


class ChangeTariffRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    tariff_id: uuid.UUID


class ChangeTariffResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    subscription: SubscriptionDetailResponse
    proration_amount_rub: int
    message: str


class CancelSubscriptionRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    reason: str


class CancelSubscriptionResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str
    grace_period_end: str
    message: str


class ReactivateResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str
    message: str
