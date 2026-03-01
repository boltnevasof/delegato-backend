import uuid
from datetime import UTC, datetime, timedelta

from app.core.config import settings
from app.core.constants import PaymentStatus
from app.exceptions.base import BadRequest, Forbidden
from app.models.payment import Payment
from app.repositories.agent import AgentRepository
from app.repositories.payment import PaymentRepository
from app.repositories.server import ServerRepository
from app.repositories.subscription import SubscriptionRepository
from app.repositories.tariff import TariffRepository
from app.services.agent import AgentService
from app.services.payment.base import PaymentGateway
from app.services.server import ServerService
from app.services.subscription import SubscriptionService
from app.services.dto.payment import PaymentHistoryDTO, PaymentSessionDTO


class PaymentService:
    def __init__(
        self,
        payment_repository: PaymentRepository,
        subscription_repository: SubscriptionRepository,
        tariff_repository: TariffRepository,
        agent_repository: AgentRepository,
        server_repository: ServerRepository,
        payment_gateway: PaymentGateway,
        subscription_service: SubscriptionService,
        agent_service: AgentService,
        server_service: ServerService,
    ) -> None:
        self._payment_repo = payment_repository
        self._subscription_repo = subscription_repository
        self._tariff_repo = tariff_repository
        self._agent_repo = agent_repository
        self._server_repo = server_repository
        self._gateway = payment_gateway
        self._subscription_service = subscription_service
        self._agent_service = agent_service
        self._server_service = server_service

    async def create_subscription(
        self, user_id: uuid.UUID, tariff_id: uuid.UUID,
    ) -> PaymentSessionDTO:
        existing = await self._subscription_repo.get_by_user_id(user_id)
        if existing:
            raise BadRequest(detail="Already subscribed")

        tariff = await self._tariff_repo.get_by_id(tariff_id)
        if tariff is None:
            raise BadRequest(detail="Tariff not found")
        if not tariff.is_self_service:
            raise BadRequest(detail="Custom tariff requires a custom request")

        idempotency_key = (
            f"sub_{user_id}_{tariff_id}_{int(datetime.now(UTC).timestamp())}"
        )

        payment = await self._payment_repo.create(
            user_id=user_id,
            amount_rub=tariff.price_rub,
            provider=settings.PAYMENT_PROVIDER,
            idempotency_key=idempotency_key,
        )

        session = await self._gateway.create_payment_session(
            amount_kopecks=tariff.price_rub,
            user_id=str(user_id),
            tariff_id=str(tariff.id),
            idempotency_key=idempotency_key,
        )

        await self._payment_repo.update_status(
            payment.id,
            PaymentStatus.PENDING,
            provider_payment_id=session.provider_payment_id,
        )

        return PaymentSessionDTO(payment_url=session.payment_url, payment_id=payment.id)

    async def process_webhook(
        self, body: bytes, signature: str, client_ip: str,
    ) -> None:
        allowed_ips = settings.payment_webhook_ips_list
        if allowed_ips and client_ip not in allowed_ips:
            raise Forbidden(detail="IP not whitelisted for webhooks")

        webhook_data = await self._gateway.verify_webhook(body, signature, client_ip)

        existing = await self._payment_repo.get_by_idempotency_key(
            webhook_data.idempotency_key,
        )
        if not existing or existing.status != PaymentStatus.PENDING:
            return

        payment = existing

        if webhook_data.status in ("CONFIRMED", "succeeded"):
            await self._payment_repo.update_status(
                payment.id,
                PaymentStatus.SUCCEEDED,
                webhook_data=webhook_data.raw_data,
            )
            await self._activate_subscription(payment, webhook_data.payment_method_token)
        else:
            await self._payment_repo.update_status(
                payment.id,
                PaymentStatus.FAILED,
                webhook_data=webhook_data.raw_data,
            )

    async def _activate_subscription(
        self, payment: Payment, payment_method_token: str | None,
    ) -> None:
        existing_sub = await self._subscription_repo.get_by_user_id(payment.user_id)
        if existing_sub:
            return

        tariffs = await self._tariff_repo.list_active()
        matching_tariff = next(
            (t for t in tariffs if t.price_rub == payment.amount_rub), None,
        )
        if not matching_tariff:
            return

        now = datetime.now(UTC)
        await self._subscription_service.create_subscription(
            user_id=payment.user_id,
            tariff_plan_id=matching_tariff.id,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            payment_method_token=payment_method_token,
        )

        existing_agent = await self._agent_repo.get_by_user_id(payment.user_id)
        if not existing_agent:
            agent = await self._agent_service.create_agent(payment.user_id)
            await self._server_service.create_server(agent.id)

    async def get_history(
        self, user_id: uuid.UUID, page: int, per_page: int,
    ) -> tuple[list[PaymentHistoryDTO], int]:
        items, total = await self._payment_repo.get_by_user_id_paginated(
            user_id, page, per_page,
        )
        return [
            PaymentHistoryDTO(
                id=p.id,
                amount_rub=p.amount_rub,
                status=p.status.value,
                created_at=p.created_at,
            )
            for p in items
        ], total
