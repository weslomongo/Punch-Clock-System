from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Employee:
    id: int
    employee_number: str
    first_name: str
    last_name: str
    pin_hash: str
    active: bool
    created_at: datetime
    updated_at: datetime

    @property
    def display_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
