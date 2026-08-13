import tempfile
import unittest
from datetime import UTC, datetime, time, timedelta
from pathlib import Path

from database.connection import Database
from database.repositories.punches import PunchRepository
from database.schema import initialize_database
from models.punch import PunchType
from services.admin_service import AdminAuthenticationError, AdminRateLimitError, AdminService
from services.employee_service import AuthenticationError, EmployeeService
from services.punch_service import (
    EmployeeUnavailableError,
    InvalidPunchTransitionError,
    PunchService,
)


class PunchServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temporary_directory.name) / "test.db")
        initialize_database(self.database)
        self.employee_service = EmployeeService(self.database)
        self.punch_service = PunchService(self.database)
        self.admin_service = AdminService(self.database)
        self.employee = self.employee_service.create_employee("1001", "Weston", "Employee", "2468")

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_employee_with_no_punch_can_clock_in(self) -> None:
        punch = self.punch_service.clock_in(self.employee.id)
        self.assertEqual(punch.event_type, PunchType.CLOCK_IN)
        self.assertTrue(self.punch_service.get_state(self.employee.id).clocked_in)

    def test_employee_already_clocked_in_cannot_clock_in_again(self) -> None:
        self.punch_service.clock_in(self.employee.id)
        with self.assertRaises(InvalidPunchTransitionError):
            self.punch_service.clock_in(self.employee.id)

    def test_employee_clocked_in_can_clock_out(self) -> None:
        self.punch_service.clock_in(self.employee.id)
        punch = self.punch_service.clock_out(self.employee.id)
        self.assertEqual(punch.event_type, PunchType.CLOCK_OUT)

    def test_employee_already_clocked_out_cannot_clock_out(self) -> None:
        with self.assertRaises(InvalidPunchTransitionError):
            self.punch_service.clock_out(self.employee.id)

    def test_inactive_employee_cannot_punch(self) -> None:
        with self.database.transaction() as connection:
            connection.execute("UPDATE employees SET active = 0 WHERE id = ?", (self.employee.id,))
        with self.assertRaises(EmployeeUnavailableError):
            self.punch_service.clock_in(self.employee.id)

    def test_invalid_pin_fails(self) -> None:
        with self.assertRaises(AuthenticationError):
            self.employee_service.authenticate("9999")

    def test_valid_pin_succeeds(self) -> None:
        authenticated = self.employee_service.authenticate("2468")
        self.assertEqual(authenticated.id, self.employee.id)

    def test_punch_timestamp_is_recorded(self) -> None:
        occurred_at = datetime(2026, 8, 11, 13, 3, 12, tzinfo=UTC)
        punch = self.punch_service.clock_in(self.employee.id, occurred_at)
        self.assertEqual(punch.occurred_at, occurred_at)

    def test_latest_punch_determines_state(self) -> None:
        self.punch_service.clock_in(self.employee.id)
        self.assertTrue(self.punch_service.get_state(self.employee.id).clocked_in)
        self.punch_service.clock_out(self.employee.id)
        state = self.punch_service.get_state(self.employee.id)
        self.assertFalse(state.clocked_in)
        self.assertEqual(state.latest_punch.event_type, PunchType.CLOCK_OUT)

    def test_events_are_append_only(self) -> None:
        self.punch_service.clock_in(self.employee.id)
        self.punch_service.clock_out(self.employee.id)
        with self.database.connection() as connection:
            count = connection.execute("SELECT COUNT(*) FROM punch_events").fetchone()[0]
        self.assertEqual(count, 2)

    def test_foreign_keys_are_enabled_for_every_connection(self) -> None:
        with self.database.connection() as connection:
            enabled = connection.execute("PRAGMA foreign_keys").fetchone()[0]
        self.assertEqual(enabled, 1)

    def test_latest_repository_orders_equal_timestamps_by_id(self) -> None:
        timestamp = datetime(2026, 8, 11, 13, 3, 12, tzinfo=UTC)
        self.punch_service.clock_in(self.employee.id, timestamp)
        self.punch_service.clock_out(self.employee.id, timestamp)
        with self.database.connection() as connection:
            latest = PunchRepository().latest_for_employee(connection, self.employee.id)
        self.assertEqual(latest.event_type, PunchType.CLOCK_OUT)

    def test_hours_worked_today_includes_completed_and_active_shifts(self) -> None:
        as_of = datetime(2026, 8, 11, 20, 0, tzinfo=UTC)
        local_as_of = as_of.astimezone()
        day_start = datetime.combine(local_as_of.date(), time.min, tzinfo=local_as_of.tzinfo)
        self.punch_service.clock_in(self.employee.id, day_start - timedelta(hours=2))
        self.punch_service.clock_out(self.employee.id, day_start + timedelta(hours=1))
        self.punch_service.clock_in(self.employee.id, as_of - timedelta(hours=2))

        worked = self.punch_service.hours_worked_today(self.employee.id, as_of)

        self.assertEqual(worked, timedelta(hours=3))

    def test_hours_worked_today_is_zero_without_punches(self) -> None:
        self.assertEqual(self.punch_service.hours_worked_today(self.employee.id), timedelta())

    def test_default_admin_credentials_succeed(self) -> None:
        self.assertEqual(self.admin_service.authenticate("admin", "password"), "admin")

    def test_invalid_admin_credentials_fail(self) -> None:
        with self.assertRaises(AdminAuthenticationError):
            self.admin_service.authenticate("admin", "incorrect")

    def test_admin_password_is_not_stored_in_plaintext(self) -> None:
        with self.database.connection() as connection:
            stored = connection.execute(
                "SELECT password_hash FROM admin_users WHERE username = ?", ("admin",)
            ).fetchone()[0]
        self.assertNotEqual(stored, "password")
        self.assertTrue(stored.startswith("scrypt$"))

    def test_admin_login_is_rate_limited(self) -> None:
        for _ in range(self.admin_service.MAX_ATTEMPTS):
            with self.assertRaises(AdminAuthenticationError):
                self.admin_service.authenticate("admin", "incorrect")
        with self.assertRaises(AdminRateLimitError):
            self.admin_service.authenticate("admin", "password")


if __name__ == "__main__":
    unittest.main()
