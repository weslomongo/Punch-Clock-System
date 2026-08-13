import sqlite3

from database.connection import Database
from utils.security import hash_pin
from utils.time import to_database_timestamp, utc_now


SCHEMA_VERSION = 2


def initialize_database(database: Database) -> None:
    with database.connection() as connection:
        connection.execute("PRAGMA journal_mode = WAL")
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version > SCHEMA_VERSION:
            raise RuntimeError(f"Database schema version {version} is newer than this application supports")
        if version == 0:
            _create_version_one(connection)
            connection.execute("PRAGMA user_version = 1")
            version = 1
        if version == 1:
            _migrate_to_version_two(connection)
            connection.execute("PRAGMA user_version = 2")
            connection.commit()


def _create_version_one(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            employee_number TEXT NOT NULL UNIQUE,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            pin_hash TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS punch_events (
            id INTEGER PRIMARY KEY,
            employee_id INTEGER NOT NULL,
            event_type TEXT NOT NULL CHECK (event_type IN ('CLOCK_IN', 'CLOCK_OUT')),
            occurred_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE RESTRICT
        );

        CREATE INDEX IF NOT EXISTS idx_punch_events_employee_time
            ON punch_events(employee_id, occurred_at DESC, id DESC);
        CREATE INDEX IF NOT EXISTS idx_employees_active ON employees(active);
        """
    )


def _migrate_to_version_two(connection: sqlite3.Connection) -> None:
    connection.execute(
        """CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )"""
    )
    existing = connection.execute(
        "SELECT 1 FROM admin_users WHERE username = ? COLLATE NOCASE", ("admin",)
    ).fetchone()
    if existing is None:
        timestamp = to_database_timestamp(utc_now())
        connection.execute(
            """INSERT INTO admin_users
               (username, password_hash, active, created_at, updated_at)
               VALUES (?, ?, 1, ?, ?)""",
            ("admin", hash_pin("password"), timestamp, timestamp),
        )
