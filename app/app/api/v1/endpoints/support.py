from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, manage_session
from app.api.v1.schemas.support import SupportRequestCreate, SupportRequestCreateResponse
from app.core.container import Container
from app.models.user import User
from app.services.dto.support import CreateSupportRequestDTO
from app.services.support import SupportService

router = APIRouter(prefix="/support", tags=["support"])


@router.post(
    "/requests",
    response_model=SupportRequestCreateResponse,
    status_code=201,
    summary="Создать обращение в поддержку",
    description="Создаёт обращение пользователя в поддержку.",
)
@inject
@manage_session
async def create_support_request(
    body: SupportRequestCreate,
    current_user: User = Depends(get_current_user),
    support_service: SupportService = Depends(Provide[Container.support_service]),
) -> SupportRequestCreateResponse:
    request = await support_service.create_request(
        user_id=current_user.id,
        dto=CreateSupportRequestDTO(
            topic=body.topic,
            description=body.description,
            contact_method=body.contact_method,
            contact=body.contact,
        ),
    )
    return SupportRequestCreateResponse(
        id=request.id,
        status=request.status.value,
        created_at=request.created_at,
    )
