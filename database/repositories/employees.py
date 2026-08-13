import sqlite3

from models.employee import Employee
from utils.time import from_database_timestamp


class EmployeeRepository:
    def get_by_id(self, connection: sqlite3.Connection, employee_id: int) -> Employee | None:
        row = connection.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()
        return self._from_row(row) if row else None

    def get_by_number(self, connection: sqlite3.Connection, employee_number: str) -> Employee | None:
        row = connection.execute("SELECT * FROM employees WHERE employee_number = ?", (employee_number,)).fetchone()
        return self._from_row(row) if row else None

    def list_active(self, connection: sqlite3.Connection) -> list[Employee]:
        rows = connection.execute("SELECT * FROM employees WHERE active = 1 ORDER BY id").fetchall()
        return [self._from_row(row) for row in rows]

    def insert(
        self, connection: sqlite3.Connection, employee_number: str, first_name: str,
        last_name: str, pin_hash: str, timestamp: str,
    ) -> int:
        cursor = connection.execute(
            """INSERT INTO employees
               (employee_number, first_name, last_name, pin_hash, active, created_at, updated_at)
               VALUES (?, ?, ?, ?, 1, ?, ?)""",
            (employee_number, first_name, last_name, pin_hash, timestamp, timestamp),
        )
        return int(cursor.lastrowid)

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Employee:
        return Employee(
            id=row["id"], employee_number=row["employee_number"], first_name=row["first_name"],
            last_name=row["last_name"], pin_hash=row["pin_hash"], active=bool(row["active"]),
            created_at=from_database_timestamp(row["created_at"]),
            updated_at=from_database_timestamp(row["updated_at"]),
        )
