import httpx
from loguru import logger

from app.core.config import settings
from app.services.email.base import EmailService


class UnisenderEmailService(EmailService):
    def __init__(self) -> None:
        self._base_url = settings.UNISENDER_BASE_URL
        self._api_key = settings.UNISENDER_API_KEY
        self._from_email = settings.UNISENDER_FROM_EMAIL
        self._from_name = settings.UNISENDER_FROM_NAME

    async def send_otp(self, email: str, code: str) -> None:
        subject = f"Ваш код подтверждения: {code}"
        body = f"Ваш код подтверждения для входа в Delegato: <b>{code}</b>. Код действителен 5 минут."
        await self._send_email(email, subject, body)

    async def send_transactional(
        self, email: str, template_id: str, variables: dict,
    ) -> None:
        payload = {
            "message": {
                "template_id": template_id,
                "recipients": [{"email": email}],
                "global_substitutions": variables,
            }
        }
        await self._request("/email/send.json", payload)

    async def _send_email(self, to_email: str, subject: str, body: str) -> None:
        payload = {
            "message": {
                "recipients": [{"email": to_email}],
                "body": {"html": body},
                "subject": subject,
                "from_email": self._from_email,
                "from_name": self._from_name,
            }
        }
        await self._request("/email/send.json", payload)

    async def _request(self, path: str, payload: dict) -> dict:
        url = f"{self._base_url}{path}"
        headers = {"X-API-KEY": self._api_key, "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                logger.error(
                    "Unisender API error: status={status} body={body}",
                    status=response.status_code,
                    body=response.text,
                )
                raise RuntimeError(f"Unisender API error: {response.status_code}")
            return response.json()
