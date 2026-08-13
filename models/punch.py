from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class PunchType(StrEnum):
    CLOCK_IN = "CLOCK_IN"
    CLOCK_OUT = "CLOCK_OUT"


@dataclass(frozen=True, slots=True)
class Punch:
    id: int
    employee_id: int
    event_type: PunchType
    occurred_at: datetime
    created_at: datetime
