from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class PaymentSession:
    payment_url: str
    provider_payment_id: str


@dataclass(frozen=True)
class PaymentResult:
    success: bool
    provider_payment_id: str
    error: str | None = None


@dataclass(frozen=True)
class WebhookData:
    provider_payment_id: str
    amount_kopecks: int
    status: str
    idempotency_key: str
    payment_method_token: str | None = None
    raw_data: dict | None = None


class PaymentGateway(ABC):
    @abstractmethod
    async def create_payment_session(
        self, amount_kopecks: int, user_id: str, tariff_id: str, idempotency_key: str,
    ) -> PaymentSession:
        ...

    @abstractmethod
    async def charge_recurring(
        self, payment_method_token: str, amount_kopecks: int, idempotency_key: str,
    ) -> PaymentResult:
        ...

    @abstractmethod
    async def verify_webhook(
        self, request_data: bytes, signature: str, source_ip: str,
    ) -> WebhookData:
        ...

    @abstractmethod
    async def cancel_subscription(self, subscription_id: str) -> bool:
        ...

    @abstractmethod
    async def get_payment_status(self, provider_payment_id: str) -> str:
        ...
