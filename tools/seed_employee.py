import argparse
import getpass
import sqlite3
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import Database
from database.schema import initialize_database
from services.employee_service import EmployeeService


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a development employee")
    parser.add_argument("--employee-number", default="1001")
    parser.add_argument("--first-name", default="Weston")
    parser.add_argument("--last-name", default="Employee")
    parser.add_argument("--pin", help="PIN (omit to enter without terminal echo)")
    parser.add_argument("--database", type=Path, default=PROJECT_ROOT / "data" / "business.db")
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    pin = arguments.pin or getpass.getpass("Employee PIN: ")
    database = Database(arguments.database)
    initialize_database(database)
    try:
        employee = EmployeeService(database).create_employee(
            arguments.employee_number, arguments.first_name, arguments.last_name, pin
        )
    except sqlite3.IntegrityError:
        print(f"Employee number {arguments.employee_number} already exists.", file=sys.stderr)
        return 1
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f"Created employee {employee.employee_number}: {employee.display_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
