import time
import secrets
from collections import defaultdict, deque

from database.connection import Database
from utils.security import hash_pin, verify_pin


class AdminAuthenticationError(ValueError):
    pass


class AdminRateLimitError(AdminAuthenticationError):
    pass


class AdminService:
    MAX_ATTEMPTS = 5
    ATTEMPT_WINDOW_SECONDS = 60

    def __init__(self, database: Database) -> None:
        self.database = database
        self._failed_attempts: dict[str, deque[float]] = defaultdict(deque)
        self._dummy_hash = hash_pin(secrets.token_urlsafe(32))

    def authenticate(self, username: str, password: str) -> str:
        normalized_username = username.strip().casefold()
        if not normalized_username or not password:
            raise AdminAuthenticationError("Enter a username and password")
        self._enforce_rate_limit(normalized_username)
        with self.database.connection() as connection:
            row = connection.execute(
                """SELECT username, password_hash FROM admin_users
                   WHERE username = ? COLLATE NOCASE AND active = 1""",
                (normalized_username,),
            ).fetchone()
        password_hash = row["password_hash"] if row is not None else self._dummy_hash
        password_matches = verify_pin(password, password_hash)
        if row is None or not password_matches:
            self._record_failure(normalized_username)
            raise AdminAuthenticationError("Username or password is incorrect")
        self._failed_attempts.pop(normalized_username, None)
        return str(row["username"])

    def _enforce_rate_limit(self, username: str) -> None:
        attempts = self._failed_attempts[username]
        cutoff = time.monotonic() - self.ATTEMPT_WINDOW_SECONDS
        while attempts and attempts[0] < cutoff:
            attempts.popleft()
        if len(attempts) >= self.MAX_ATTEMPTS:
            raise AdminRateLimitError("Too many failed attempts. Try again in one minute.")

    def _record_failure(self, username: str) -> None:
        self._failed_attempts[username].append(time.monotonic())
