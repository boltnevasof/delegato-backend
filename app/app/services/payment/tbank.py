import hashlib
import json

import httpx
from loguru import logger

from app.core.config import settings
from app.services.payment.base import (
    PaymentGateway,
    PaymentResult,
    PaymentSession,
    WebhookData,
)


class TBankPaymentGateway(PaymentGateway):
    BASE_URL = "https://securepay.tinkoff.ru/v2"

    def __init__(self) -> None:
        self._terminal_key = settings.PAYMENT_TERMINAL_KEY
        self._secret_key = settings.PAYMENT_SECRET_KEY

    async def create_payment_session(
        self, amount_kopecks: int, user_id: str, tariff_id: str, idempotency_key: str,
    ) -> PaymentSession:
        payload = {
            "TerminalKey": self._terminal_key,
            "Amount": amount_kopecks,
            "OrderId": idempotency_key,
            "Description": f"Delegato subscription",
            "Recurrent": "Y",
            "CustomerKey": user_id,
        }
        payload["Token"] = self._generate_token(payload)

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{self.BASE_URL}/Init", json=payload)
            resp.raise_for_status()
            data = resp.json()

        return PaymentSession(
            payment_url=data["PaymentURL"],
            provider_payment_id=str(data["PaymentId"]),
        )

    async def charge_recurring(
        self, payment_method_token: str, amount_kopecks: int, idempotency_key: str,
    ) -> PaymentResult:
        payload = {
            "TerminalKey": self._terminal_key,
            "Amount": amount_kopecks,
            "OrderId": idempotency_key,
            "RebillId": payment_method_token,
        }
        payload["Token"] = self._generate_token(payload)

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{self.BASE_URL}/Charge", json=payload)
            data = resp.json()

        success = data.get("Status") == "CONFIRMED"
        return PaymentResult(
            success=success,
            provider_payment_id=str(data.get("PaymentId", "")),
            error=None if success else data.get("Message"),
        )

    async def verify_webhook(
        self, request_data: bytes, signature: str, source_ip: str,
    ) -> WebhookData:
        data = json.loads(request_data)

        # T-Bank uses token-based verification
        received_token = data.pop("Token", "")
        expected_token = self._generate_token(data)
        if received_token != expected_token:
            raise ValueError("Invalid webhook signature")

        return WebhookData(
            provider_payment_id=str(data.get("PaymentId", "")),
            amount_kopecks=data.get("Amount", 0),
            status=data.get("Status", ""),
            idempotency_key=data.get("OrderId", ""),
            payment_method_token=str(data.get("RebillId")) if data.get("RebillId") else None,
            raw_data=data,
        )

    async def cancel_subscription(self, subscription_id: str) -> bool:
        logger.info("TBank: cancel_subscription is a no-op (stub)")
        return True

    async def get_payment_status(self, provider_payment_id: str) -> str:
        payload = {
            "TerminalKey": self._terminal_key,
            "PaymentId": provider_payment_id,
        }
        payload["Token"] = self._generate_token(payload)

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{self.BASE_URL}/GetState", json=payload)
            data = resp.json()

        return data.get("Status", "UNKNOWN")

    def _generate_token(self, data: dict) -> str:
        filtered = {k: v for k, v in data.items() if k not in ("Token", "DATA", "Receipt")}
        filtered["Password"] = self._secret_key
        sorted_values = [str(v) for _, v in sorted(filtered.items())]
        concatenated = "".join(sorted_values)
        return hashlib.sha256(concatenated.encode()).hexdigest()
