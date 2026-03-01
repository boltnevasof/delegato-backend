import uuid

from app.exceptions.base import NotFound
from app.models.custom_request import CustomTariffRequest
from app.models.tariff import TariffPlan
from app.repositories.custom_request import CustomTariffRequestRepository
from app.repositories.tariff import TariffRepository


class TariffService:
    def __init__(
        self,
        tariff_repository: TariffRepository,
        custom_request_repository: CustomTariffRequestRepository,
    ) -> None:
        self._tariff_repo = tariff_repository
        self._custom_request_repo = custom_request_repository

    async def list_tariffs(self) -> list[TariffPlan]:
        return await self._tariff_repo.list_active()

    async def get_tariff(self, tariff_id: uuid.UUID) -> TariffPlan:
        tariff = await self._tariff_repo.get_by_id(tariff_id)
        if tariff is None:
            raise NotFound(detail="Tariff not found")
        return tariff

    async def create_custom_request(
        self,
        user_id: uuid.UUID,
        contact_info: str,
        requirements: str,
    ) -> CustomTariffRequest:
        return await self._custom_request_repo.create(
            user_id=user_id,
            contact_info=contact_info,
            requirements=requirements,
        )
