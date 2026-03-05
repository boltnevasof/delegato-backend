from dataclasses import dataclass


@dataclass(frozen=True)
class CreateSupportRequestDTO:
    topic: str
    description: str
    contact_method: str
    contact: str
