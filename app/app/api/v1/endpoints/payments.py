from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Request

from app.api.deps import PaginationParams, get_current_user, manage_session
from app.api.v1.schemas.common import MessageResponse
from app.api.v1.schemas.payment import (
    PaymentHistoryItem,
    PaymentHistoryResponse,
    SubscribeRequest,
    SubscribeResponse,
)
from app.core.container import Container
from app.models.user import User
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post(
    "/subscribe",
    response_model=SubscribeResponse,
    summary="Создать подписку",
    description="Инициирует оплату выбранного тарифа. Возвращает URL платёжной страницы, на которую нужно перенаправить пользователя.",
)
@inject
@manage_session
async def subscribe(
    body: SubscribeRequest,
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(Provide[Container.payment_service]),
) -> SubscribeResponse:
    result = await payment_service.create_subscription(
        user_id=current_user.id, tariff_id=body.tariff_id,
    )
    return SubscribeResponse(payment_url=result.payment_url, payment_id=result.payment_id)


@router.post(
    "/webhook",
    response_model=MessageResponse,
    summary="Вебхук платёжной системы",
    description="Принимает уведомления от платёжного провайдера (TBank / YooKassa). Проверяет подпись и обновляет статус платежа и подписки.",
)
@inject
@manage_session
async def payment_webhook(
    request: Request,
    payment_service: PaymentService = Depends(Provide[Container.payment_service]),
) -> MessageResponse:
    body = await request.body()
    signature = request.headers.get(
        "X-Signature", request.headers.get("HTTP_NOTIFICATION_TOKEN", ""),
    )
    client_ip = request.client.host if request.client else ""
    await payment_service.process_webhook(body, signature, client_ip)
    return MessageResponse(message="ok")


@router.get(
    "/history",
    response_model=PaymentHistoryResponse,
    summary="История платежей",
    description="Возвращает постраничный список всех платежей текущего пользователя с суммой, статусом и датой.",
)
@inject
@manage_session
async def payment_history(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(Provide[Container.payment_service]),
) -> PaymentHistoryResponse:
    items, total = await payment_service.get_history(
        current_user.id, pagination.page, pagination.per_page,
    )
    return PaymentHistoryResponse(
        items=[
            PaymentHistoryItem(
                id=p.id,
                amount_rub=p.amount_rub,
                status=p.status,
                created_at=p.created_at,
            )
            for p in items
        ],
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
    )
