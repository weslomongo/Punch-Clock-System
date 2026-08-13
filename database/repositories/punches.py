import sqlite3

from models.punch import Punch, PunchType
from utils.time import from_database_timestamp


class PunchRepository:
    def latest_for_employee(self, connection: sqlite3.Connection, employee_id: int) -> Punch | None:
        row = connection.execute(
            """SELECT * FROM punch_events WHERE employee_id = ?
               ORDER BY occurred_at DESC, id DESC LIMIT 1""",
            (employee_id,),
        ).fetchone()
        return self._from_row(row) if row else None

    def insert(
        self, connection: sqlite3.Connection, employee_id: int,
        event_type: PunchType, occurred_at: str, created_at: str,
    ) -> int:
        cursor = connection.execute(
            """INSERT INTO punch_events (employee_id, event_type, occurred_at, created_at)
               VALUES (?, ?, ?, ?)""",
            (employee_id, event_type.value, occurred_at, created_at),
        )
        return int(cursor.lastrowid)

    def through_time(
        self, connection: sqlite3.Connection, employee_id: int, through_timestamp: str
    ) -> list[Punch]:
        rows = connection.execute(
            """SELECT * FROM punch_events
               WHERE employee_id = ? AND occurred_at <= ?
               ORDER BY occurred_at, id""",
            (employee_id, through_timestamp),
        ).fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Punch:
        return Punch(
            id=row["id"], employee_id=row["employee_id"], event_type=PunchType(row["event_type"]),
            occurred_at=from_database_timestamp(row["occurred_at"]),
            created_at=from_database_timestamp(row["created_at"]),
        )
