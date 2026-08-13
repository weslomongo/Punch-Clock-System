from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)


def to_database_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("A timezone-aware datetime is required")
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def from_database_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Database timestamp does not contain a timezone")
    return parsed.astimezone(UTC)


def to_local(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("A timezone-aware datetime is required")
    return value.astimezone()


def format_time(value: datetime) -> str:
    return to_local(value).strftime("%-I:%M %p")
