import hashlib
import hmac
import json
import uuid

import httpx
from loguru import logger

from app.core.config import settings
from app.services.payment.base import (
    PaymentGateway,
    PaymentResult,
    PaymentSession,
    WebhookData,
)


class YooKassaPaymentGateway(PaymentGateway):
    BASE_URL = "https://api.yookassa.ru/v3"

    def __init__(self) -> None:
        self._shop_id = settings.PAYMENT_TERMINAL_KEY
        self._secret_key = settings.PAYMENT_SECRET_KEY

    async def create_payment_session(
        self, amount_kopecks: int, user_id: str, tariff_id: str, idempotency_key: str,
    ) -> PaymentSession:
        amount_rub = amount_kopecks / 100
        payload = {
            "amount": {"value": f"{amount_rub:.2f}", "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": "https://delegato.ru/payment/success"},
            "capture": True,
            "description": "Delegato subscription",
            "save_payment_method": True,
            "metadata": {"user_id": user_id, "tariff_id": tariff_id},
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.BASE_URL}/payments",
                json=payload,
                auth=(self._shop_id, self._secret_key),
                headers={"Idempotence-Key": idempotency_key},
            )
            resp.raise_for_status()
            data = resp.json()

        return PaymentSession(
            payment_url=data["confirmation"]["confirmation_url"],
            provider_payment_id=data["id"],
        )

    async def charge_recurring(
        self, payment_method_token: str, amount_kopecks: int, idempotency_key: str,
    ) -> PaymentResult:
        amount_rub = amount_kopecks / 100
        payload = {
            "amount": {"value": f"{amount_rub:.2f}", "currency": "RUB"},
            "capture": True,
            "payment_method_id": payment_method_token,
            "description": "Delegato subscription renewal",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.BASE_URL}/payments",
                json=payload,
                auth=(self._shop_id, self._secret_key),
                headers={"Idempotence-Key": idempotency_key},
            )
            data = resp.json()

        success = data.get("status") == "succeeded"
        return PaymentResult(
            success=success,
            provider_payment_id=data.get("id", ""),
            error=None if success else data.get("cancellation_details", {}).get("reason"),
        )

    async def verify_webhook(
        self, request_data: bytes, signature: str, source_ip: str,
    ) -> WebhookData:
        # YooKassa webhook verification via HMAC-SHA256
        expected = hmac.new(
            self._secret_key.encode(), request_data, hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise ValueError("Invalid webhook signature")

        data = json.loads(request_data)
        event = data.get("event", "")
        payment = data.get("object", {})
        amount = payment.get("amount", {})
        amount_kopecks = int(float(amount.get("value", "0")) * 100)

        return WebhookData(
            provider_payment_id=payment.get("id", ""),
            amount_kopecks=amount_kopecks,
            status=payment.get("status", ""),
            idempotency_key=payment.get("metadata", {}).get("idempotency_key", str(uuid.uuid4())),
            payment_method_token=payment.get("payment_method", {}).get("id"),
            raw_data=data,
        )

    async def cancel_subscription(self, subscription_id: str) -> bool:
        logger.info("YooKassa: cancel_subscription is a no-op (stub)")
        return True

    async def get_payment_status(self, provider_payment_id: str) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{self.BASE_URL}/payments/{provider_payment_id}",
                auth=(self._shop_id, self._secret_key),
            )
            data = resp.json()

        return data.get("status", "unknown")
