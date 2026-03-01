from abc import ABC, abstractmethod


class EmailService(ABC):
    @abstractmethod
    async def send_otp(self, email: str, code: str) -> None:
        ...

    @abstractmethod
    async def send_transactional(
        self, email: str, template_id: str, variables: dict,
    ) -> None:
        ...
