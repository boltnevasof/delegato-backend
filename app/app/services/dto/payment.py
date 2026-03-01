import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class PaymentSessionDTO:
    payment_url: str
    payment_id: uuid.UUID


@dataclass(frozen=True)
class WebhookDataDTO:
    provider_payment_id: str
    amount_kopecks: int
    status: str
    idempotency_key: str
    payment_method_token: str | None = None


@dataclass(frozen=True)
class PaymentResultDTO:
    success: bool
    provider_payment_id: str
    error: str | None = None


@dataclass(frozen=True)
class PaymentHistoryDTO:
    id: uuid.UUID
    amount_rub: int
    status: str
    created_at: object  # datetime
