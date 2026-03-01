from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.v1.schemas.subscription import (
    CancelSubscriptionRequest,
    CancelSubscriptionResponse,
    ChangeTariffRequest,
    ChangeTariffResponse,
    ReactivateResponse,
    SubscriptionDetailResponse,
    TariffSummary,
)
from app.core.container import Container
from app.models.user import User
from app.services.subscription import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


def _build_sub_response(sub) -> SubscriptionDetailResponse:
    return SubscriptionDetailResponse(
        id=sub.id,
        tariff=TariffSummary(
            slug=sub.tariff_plan.slug,
            name=sub.tariff_plan.name,
            price_rub=sub.tariff_plan.price_rub,
        ),
        status=sub.status.value,
        current_period_start=sub.current_period_start,
        current_period_end=sub.current_period_end,
        payment_method=sub.payment_method_token,
        cancel_reason=sub.cancel_reason,
    )


@router.get(
    "/current",
    response_model=SubscriptionDetailResponse,
    summary="Текущая подписка",
    description="Возвращает детали активной подписки пользователя: тариф, период, статус и причину отмены (если есть).",
)
@inject
async def get_current_subscription(
    current_user: User = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(
        Provide[Container.subscription_service],
    ),
) -> SubscriptionDetailResponse:
    sub = await subscription_service.get_current(current_user.id)
    return _build_sub_response(sub)


@router.post(
    "/change-tariff",
    response_model=ChangeTariffResponse,
    summary="Сменить тариф",
    description="Переключает подписку на другой тарифный план с расчётом пропорциональной доплаты/возврата за оставшийся период.",
)
@inject
async def change_tariff(
    body: ChangeTariffRequest,
    current_user: User = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(
        Provide[Container.subscription_service],
    ),
) -> ChangeTariffResponse:
    result = await subscription_service.change_tariff(current_user.id, body.tariff_id)
    return ChangeTariffResponse(
        subscription=_build_sub_response(result["subscription"]),
        proration_amount_rub=result["proration_amount_rub"],
        message="Tariff changed successfully",
    )


@router.post(
    "/cancel",
    response_model=CancelSubscriptionResponse,
    summary="Отменить подписку",
    description="Отменяет подписку. Доступ сохраняется до конца grace-периода, после чего сервер останавливается.",
)
@inject
async def cancel_subscription(
    body: CancelSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(
        Provide[Container.subscription_service],
    ),
) -> CancelSubscriptionResponse:
    result = await subscription_service.cancel(current_user.id, body.reason)
    return CancelSubscriptionResponse(
        status=result["status"],
        grace_period_end=result["grace_period_end"],
        message="Subscription will end after grace period",
    )


@router.post(
    "/reactivate",
    response_model=ReactivateResponse,
    summary="Реактивировать подписку",
    description="Возобновляет ранее отменённую подписку, если grace-период ещё не истёк.",
)
@inject
async def reactivate_subscription(
    current_user: User = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(
        Provide[Container.subscription_service],
    ),
) -> ReactivateResponse:
    sub = await subscription_service.reactivate(current_user.id)
    return ReactivateResponse(
        status=sub.status.value,
        message="Subscription reactivated",
    )
