import uuid

from app.models.support_request import SupportRequest
from app.repositories.support_request import SupportRequestRepository
from app.services.dto.support import CreateSupportRequestDTO


class SupportService:
    def __init__(
        self,
        support_request_repository: SupportRequestRepository,
    ) -> None:
        self._support_request_repo = support_request_repository

    async def create_request(
        self,
        user_id: uuid.UUID,
        dto: CreateSupportRequestDTO,
    ) -> SupportRequest:
        return await self._support_request_repo.create(
            user_id=user_id,
            topic=dto.topic,
            description=dto.description,
            contact_method=dto.contact_method,
            contact=dto.contact,
        )
