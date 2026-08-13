from database.connection import Database
from database.repositories.employees import EmployeeRepository
from models.employee import Employee
from utils.security import hash_pin, verify_pin
from utils.time import to_database_timestamp, utc_now
from utils.validation import normalize_pin


class AuthenticationError(ValueError):
    pass


class EmployeeService:
    def __init__(self, database: Database, repository: EmployeeRepository | None = None) -> None:
        self.database = database
        self.repository = repository or EmployeeRepository()

    def authenticate(self, pin: str) -> Employee:
        try:
            normalized = normalize_pin(pin)
        except ValueError as error:
            raise AuthenticationError("Enter a valid employee PIN") from error

        with self.database.connection() as connection:
            employees = self.repository.list_active(connection)
        for employee in employees:
            if verify_pin(normalized, employee.pin_hash):
                return employee
        raise AuthenticationError("Employee PIN not recognized")

    def create_employee(self, employee_number: str, first_name: str, last_name: str, pin: str) -> Employee:
        normalized = normalize_pin(pin)
        number = employee_number.strip()
        first = first_name.strip()
        last = last_name.strip()
        if not number or not first or not last:
            raise ValueError("Employee number and name are required")
        timestamp = to_database_timestamp(utc_now())
        with self.database.transaction() as connection:
            employee_id = self.repository.insert(connection, number, first, last, hash_pin(normalized), timestamp)
            employee = self.repository.get_by_id(connection, employee_id)
        if employee is None:
            raise RuntimeError("Employee could not be read after creation")
        return employee
