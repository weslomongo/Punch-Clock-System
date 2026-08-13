from dataclasses import dataclass
from datetime import datetime, time, timedelta

from database.connection import Database
from database.repositories.employees import EmployeeRepository
from database.repositories.punches import PunchRepository
from models.punch import Punch, PunchType
from utils.time import to_database_timestamp, utc_now


class PunchError(ValueError):
    pass


class EmployeeUnavailableError(PunchError):
    pass


class InvalidPunchTransitionError(PunchError):
    pass


@dataclass(frozen=True, slots=True)
class PunchState:
    clocked_in: bool
    latest_punch: Punch | None


class PunchService:
    def __init__(
        self, database: Database, employee_repository: EmployeeRepository | None = None,
        punch_repository: PunchRepository | None = None,
    ) -> None:
        self.database = database
        self.employees = employee_repository or EmployeeRepository()
        self.punches = punch_repository or PunchRepository()

    def get_state(self, employee_id: int) -> PunchState:
        with self.database.connection() as connection:
            employee = self.employees.get_by_id(connection, employee_id)
            if employee is None or not employee.active:
                raise EmployeeUnavailableError("Employee is not available for punching")
            latest = self.punches.latest_for_employee(connection, employee_id)
        return self._state_from_latest(latest)

    def hours_worked_today(self, employee_id: int, as_of: datetime | None = None) -> timedelta:
        current_time = as_of or utc_now()
        if current_time.tzinfo is None:
            raise ValueError("A timezone-aware datetime is required")
        local_time = current_time.astimezone()
        day_start = datetime.combine(local_time.date(), time.min, tzinfo=local_time.tzinfo)
        with self.database.connection() as connection:
            employee = self.employees.get_by_id(connection, employee_id)
            if employee is None or not employee.active:
                raise EmployeeUnavailableError("Employee is not available for punching")
            events = self.punches.through_time(
                connection, employee_id, to_database_timestamp(current_time)
            )

        total = timedelta()
        clocked_in_at: datetime | None = None
        for event in events:
            if event.event_type is PunchType.CLOCK_IN:
                clocked_in_at = event.occurred_at
            elif clocked_in_at is not None:
                total += self._overlap_with_today(clocked_in_at, event.occurred_at, day_start, current_time)
                clocked_in_at = None
        if clocked_in_at is not None:
            total += self._overlap_with_today(clocked_in_at, current_time, day_start, current_time)
        return total

    def clock_in(self, employee_id: int, occurred_at: datetime | None = None) -> Punch:
        return self._record(employee_id, PunchType.CLOCK_IN, occurred_at)

    def clock_out(self, employee_id: int, occurred_at: datetime | None = None) -> Punch:
        return self._record(employee_id, PunchType.CLOCK_OUT, occurred_at)

    def _record(self, employee_id: int, event_type: PunchType, occurred_at: datetime | None) -> Punch:
        event_time = occurred_at or utc_now()
        event_timestamp = to_database_timestamp(event_time)
        created_timestamp = to_database_timestamp(utc_now())
        with self.database.transaction(immediate=True) as connection:
            employee = self.employees.get_by_id(connection, employee_id)
            if employee is None or not employee.active:
                raise EmployeeUnavailableError("Employee is not available for punching")
            latest = self.punches.latest_for_employee(connection, employee_id)
            state = self._state_from_latest(latest)
            if event_type is PunchType.CLOCK_IN and state.clocked_in:
                raise InvalidPunchTransitionError("Employee is already clocked in")
            if event_type is PunchType.CLOCK_OUT and not state.clocked_in:
                raise InvalidPunchTransitionError("Employee is already clocked out")
            punch_id = self.punches.insert(
                connection, employee_id, event_type, event_timestamp, created_timestamp
            )
            punch = self.punches.latest_for_employee(connection, employee_id)
        if punch is None or punch.id != punch_id:
            raise RuntimeError("Punch could not be read after recording")
        return punch

    @staticmethod
    def _state_from_latest(latest: Punch | None) -> PunchState:
        return PunchState(clocked_in=latest is not None and latest.event_type is PunchType.CLOCK_IN, latest_punch=latest)

    @staticmethod
    def _overlap_with_today(
        started_at: datetime, ended_at: datetime, local_day_start: datetime, current_time: datetime
    ) -> timedelta:
        start = max(started_at.astimezone(), local_day_start)
        end = min(ended_at.astimezone(), current_time.astimezone())
        return max(end - start, timedelta())
