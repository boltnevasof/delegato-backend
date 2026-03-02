from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, manage_session
from app.api.v1.schemas.tariff import (
    CustomTariffRequestCreate,
    CustomTariffRequestResponse,
    TariffListResponse,
    TariffResponse,
)
from app.core.container import Container
from app.models.user import User
from app.services.tariff import TariffService

router = APIRouter(prefix="/tariffs", tags=["tariffs"])


@router.get(
    "",
    response_model=TariffListResponse,
    summary="Список тарифов",
    description="Возвращает все доступные тарифные планы с ценами, лимитами каналов, LLM-моделью и уровнем доступа к навыкам.",
)
@inject
@manage_session
async def list_tariffs(
    tariff_service: TariffService = Depends(Provide[Container.tariff_service]),
) -> TariffListResponse:
    tariffs = await tariff_service.list_tariffs()
    return TariffListResponse(
        tariffs=[
            TariffResponse(
                id=t.id,
                slug=t.slug,
                name=t.name,
                price_rub=t.price_rub,
                max_channels=t.max_channels,
                llm_model=t.llm_model,
                skills_access=t.skills_access.value,
                is_self_service=t.is_self_service,
            )
            for t in tariffs
        ],
    )


@router.post(
    "/custom/request",
    response_model=CustomTariffRequestResponse,
    status_code=201,
    summary="Заявка на кастомный тариф",
    description="Создаёт заявку на индивидуальный тарифный план. Менеджер свяжется с пользователем по указанным контактам.",
)
@inject
@manage_session
async def create_custom_request(
    body: CustomTariffRequestCreate,
    current_user: User = Depends(get_current_user),
    tariff_service: TariffService = Depends(Provide[Container.tariff_service]),
) -> CustomTariffRequestResponse:
    request = await tariff_service.create_custom_request(
        user_id=current_user.id,
        contact_info=body.contact_info,
        requirements=body.requirements,
    )
    return CustomTariffRequestResponse(id=request.id, status=request.status.value)
